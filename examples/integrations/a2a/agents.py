"""
OBO + A2A Composition — Docker Demo
======================================
Real Ed25519 signing. Stdlib + cryptography + flask + requests.

Two runtime modes:

  python agents.py --demo      TravelAgent: issues credentials, sends A2A tasks,
                               seals evidence envelopes, POSTs to SAPP. (default)

  python agents.py --server    FlightSearchAgent: HTTP server accepting A2A tasks,
                               verifying OBO credentials, returning results.

Environment variables:

  TravelAgent (--demo):
    TRAVEL_AGENT_OPERATOR_ID      DNS name of issuing operator
    TRAVEL_AGENT_PRINCIPAL_ID     KYC-verified agent/user identifier
    TRAVEL_AGENT_PRIVATE_KEY_B64  base64(PEM PKCS8 Ed25519 private key)
    FLIGHT_SEARCH_URL             http://flight-search:8081
    SAPP_URL                      http://sapp:8080

  FlightSearchAgent (--server):
    FLIGHT_SEARCH_PORT            (default 8081)
    TRAVEL_AGENT_PUBKEY           base64url of raw Ed25519 pubkey (32 bytes)
                                  In production: resolved from DNS
                                  _obo-key.<operator_id>  IN TXT  "v=obo1 ed25519=<value>"
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

    def run_demo(self):
        banner = "═" * 62
        print(f"\n{banner}")
        print("  OBO + A2A DEMO — Cross-org task with real evidence chain")
        print(f"{banner}\n")

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
        print("  DEMO COMPLETE — check SAPP at GET /v1/envelopes")
        print(f"{banner}\n")

    def _run_scenario(self, label, intent, payload, tamper):
        # ── Step 1: Issue OBO credential ──────────────────────────────────────
        print(f"\n  [1/4] Issuing OBO Credential")
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
        print(f"\n  [2/4] Sending A2A Task → FlightSearchAgent")
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

        print(f"\n  [3/4] FlightSearchAgent response")
        print(f"        status: {completed.status}")
        if completed.status == "completed":
            flights = (completed.result or {}).get("flights", [])
            print(f"        flights found: {len(flights)}")
            for f in flights[:2]:
                print(f"          {f['flight_number']}  {f['origin']}→{f['destination']}  ${f['fare_usd']}")
        else:
            err = (completed.result or {}).get("error", "unknown")
            print(f"        ✗ rejected: {err}")

        # ── Step 4: Seal evidence envelope → SAPP ────────────────────────────
        print(f"\n  [4/4] Sealing OBO Evidence Envelope → SAPP")
        outcome = "allow" if completed.status == "completed" else "deny"
        result_summary = json.dumps(completed.result or {}, sort_keys=True)
        envelope = OBOEvidenceEnvelope.seal(
            private_key=self.private_key,
            credential=cred,
            outcome=outcome,
            task_id=completed.task_id,
            task_result_summary=result_summary,
        )
        print(f"        evidence_digest: {envelope.evidence_digest[:20]}…")
        print(f"        envelope_sig:    Ed25519 ✓  ({envelope.envelope_sig[:20]}…)")
        print(f"        POST {self.sapp_url}/v1/envelopes")

        try:
            receipt = self._post_json(
                f"{self.sapp_url}/v1/envelopes", envelope.to_dict()
            )
            print(f"\n        ── SAPP Receipt ──────────────────────────────────")
            print(f"        receipt_id:    {receipt.get('receipt_id', '?')[:30]}…")
            print(f"        merkle_leaf:   {receipt.get('merkle_leaf', '?')[:20]}…")
            print(f"        anchored_at:   {receipt.get('anchored_at', '?')}")
            print(f"        status:        {receipt.get('status', '?')} ✓")
        except Exception as e:
            print(f"        ✗ SAPP submission failed: {e}")


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
