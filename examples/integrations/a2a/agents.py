"""
OBO + A2A Composition — Docker Demo
======================================
Real Ed25519 signing. Stdlib + cryptography + flask.

Two runtime modes:

  python agents.py --demo      TravelAgent: issues credentials, sends A2A tasks,
                               seals evidence envelopes, mints to SAPP. (default)

  python agents.py --server    FlightSearchAgent: HTTP server accepting A2A tasks,
                               verifying OBO credentials, returning results.

Environment variables:

  TravelAgent (--demo):
    TRAVEL_AGENT_OPERATOR_ID      DNS name of issuing operator
    TRAVEL_AGENT_PRINCIPAL_ID     KYC-verified agent/user identifier
    TRAVEL_AGENT_PRIVATE_KEY_B64  base64(PEM PKCS8 Ed25519 private key)
    FLIGHT_SEARCH_URL             http://flight-search:8081
    SAPP_URL                      http://sapp:8080
    SAPP_ORG_ID                   (optional) SAPP tenant org_id
    SAPP_PROFILE_ID               evidence profile: default|regulated|regulated_eu_finance
                                  (default: regulated)

  FlightSearchAgent (--server):
    FLIGHT_SEARCH_PORT            (default 8081)
    TRAVEL_AGENT_PUBKEY           base64url of raw Ed25519 pubkey (32 bytes)
                                  In production: resolved from DNS
                                  _obo-key.<operator_id>  IN TXT  "v=obo1 ed25519=<value>"

Agent Cards (A2A discovery):
  FlightSearchAgent serves GET /.well-known/agent.json advertising its skills
  and declaring OBO as the required authentication scheme. TravelAgent fetches
  this card on startup — discovers the OBO requirement, confirms the endpoint,
  then proceeds. This is the correct A2A discovery pattern: the card is the
  contract, not out-of-band configuration.

  The OBO entry in authentication.schemes is the key signal:
    "authentication": { "schemes": ["obo"], "obo": { ... } }
  Any A2A sender reading this card knows it must attach an OBO credential.

SAPP integration:
  Evidence is minted via POST /v1/evidence/mint (ADR-153 domain-neutral API).
  Leaves follow the canonical tag:value format, lexicographically sorted by SAPP.
  After mint, GET /evidence/{evidence_id}/proof fetches the signed Merkle proof
  (JWS compact, ADR-181 E7 signing authority).
"""

import argparse
import base64
import dataclasses
import datetime
import hashlib
import json
import os
import sys
import time
import uuid
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
)

# ─── Key helpers ──────────────────────────────────────────────────────────────

def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def load_private_key_from_env() -> Ed25519PrivateKey:
    """Load Ed25519 private key from TRAVEL_AGENT_PRIVATE_KEY_B64 env var."""
    b64 = os.environ.get("TRAVEL_AGENT_PRIVATE_KEY_B64", "")
    if not b64:
        raise RuntimeError("TRAVEL_AGENT_PRIVATE_KEY_B64 not set — run keygen.py first")
    pem = base64.b64decode(b64)
    return load_pem_private_key(pem, password=None)


def load_public_key_from_env() -> Ed25519PublicKey:
    """Load Ed25519 public key from TRAVEL_AGENT_PUBKEY env var (base64url raw 32 bytes)."""
    b64 = os.environ.get("TRAVEL_AGENT_PUBKEY", "")
    if not b64:
        raise RuntimeError("TRAVEL_AGENT_PUBKEY not set — copy from keygen.py output")
    raw = _b64url_decode(b64)
    return Ed25519PublicKey.from_public_bytes(raw)


# ─── OBO Data Structures ──────────────────────────────────────────────────────

