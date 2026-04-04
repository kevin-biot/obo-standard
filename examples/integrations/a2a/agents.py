"""
OBO + A2A Composition Example
==============================
Illustrative reference — not a production implementation.

This example shows how an OBO credential and evidence envelope compose
with the A2A task protocol. Two synthetic agents exchange tasks.

Pattern:
  - The sending agent (TravelAgent) carries an OBO credential.
  - The credential is included in the A2A task metadata extension.
  - The receiving agent (FlightSearchAgent) verifies the OBO credential
    before accepting the task.
  - On completion, an OBO Evidence Envelope is sealed with the A2A
    task.id as the correlation anchor.

Dependencies (stdlib only — intentionally zero external imports):
  import json, hashlib, base64, uuid, datetime, dataclasses

OBO fields map to A2A fields as follows:

  OBO Credential                    A2A Task Metadata
  ─────────────────────────────     ────────────────────────────────
  credential.operator_id        →   extensions.obo.operator_id
  credential.principal_id       →   extensions.obo.principal_id
  credential.intent_hash        →   extensions.obo.intent_hash
  credential.credential_id      →   extensions.obo.credential_id
  credential.issued_at          →   extensions.obo.issued_at
  credential.credential_sig     →   extensions.obo.credential_sig

  A2A Task                          OBO Evidence Envelope
  ────────────────────────────────  ─────────────────────────────────
  task.id                       →   envelope.task_correlation_ref
  task.status                   →   envelope.outcome
  task.result                   →   (informs) envelope.evidence_digest
"""

import json
import hashlib
import base64
import uuid
import datetime
import dataclasses
from typing import Optional


# ─── OBO Data Structures ──────────────────────────────────────────────────────

@dataclasses.dataclass
class OBOCredential:
    """
    Minimal OBO Credential (§3.1 of draft-obo-agentic-evidence-envelope-00).

    In production: Ed25519-signed JWT or CBOR. Here: a dict with a
    deterministic synthetic signature for illustrative purposes only.
    """
    credential_id: str
    operator_id: str          # DNS name of issuing operator
    principal_id: str         # KYC-verified identifier of the acting agent/user
    intent_hash: str          # SHA-256 of the canonical intent phrase
    issued_at: str            # ISO 8601
    expires_at: str           # ISO 8601
    governance_framework_ref: str
    credential_sig: str       # In production: Ed25519 over canonical fields

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def issue(
        cls,
        operator_id: str,
        principal_id: str,
        intent_phrase: str,
        governance_framework_ref: str = "https://example.com/obo/v1/policy",
        ttl_seconds: int = 300,
    ) -> "OBOCredential":
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(seconds=ttl_seconds)
        intent_hash = hashlib.sha256(intent_phrase.encode()).hexdigest()

        credential = cls(
            credential_id=f"urn:obo:cred:{uuid.uuid4()}",
            operator_id=operator_id,
            principal_id=principal_id,
            intent_hash=intent_hash,
            issued_at=now.isoformat(),
            expires_at=expires.isoformat(),
            governance_framework_ref=governance_framework_ref,
            credential_sig="",  # populated below
        )
        # Synthetic sig — in production: Ed25519(operator_private_key, canonical_payload)
        canonical = json.dumps(
            {k: v for k, v in credential.to_dict().items() if k != "credential_sig"},
            sort_keys=True,
        )
        credential.credential_sig = base64.urlsafe_b64encode(
            hashlib.sha256(canonical.encode()).digest()
        ).decode()
        return credential


