"""
SAPP Stub — Settlement and Audit Processing Platform (demo stub)
=================================================================
Accepts OBO Evidence Envelopes, verifies the Ed25519 envelope_sig,
stores them in memory (+ JSONL file), and returns a Merkle receipt stub.

Routes:
  POST /v1/envelopes          Accept and store an envelope
  GET  /v1/envelopes          List all stored envelopes
  GET  /v1/envelopes/<id>     Retrieve a specific envelope
  GET  /health                Health check

In production:
  - POST body would be HTTP-Message-Signed per RFC 9421 (§4.4)
  - Merkle tree would be real (inclusion proof, epoch root anchored in DNS)
  - Storage would be immutable append-only log

This stub:
  - Verifies envelope_sig (Ed25519 over evidence_digest)
  - Returns a deterministic stub Merkle leaf (SHA-256 of envelope_id + timestamp)
  - Writes envelopes to /data/envelopes.jsonl for inspection after the demo
"""

import base64
import datetime
import hashlib
import json
import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

app = Flask("sapp-stub")

# In-memory store (envelope_id → envelope dict + receipt)
_store: dict[str, dict] = {}

# JSONL file for post-demo inspection
DATA_DIR = Path(os.environ.get("SAPP_DATA_DIR", "/data"))
DATA_DIR.mkdir(exist_ok=True)
ENVELOPE_LOG = DATA_DIR / "envelopes.jsonl"


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def _load_pubkey(b64: str) -> Ed25519PublicKey:
    raw = _b64url_decode(b64)
    return Ed25519PublicKey.from_public_bytes(raw)


def _stub_merkle_leaf(envelope_id: str, anchored_at: str) -> str:
    """
    Stub Merkle leaf. In production: real Merkle tree inclusion proof.
    Here: deterministic SHA-256(envelope_id + anchored_at) for demo traceability.
    """
    return hashlib.sha256(f"{envelope_id}:{anchored_at}".encode()).hexdigest()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "envelopes_received": len(_store)})


@app.route("/v1/envelopes", methods=["POST"])
def receive_envelope():
    envelope = request.get_json(force=True)
    envelope_id = envelope.get("envelope_id", "")

    print(f"\n[SAPP] ← envelope {str(envelope_id)[:30]}…")

    # ── Required fields ───────────────────────────────────────────────────────
    required = [
        "envelope_id", "credential_id", "operator_id", "principal_id",
        "outcome", "task_correlation_ref", "evidence_digest", "envelope_sig",
    ]
    missing = [f for f in required if not envelope.get(f)]
    if missing:
        print(f"[SAPP] ✗ rejected — missing fields: {missing}")
        return jsonify({"error": f"missing fields: {missing}"}), 422

    # ── Ed25519 signature verification ────────────────────────────────────────
    pubkey_b64 = os.environ.get("TRAVEL_AGENT_PUBKEY", "")
    if pubkey_b64:
        try:
            pubkey = _load_pubkey(pubkey_b64)
            sig_bytes = _b64url_decode(envelope["envelope_sig"])
            pubkey.verify(sig_bytes, envelope["evidence_digest"].encode())
            print(f"[SAPP] ✓ envelope_sig verified (Ed25519)")
        except InvalidSignature:
            print(f"[SAPP] ✗ rejected — envelope_sig invalid")
            return jsonify({"error": "envelope_sig Ed25519 verification failed"}), 422
        except Exception as e:
            print(f"[SAPP] ⚠  sig verify error: {e}")
    else:
        print(f"[SAPP] ⚠  TRAVEL_AGENT_PUBKEY not set — sig verification skipped")

    # ── Build receipt ─────────────────────────────────────────────────────────
    anchored_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    merkle_leaf = _stub_merkle_leaf(envelope_id, anchored_at)
    receipt_id = f"sapp-receipt-{uuid.uuid4()}"

    receipt = {
        "receipt_id": receipt_id,
        "envelope_id": envelope_id,
        "merkle_leaf": merkle_leaf,
        "anchored_at": anchored_at,
        "status": "accepted",
        # In production: epoch_root, inclusion_proof, dns_anchor
        "_note": "stub receipt — production would include Merkle inclusion proof",
    }

    record = {"envelope": envelope, "receipt": receipt}
    _store[envelope_id] = record

    # Append to JSONL for post-demo inspection
    with ENVELOPE_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")

    print(f"[SAPP] ✓ accepted — merkle_leaf: {merkle_leaf[:20]}…  receipt: {receipt_id[:20]}…")
    return jsonify(receipt), 201


@app.route("/v1/envelopes", methods=["GET"])
def list_envelopes():
    summary = [
        {
            "envelope_id": v["envelope"]["envelope_id"],
            "operator_id": v["envelope"]["operator_id"],
            "outcome": v["envelope"]["outcome"],
            "task_correlation_ref": v["envelope"]["task_correlation_ref"],
            "anchored_at": v["receipt"]["anchored_at"],
            "merkle_leaf": v["receipt"]["merkle_leaf"],
        }
        for v in _store.values()
    ]
    return jsonify({"count": len(summary), "envelopes": summary})


@app.route("/v1/envelopes/<envelope_id>", methods=["GET"])
def get_envelope(envelope_id: str):
    record = _store.get(envelope_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    return jsonify(record)


if __name__ == "__main__":
    port = int(os.environ.get("SAPP_PORT", 8080))
    print(f"[SAPP stub] listening on :{port}")
    print(f"[SAPP stub] envelopes will be written to {ENVELOPE_LOG}")
    app.run(host="0.0.0.0", port=port)