@dataclasses.dataclass
class OBOCredential:
    """
    OBO Credential (§3.1). Real Ed25519 signature over canonical fields.
    """
    credential_id: str
    operator_id: str
    principal_id: str
    intent_hash: str          # SHA-256 of canonical intent phrase
    issued_at: str
    expires_at: str
    governance_framework_ref: str
    credential_sig: str       # base64url Ed25519 signature

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def _canonical(self) -> bytes:
        """Canonical payload for signing/verification — all fields except credential_sig."""
        payload = {k: v for k, v in self.to_dict().items() if k != "credential_sig"}
        return json.dumps(payload, sort_keys=True).encode()

    @classmethod
    def issue(
        cls,
        private_key: Ed25519PrivateKey,
        operator_id: str,
        principal_id: str,
        intent_phrase: str,
        governance_framework_ref: str = "https://example.com/obo/v1/policy",
        ttl_seconds: int = 300,
    ) -> "OBOCredential":
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(seconds=ttl_seconds)
        intent_hash = hashlib.sha256(intent_phrase.encode()).hexdigest()

        cred = cls(
            credential_id=f"urn:obo:cred:{uuid.uuid4()}",
            operator_id=operator_id,
            principal_id=principal_id,
            intent_hash=intent_hash,
            issued_at=now.isoformat(),
            expires_at=expires.isoformat(),
            governance_framework_ref=governance_framework_ref,
            credential_sig="",
        )
        sig_bytes = private_key.sign(cred._canonical())
        cred.credential_sig = _b64url_encode(sig_bytes)
        return cred

    def verify(self, public_key: Ed25519PublicKey) -> None:
        """Raises InvalidSignature if the credential signature is invalid."""
        sig_bytes = _b64url_decode(self.credential_sig)
        public_key.verify(sig_bytes, self._canonical())


@dataclasses.dataclass
class OBOEvidenceEnvelope:
    """
    OBO Evidence Envelope (§3.2). Sealed post-task. Ed25519 over evidence_digest.
    The A2A task.id is the correlation anchor — links evidence back to the task
    and forward to SAPP / Merkle / regulator API.
    """
    envelope_id: str
    credential_id: str
    operator_id: str
    principal_id: str
    intent_hash: str
    outcome: str                  # "allow" | "deny" | "escalate"
    task_correlation_ref: str     # A2A task.id
    executed_at: str
    evidence_digest: str          # SHA-256 of binding payload
    envelope_sig: str             # base64url Ed25519 over evidence_digest

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def seal(
        cls,
        private_key: Ed25519PrivateKey,
        credential: OBOCredential,
        outcome: str,
        task_id: str,
        task_result_summary: str,
    ) -> "OBOEvidenceEnvelope":
        executed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        digest_payload = (
            f"{credential.credential_id}:{outcome}:{task_id}:{task_result_summary}"
        )
        evidence_digest = hashlib.sha256(digest_payload.encode()).hexdigest()

        env = cls(
            envelope_id=f"urn:obo:env:{uuid.uuid4()}",
            credential_id=credential.credential_id,
            operator_id=credential.operator_id,
            principal_id=credential.principal_id,
            intent_hash=credential.intent_hash,
            outcome=outcome,
            task_correlation_ref=task_id,
            executed_at=executed_at,
            evidence_digest=evidence_digest,
            envelope_sig="",
        )
        sig_bytes = private_key.sign(evidence_digest.encode())
        env.envelope_sig = _b64url_encode(sig_bytes)
        return env

    def verify(self, public_key: Ed25519PublicKey) -> None:
        sig_bytes = _b64url_decode(self.envelope_sig)
        public_key.verify(sig_bytes, self.evidence_digest.encode())


# ─── A2A Agent Card ───────────────────────────────────────────────────────────