@dataclasses.dataclass
class OBOEvidenceEnvelope:
    """
    Minimal OBO Evidence Envelope (§3.2 of draft-obo-agentic-evidence-envelope-00).

    Sealed post-task. The A2A task.id becomes task_correlation_ref,
    providing an unambiguous audit link from the evidence record back to
    the A2A task and forward to any SAPP/Merkle submission.
    """
    envelope_id: str
    credential_id: str
    operator_id: str
    principal_id: str
    intent_hash: str
    outcome: str                    # "allow" | "deny" | "escalate"
    task_correlation_ref: str       # A2A task.id
    executed_at: str                # ISO 8601
    evidence_digest: str            # SHA-256 of (credential_id + outcome + task_correlation_ref)
    envelope_sig: str               # In production: Ed25519 over evidence_digest

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def seal(
        cls,
        credential: OBOCredential,
        outcome: str,
        task_id: str,
        task_result_summary: str,
    ) -> "OBOEvidenceEnvelope":
        executed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # evidence_digest binds credential identity, outcome, and correlation anchor
        digest_payload = f"{credential.credential_id}:{outcome}:{task_id}:{task_result_summary}"
        evidence_digest = hashlib.sha256(digest_payload.encode()).hexdigest()

        envelope = cls(
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
        # Synthetic sig — in production: Ed25519(operator_private_key, evidence_digest)
        envelope.envelope_sig = base64.urlsafe_b64encode(
            hashlib.sha256(evidence_digest.encode()).digest()
        ).decode()
        return envelope


# ─── A2A Data Structures ──────────────────────────────────────────────────────
# Minimal A2A-compatible task envelope. Mirrors the A2A Task schema:
# https://github.com/a2aproject/A2A

@dataclasses.dataclass
class A2ATask:
    task_id: str
    kind: str = "task"
    status: str = "submitted"       # submitted | working | completed | failed
    intent: str = ""
    payload: dict = dataclasses.field(default_factory=dict)
    result: Optional[dict] = None
    extensions: dict = dataclasses.field(default_factory=dict)   # OBO lives here

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


# ─── Agents ───────────────────────────────────────────────────────────────────

class TravelAgent:
    """
    Sending agent. Carries an OBO credential and attaches it to every
    A2A task it emits. Seals an OBO Evidence Envelope when a task
    completes (or fails).

    This agent does NOT have a shared trust domain with FlightSearchAgent.
    OBO is the accountability layer that makes the cross-org interaction
    auditable without requiring a shared OAuth authorisation server.
    """

    OPERATOR_ID = "travel-agent.example.com"
    PRINCIPAL_ID = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"  # KYC-verified

    def __init__(self):
        self.pending_tasks: dict[str, tuple[A2ATask, OBOCredential]] = {}

    def emit_task(self, intent_phrase: str, payload: dict) -> A2ATask:
        """
        Build an A2A task with an OBO credential attached in extensions.obo.
        """
        credential = OBOCredential.issue(
            operator_id=self.OPERATOR_ID,
            principal_id=self.PRINCIPAL_ID,
            intent_phrase=intent_phrase,
        )

        task = A2ATask(
            task_id=f"task-{uuid.uuid4()}",
            intent=intent_phrase,
            payload=payload,
            extensions={
                "obo": {
                    "spec_version": "draft-obo-agentic-evidence-envelope-00",
                    "credential_id": credential.credential_id,
                    "operator_id": credential.operator_id,
                    "principal_id": credential.principal_id,
                    "intent_hash": credential.intent_hash,
                    "issued_at": credential.issued_at,
                    "expires_at": credential.expires_at,
                    "governance_framework_ref": credential.governance_framework_ref,
                    "credential_sig": credential.credential_sig,
                }
            },
        )

        self.pending_tasks[task.task_id] = (task, credential)
        print(f"[TravelAgent] → emitting task {task.task_id[:12]}…")
        print(f"             intent: {intent_phrase}")
        print(f"             credential: {credential.credential_id[:40]}…")
        return task

    def seal_evidence(self, completed_task: A2ATask) -> OBOEvidenceEnvelope:
        """
        Seal an OBO Evidence Envelope once the A2A task has a final status.
        The A2A task.id is the correlation anchor.
        """
        task, credential = self.pending_tasks[completed_task.task_id]
        outcome = "allow" if completed_task.status == "completed" else "deny"
        result_summary = json.dumps(completed_task.result or {}, sort_keys=True)

        envelope = OBOEvidenceEnvelope.seal(
            credential=credential,
            outcome=outcome,
            task_id=completed_task.task_id,
            task_result_summary=result_summary,
        )
        print(f"[TravelAgent] ✓ evidence envelope sealed")
        print(f"             envelope_id: {envelope.envelope_id[:40]}…")
        print(f"             outcome: {envelope.outcome}")
        print(f"             evidence_digest: {envelope.evidence_digest[:20]}…")
        return envelope


class FlightSearchAgent:
    """
    Receiving agent. Verifies the OBO credential in extensions.obo before
    accepting a task. Performs no OAuth exchange — the OBO credential IS the
    accountability layer.

    In production, verification would:
      1. Resolve operator_id via DNS TXT _obo-key.<operator_id>   (Appendix E)
         or via did:web DID Document                               (Appendix F)
      2. Verify credential_sig with the resolved Ed25519 public key
      3. Check intent_hash matches the task intent
      4. Check issued_at / expires_at window

    Here: we check structural presence and intent hash consistency only.
    """

    OPERATOR_ID = "flight-search.example.com"

    def receive(self, task: A2ATask) -> A2ATask:
        print(f"[FlightSearchAgent] ← received task {task.task_id[:12]}…")

        obo = task.extensions.get("obo")
        if not obo:
            print("[FlightSearchAgent] ✗ REJECTED — no OBO credential in extensions")
            task.status = "failed"
            task.result = {"error": "missing OBO credential"}
            return task

        # Structural verification
        required_fields = [
            "credential_id", "operator_id", "principal_id",
            "intent_hash", "credential_sig", "expires_at",
        ]
        missing = [f for f in required_fields if not obo.get(f)]
        if missing:
            print(f"[FlightSearchAgent] ✗ REJECTED — OBO credential missing fields: {missing}")
            task.status = "failed"
            task.result = {"error": f"incomplete OBO credential: {missing}"}
            return task

        # Intent hash consistency: hash the task's own intent and compare
        computed_hash = hashlib.sha256(task.intent.encode()).hexdigest()
        if computed_hash != obo["intent_hash"]:
            print("[FlightSearchAgent] ✗ REJECTED — intent_hash mismatch (tampered or drift)")
            task.status = "failed"
            task.result = {"error": "OBO intent_hash does not match task intent"}
            return task

        # Expiry check
        expires_at = datetime.datetime.fromisoformat(obo["expires_at"])
        if datetime.datetime.now(datetime.timezone.utc) > expires_at:
            print("[FlightSearchAgent] ✗ REJECTED — OBO credential expired")
            task.status = "failed"
            task.result = {"error": "OBO credential expired"}
            return task

        print(f"[FlightSearchAgent] ✓ OBO credential accepted")
        print(f"             from: {obo['operator_id']}")
        print(f"             principal: {obo['principal_id'][:40]}…")

        # Execute the task
        task.status = "working"
        task = self._execute(task)
        return task

    def _execute(self, task: A2ATask) -> A2ATask:
        """Synthetic task execution — returns plausible flight results."""
        origin = task.payload.get("origin", "LHR")
        destination = task.payload.get("destination", "JFK")
        date = task.payload.get("date", "2025-06-15")

        print(f"[FlightSearchAgent] ⚙  searching {origin} → {destination} on {date}")

        task.status = "completed"
        task.result = {
            "flights": [
                {
                    "flight_number": "BA117",
                    "origin": origin,
                    "destination": destination,
                    "departure": f"{date}T09:00:00Z",
                    "arrival": f"{date}T11:55:00Z",
                    "fare_usd": 487.00,
                    "class": "economy",
                },
                {
                    "flight_number": "VS3",
                    "origin": origin,
                    "destination": destination,
                    "departure": f"{date}T11:30:00Z",
                    "arrival": f"{date}T14:20:00Z",
                    "fare_usd": 512.00,
                    "class": "economy",
                },
            ],
            "searched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        print(f"[FlightSearchAgent] ✓ task completed — {len(task.result['flights'])} flights found")
        return task


# ─── Scenario Runner ──────────────────────────────────────────────────────────

def run_scenario(label: str, intent: str, payload: dict, tamper: bool = False):
    print(f"\n{'─' * 60}")
    print(f"SCENARIO: {label}")
    print(f"{'─' * 60}")

    travel = TravelAgent()
    search = FlightSearchAgent()

    task = travel.emit_task(intent_phrase=intent, payload=payload)

    if tamper:
        # Simulate a tampered intent (the task intent drifts from what was signed)
        original_intent = task.intent
        task.intent = "search flights from LHR to CDG on 2025-06-15"  # changed destination
        print(f"[TAMPER] intent changed: '{original_intent}' → '{task.intent}'")

    completed_task = search.receive(task)
    envelope = travel.seal_evidence(completed_task)

    print(f"\n── Evidence Envelope ──────────────────────────────────────")
    print(json.dumps(envelope.to_dict(), indent=2))
    return envelope


def main():
    # Scenario 1: Normal cross-org task, OBO credential accepted
    run_scenario(
        label="Cross-org flight search (clean)",
        intent="search flights from LHR to JFK on 2025-06-15",
        payload={"origin": "LHR", "destination": "JFK", "date": "2025-06-15"},
    )

    # Scenario 2: Second task from same agent, different intent (new credential issued)
    run_scenario(
        label="Cross-org hotel search (clean)",
        intent="search hotels in New York for 2025-06-15 to 2025-06-18",
        payload={"city": "New York", "check_in": "2025-06-15", "check_out": "2025-06-18"},
    )

    # Scenario 3: Tampered intent — receiving agent rejects
    run_scenario(
        label="Tampered intent (should be rejected)",
        intent="search flights from LHR to JFK on 2025-06-15",
        payload={"origin": "LHR", "destination": "JFK", "date": "2025-06-15"},
        tamper=True,
    )


if __name__ == "__main__":
    main()