# FlightSearchAgent's Agent Card — served at GET /.well-known/agent.json
# This is the discovery artefact. The authentication.schemes entry is the
# machine-readable signal that OBO credentials are required.
FLIGHT_SEARCH_AGENT_CARD = {
    "schema_version": "1.0",
    "name": "FlightSearchAgent",
    "description": (
        "Searches flights and hotels across carriers. "
        "Cross-org requests require an OBO credential in extensions.obo."
    ),
    "version": "1.0.0",
    "url": "",          # populated at runtime from FLIGHT_SEARCH_URL
    "provider": {
        "name": "flight-search.example.com",
        "url":  "https://flight-search.example.com",
    },
    "capabilities": {
        "streaming":           False,
        "push_notifications":  False,
    },
    "authentication": {
        # OBO is the declared authentication scheme for cross-org requests.
        # A sender reading this card knows it must attach extensions.obo.
        # Within a shared trust domain, bearer tokens would also be listed here.
        "schemes": ["obo"],
        "obo": {
            "spec_version":     "draft-obo-agentic-evidence-envelope-00",
            "required_fields":  [
                "credential_id", "operator_id", "principal_id",
                "intent_hash", "credential_sig", "expires_at",
            ],
            "key_resolution":   "dns-txt",
            "dns_record_format": "_obo-key.{operator_id}  IN TXT  \"v=obo1 ed25519=<pubkey>\"",
            "did_alternative":  "did:web:{operator_id}",
        },
    },
    "skills": [
        {
            "id":          "flight-search",
            "name":        "Flight Search",
            "description": "Search available flights between two airports on a given date.",
            "tags":        ["travel", "flights"],
            "examples":    ["search flights from LHR to JFK on 2025-06-15"],
            "input_schema": {
                "type": "object",
                "required": ["origin", "destination", "date"],
                "properties": {
                    "origin":      {"type": "string", "description": "IATA airport code"},
                    "destination": {"type": "string", "description": "IATA airport code"},
                    "date":        {"type": "string", "format": "date"},
                },
            },
        },
        {
            "id":          "hotel-search",
            "name":        "Hotel Search",
            "description": "Search available hotels in a city for a date range.",
            "tags":        ["travel", "hotels"],
            "examples":    ["search hotels in New York 2025-06-15 to 2025-06-18"],
            "input_schema": {
                "type": "object",
                "required": ["city", "check_in", "check_out"],
                "properties": {
                    "city":      {"type": "string"},
                    "check_in":  {"type": "string", "format": "date"},
                    "check_out": {"type": "string", "format": "date"},
                },
            },
        },
    ],
}


# ─── A2A Task ─────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class A2ATask:
    task_id: str
    kind: str = "task"
    status: str = "submitted"
    intent: str = ""
    payload: dict = dataclasses.field(default_factory=dict)
    result: Optional[dict] = None
    extensions: dict = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "id": self.task_id,
            "status": self.status,
            "intent": self.intent,
            "payload": self.payload,
            "result": self.result,
            "extensions": self.extensions,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "A2ATask":
        return cls(
            task_id=d["id"],
            kind=d.get("kind", "task"),
            status=d.get("status", "submitted"),
            intent=d.get("intent", ""),
            payload=d.get("payload", {}),
            result=d.get("result"),
            extensions=d.get("extensions", {}),
        )


# ─── TravelAgent (client) ─────────────────────────────────────────────────────

class TravelAgent:
    """
    Issuing operator. Signs OBO credentials and A2A tasks. Seals evidence envelopes.
    Submits envelopes to SAPP.
    """

    def __init__(self):
        self.private_key = load_private_key_from_env()
        self.public_key = self.private_key.public_key()
        self.operator_id = os.environ.get(
            "TRAVEL_AGENT_OPERATOR_ID", "travel-agent.example.com"
        )
        self.principal_id = os.environ.get(
            "TRAVEL_AGENT_PRINCIPAL_ID",
            "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
        )
        self.flight_search_url = os.environ.get(
            "FLIGHT_SEARCH_URL", "http://localhost:8081"
        )
        self.sapp_url = os.environ.get("SAPP_URL", "http://localhost:8080")
        self._pending: dict[str, OBOCredential] = {}

    def discover_agent_card(self) -> dict:
        """
        Fetch FlightSearchAgent's Agent Card from /.well-known/agent.json.
        This is the A2A discovery step — confirms the endpoint, skills, and
        that OBO is declared as the required authentication scheme.
        """
        try:
            card = self._get_json(f"{self.flight_search_url}/.well-known/agent.json")
            return card
        except Exception as e:
            return {"_error": str(e)}

    def _post_json(self, url: str, body: dict) -> dict:
        import urllib.request
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def _get_json(self, url: str) -> dict:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def _mint_evidence(self, envelope: "OBOEvidenceEnvelope", cred: "OBOCredential") -> dict:
        """
        POST /v1/evidence/mint — SAPP domain-neutral canonical API (ADR-153).

        Leaves follow tag:value format. SAPP lexicographically sorts them before
        Merkle construction — order here is for readability only.

        Required leaves for 'regulated' profile:
          producer_id, event_time, schema_ref

        OBO-specific leaves carry the full evidence provenance so the Merkle tree
        binds credential identity, intent, outcome and task correlation in one shot.
        """
        org_id     = os.environ.get("SAPP_ORG_ID", "")
        profile_id = os.environ.get("SAPP_PROFILE_ID", "regulated")

        body: dict = {
            "evidence_id": envelope.envelope_id,   # idempotency key — safe to replay
            "profile_id":  profile_id,
            "leaves": [
                # ── regulated profile required leaves ──────────────────────────
                f"producer_id:{cred.operator_id}",
                f"event_time:{envelope.executed_at}",
                f"schema_ref:draft-obo-agentic-evidence-envelope-00",
                # ── OBO credential provenance ──────────────────────────────────
                f"obo_credential_id:{cred.credential_id}",
                f"obo_operator_id:{cred.operator_id}",
                f"obo_principal_id:{cred.principal_id}",
                f"obo_intent_hash:{cred.intent_hash}",
                f"obo_governance_ref:{cred.governance_framework_ref}",
                # ── Evidence envelope binding ──────────────────────────────────
                f"obo_envelope_id:{envelope.envelope_id}",
                f"obo_outcome:{envelope.outcome}",
                f"obo_task_ref:{envelope.task_correlation_ref}",
                f"obo_evidence_digest:{envelope.evidence_digest}",
                f"obo_envelope_sig:{envelope.envelope_sig}",
            ],
        }
        if org_id:
            body["org_id"] = org_id

        return self._post_json(f"{self.sapp_url}/v1/evidence/mint", body)

    def _fetch_proof(self, evidence_id: str) -> dict:
        """
        GET /evidence/{evidence_id}/proof — signed Merkle proof (ADR-181 E7).
        Returns JWS compact signature over the 3-level proof chain.
        Falls back gracefully if SAPP version does not yet expose this route.
        """
        try:
            return self._get_json(f"{self.sapp_url}/evidence/{evidence_id}/proof")
        except Exception:
            # Older SAPP or stub — try tenant route
            try:
                return self._get_json(
                    f"{self.sapp_url}/tenant/evidence/{evidence_id}/proof"
                )
            except Exception as e:
                return {"_note": f"proof not available: {e}"}

    def run_demo(self):
        banner = "═" * 62
        print(f"\n{banner}")
        print("  OBO + A2A DEMO — Cross-org task with real evidence chain")
        print(f"{banner}\n")

        # ── Agent Card discovery ──────────────────────────────────────────────
        print(f"  [discovery] GET {self.flight_search_url}/.well-known/agent.json")
        card = self.discover_agent_card()
        if "_error" in card:
            print(f"  ⚠  Agent Card unavailable: {card['_error']}")
        else:
            auth_schemes = card.get("authentication", {}).get("schemes", [])
            skills       = [s["id"] for s in card.get("skills", [])]
            obo_required = "obo" in auth_schemes
            print(f"  agent:       {card.get('name', '?')}  v{card.get('version', '?')}")
            print(f"  skills:      {', '.join(skills)}")
            print(f"  auth.obo:    {'✓ required' if obo_required else '✗ not declared'}")
            if not obo_required:
                print(f"  ⚠  WARNING — agent card does not declare OBO; proceeding anyway")
            print()

        scenarios = [
            {
                "label": "Flight search: LHR → JFK",
                "intent": "search flights from LHR to JFK on 2025-06-15",
                "payload": {"origin": "LHR", "destination": "JFK", "date": "2025-06-15"},
                "tamper": False,
            },
            {
                "label": "Hotel search: New York",
                "intent": "search hotels in New York 2025-06-15 to 2025-06-18",
                "payload": {"city": "New York", "check_in": "2025-06-15", "check_out": "2025-06-18"},
                "tamper": False,
            },
            {
                "label": "Tampered intent (should be rejected)",
                "intent": "search flights from LHR to JFK on 2025-06-15",
                "payload": {"origin": "LHR", "destination": "JFK", "date": "2025-06-15"},
                "tamper": True,
            },
        ]

        for i, s in enumerate(scenarios, 1):
            print(f"{'─' * 62}")
            print(f"  SCENARIO {i}: {s['label']}")
            print(f"{'─' * 62}")
            self._run_scenario(**s)
            print()

        print(f"{banner}")
        print("  DEMO COMPLETE")
        print(f"  Inspect:  curl {self.sapp_url}/evidence/{{trace_id}}/proof | jq")
        print(f"{banner}\n")

    def _run_scenario(self, label, intent, payload, tamper):
        # ── Step 1: Issue OBO credential ──────────────────────────────────────
        print(f"\n  [1/5] Issuing OBO Credential")
        cred = OBOCredential.issue(
            private_key=self.private_key,
            operator_id=self.operator_id,
            principal_id=self.principal_id,
            intent_phrase=intent,
        )
        print(f"        operator_id:    {cred.operator_id}")
        print(f"        principal_id:   {cred.principal_id[:52]}…")
        print(f"        intent_hash:    {cred.intent_hash[:20]}…")
        print(f"        credential_sig: Ed25519 ✓  ({cred.credential_sig[:20]}…)")

        # ── Step 2: Build and send A2A task ───────────────────────────────────
        print(f"\n  [2/5] Sending A2A Task → FlightSearchAgent")
        task = A2ATask(
            task_id=f"task-{uuid.uuid4()}",
            intent=intent,
            payload=payload,
            extensions={
                "obo": {
                    "spec_version": "draft-obo-agentic-evidence-envelope-00",
                    **cred.to_dict(),
                }
            },
        )
        self._pending[task.task_id] = cred

        if tamper:
            task.intent = "search flights from LHR to CDG on 2025-06-15"
            print(f"        ⚠ TAMPER: intent changed to '{task.intent}'")

        print(f"        POST {self.flight_search_url}/tasks")
        print(f"        task_id: {task.task_id[:16]}…")

        try:
            result = self._post_json(
                f"{self.flight_search_url}/tasks", task.to_dict()
            )
        except Exception as e:
            print(f"        ✗ request failed: {e}")
            return

        completed = A2ATask.from_dict(result)

        print(f"\n  [3/5] FlightSearchAgent response")
        print(f"        status: {completed.status}")
        if completed.status == "completed":
            flights = (completed.result or {}).get("flights", [])
            print(f"        flights found: {len(flights)}")
            for f in flights[:2]:
                print(f"          {f['flight_number']}  {f['origin']}→{f['destination']}  ${f['fare_usd']}")
        else:
            err = (completed.result or {}).get("error", "unknown")
            print(f"        ✗ rejected: {err}")

        # ── Step 4: Seal evidence envelope ───────────────────────────────────
        print(f"\n  [4/5] Sealing OBO Evidence Envelope")
        outcome = "allow" if completed.status == "completed" else "deny"
        result_summary = json.dumps(completed.result or {}, sort_keys=True)
        envelope = OBOEvidenceEnvelope.seal(
            private_key=self.private_key,
            credential=cred,
            outcome=outcome,
            task_id=completed.task_id,
            task_result_summary=result_summary,
        )
        print(f"        envelope_id:     {envelope.envelope_id[:40]}…")
        print(f"        outcome:         {envelope.outcome}")
        print(f"        evidence_digest: {envelope.evidence_digest[:20]}…")
        print(f"        envelope_sig:    Ed25519 ✓  ({envelope.envelope_sig[:20]}…)")
        print(f"        task_ref:        {envelope.task_correlation_ref[:20]}…")

        # ── Step 5: Mint to SAPP ──────────────────────────────────────────────
        print(f"\n  [5/5] Minting Evidence → SAPP  POST /v1/evidence/mint")
        try:
            mint_resp = self._mint_evidence(envelope, cred)

            merkle_root     = mint_resp.get("merkle_root", "")
            evidence_bundle = mint_resp.get("evidence_bundle", "")
            checkpoint_idx  = mint_resp.get("checkpoint_index", "?")
            tree_size       = mint_resp.get("tree_size", "?")
            created_at      = mint_resp.get("created_at", "?")

            print(f"\n        ── SAPP Mint Response ────────────────────────────")
            print(f"        evidence_bundle: {str(evidence_bundle)[:30]}…")
            print(f"        merkle_root:     {str(merkle_root)[:20]}…")
            print(f"        checkpoint_idx:  {checkpoint_idx}")
            print(f"        tree_size:       {tree_size}")
            print(f"        created_at:      {created_at}")

            # ── Fetch signed Merkle proof (ADR-181 E7) ────────────────────────
            print(f"\n        ── Fetching Signed Proof  GET /evidence/…/proof ──")
            proof = self._fetch_proof(envelope.envelope_id)

            if "_note" in proof:
                print(f"        ⚠  {proof['_note']}")
            else:
                # JWS compact signature is in proof.signature or proof.jws
                jws   = proof.get("signature") or proof.get("jws") or proof.get("proof_jws", "")
                depth = proof.get("proof_depth") or proof.get("depth", "?")
                print(f"        proof_depth:     {depth}")
                print(f"        JWS proof:       {str(jws)[:40]}…  ✓")
                print(f"\n        ── Evidence Chain ────────────────────────────────")
                print(f"        OBO credential issued  → evidence_digest bound")
                print(f"        A2A task correlated    → task_ref: {envelope.task_correlation_ref[:16]}…")
                print(f"        SAPP Merkle anchored   → root: {str(merkle_root)[:16]}…")
                print(f"        Proof signed (E7)      → JWS: {str(jws)[:16]}…")

        except Exception as e:
            print(f"        ✗ SAPP mint failed: {e}")


# ─── FlightSearchAgent (server) ───────────────────────────────────────────────

def run_flight_search_server():
    """
    FlightSearch HTTP server. Accepts A2A tasks at POST /tasks.
    Verifies OBO credential before executing.

    Key resolution:
      Production: DNS TXT  _obo-key.<operator_id>  "v=obo1 ed25519=<pubkey_b64>"
      Demo:       TRAVEL_AGENT_PUBKEY env var (base64url raw 32 bytes)
    """
    from flask import Flask, request, jsonify

    app = Flask("flight-search")
    port = int(os.environ.get("FLIGHT_SEARCH_PORT", 8081))

    # Load verifying public key
    try:
        public_key = load_public_key_from_env()
        raw = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        print(f"[FlightSearchAgent] OBO verifying key loaded: {_b64url_encode(raw)[:20]}…")
    except RuntimeError as e:
        print(f"[FlightSearchAgent] WARNING: {e}")
        public_key = None

    # Build Agent Card with runtime URL
    agent_card = dict(FLIGHT_SEARCH_AGENT_CARD)
    agent_card["url"] = os.environ.get("FLIGHT_SEARCH_URL", f"http://localhost:{port}")

    @app.route("/.well-known/agent.json")
    def agent_card_route():
        return jsonify(agent_card)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/tasks", methods=["POST"])
    def receive_task():
        task_dict = request.get_json(force=True)
        task = A2ATask.from_dict(task_dict)
        print(f"\n[FlightSearchAgent] ← task {task.task_id[:16]}… intent: {task.intent[:50]}")

        obo_raw = task.extensions.get("obo", {})

        # ── Structural check ──────────────────────────────────────────────────
        required = [
            "credential_id", "operator_id", "principal_id",
            "intent_hash", "credential_sig", "expires_at",
        ]
        missing = [f for f in required if not obo_raw.get(f)]
        if missing:
            msg = f"OBO credential missing fields: {missing}"
            print(f"[FlightSearchAgent] ✗ REJECTED — {msg}")
            task.status = "failed"
            task.result = {"error": msg}
            return jsonify(task.to_dict()), 422

        cred = OBOCredential(
            credential_id=obo_raw["credential_id"],
            operator_id=obo_raw["operator_id"],
            principal_id=obo_raw["principal_id"],
            intent_hash=obo_raw["intent_hash"],
            issued_at=obo_raw.get("issued_at", ""),
            expires_at=obo_raw["expires_at"],
            governance_framework_ref=obo_raw.get("governance_framework_ref", ""),
            credential_sig=obo_raw["credential_sig"],
        )

        # ── Expiry ────────────────────────────────────────────────────────────
        expires = datetime.datetime.fromisoformat(cred.expires_at)
        if datetime.datetime.now(datetime.timezone.utc) > expires:
            msg = "OBO credential expired"
            print(f"[FlightSearchAgent] ✗ REJECTED — {msg}")
            task.status = "failed"
            task.result = {"error": msg}
            return jsonify(task.to_dict()), 422

        # ── Intent hash consistency ───────────────────────────────────────────
        computed = hashlib.sha256(task.intent.encode()).hexdigest()
        if computed != cred.intent_hash:
            msg = "OBO intent_hash mismatch — tampered or drifted intent"
            print(f"[FlightSearchAgent] ✗ REJECTED — {msg}")
            task.status = "failed"
            task.result = {"error": msg}
            return jsonify(task.to_dict()), 422

        # ── Ed25519 signature verification ────────────────────────────────────
        if public_key is not None:
            try:
                cred.verify(public_key)
                print(f"[FlightSearchAgent] ✓ Ed25519 credential_sig verified")
            except InvalidSignature:
                msg = "OBO credential_sig invalid — Ed25519 verification failed"
                print(f"[FlightSearchAgent] ✗ REJECTED — {msg}")
                task.status = "failed"
                task.result = {"error": msg}
                return jsonify(task.to_dict()), 422
        else:
            print(f"[FlightSearchAgent] ⚠  Ed25519 verify skipped (no pubkey configured)")

        print(f"[FlightSearchAgent] ✓ OBO credential accepted (operator: {cred.operator_id})")

        # ── Execute task ──────────────────────────────────────────────────────
        task = _execute_task(task)
        return jsonify(task.to_dict())

    print(f"[FlightSearchAgent] listening on :{port}")
    app.run(host="0.0.0.0", port=port)


def _execute_task(task: A2ATask) -> A2ATask:
    """Synthetic task execution."""
    intent_lower = task.intent.lower()

    if "flight" in intent_lower or "origin" in task.payload:
        origin = task.payload.get("origin", "LHR")
        destination = task.payload.get("destination", "JFK")
        date = task.payload.get("date", "2025-06-15")
        task.status = "completed"
        task.result = {
            "flights": [
                {"flight_number": "BA117", "origin": origin, "destination": destination,
                 "departure": f"{date}T09:00:00Z", "arrival": f"{date}T11:55:00Z",
                 "fare_usd": 487.00, "class": "economy"},
                {"flight_number": "VS3", "origin": origin, "destination": destination,
                 "departure": f"{date}T11:30:00Z", "arrival": f"{date}T14:20:00Z",
                 "fare_usd": 512.00, "class": "economy"},
            ],
            "searched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    elif "hotel" in intent_lower or "city" in task.payload:
        city = task.payload.get("city", "New York")
        task.status = "completed"
        task.result = {
            "hotels": [
                {"name": "The Standard", "city": city, "rate_usd": 289.00,
                 "check_in": task.payload.get("check_in"), "check_out": task.payload.get("check_out")},
                {"name": "Arlo Midtown", "city": city, "rate_usd": 219.00,
                 "check_in": task.payload.get("check_in"), "check_out": task.payload.get("check_out")},
            ],
            "searched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    else:
        task.status = "completed"
        task.result = {"message": "task executed", "intent": task.intent}

    print(f"[FlightSearchAgent] ✓ task completed (status: {task.status})")
    return task


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", action="store_true",
        help="Run as FlightSearchAgent HTTP server"
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run TravelAgent demo (default)"
    )
    args = parser.parse_args()

    if args.server:
        run_flight_search_server()
    else:
        # Give servers time to start if running in docker-compose
        startup_wait = int(os.environ.get("STARTUP_WAIT_SECONDS", "0"))
        if startup_wait:
            print(f"[TravelAgent] waiting {startup_wait}s for services to start…")
            time.sleep(startup_wait)
        TravelAgent().run_demo()


if __name__ == "__main__":
    main()
