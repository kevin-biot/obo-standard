"""
Evidence Anchor Stub — reference implementation of the Evidence Anchor interface
================================================================================
Accepts OBO Evidence Envelopes, stores them in memory (+ JSONL file), and
returns stub Merkle receipts.

This stub is based on SAPP (Secure Agent Payment Protocol), the internal
reference implementation of the Evidence Anchor interface. The API design
follows internal reference implementation specs (mint API, signed proof API).
Any conforming Evidence Anchor may be substituted.

Routes:
  POST /v1/evidence/mint       Accept and mint evidence
  GET  /evidence/<id>/proof    Return stub signed Merkle proof
  GET  /v1/envelopes           List all stored evidence records
  GET  /v1/envelopes/<id>      Retrieve a specific record
  GET  /health                 Health check

In production:
  - POST body would be HTTP-Message-Signed per RFC 9421 (§4.4)
  - Merkle tree would be real (inclusion proof, epoch root anchored in DNS)
  - Storage would be immutable append-only log
  - Proof JWS would be signed by Evidence Anchor operator key

This stub:
  - Accepts any valid JSON with 'leaves' array
  - Returns deterministic stub merkle_root (SHA-256 over sorted leaves)
  - Writes records to /data/envelopes.jsonl for post-demo inspection
"""

import base64
import datetime
import hashlib
import json
import os
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask("sapp-stub")

# In-memory store: evidence_id → {request, receipt}
_store: dict[str, dict] = {}

# JSONL file for post-demo inspection
DATA_DIR = Path(os.environ.get("ANCHOR_DATA_DIR", "/data"))
DATA_DIR.mkdir(exist_ok=True)
ENVELOPE_LOG = DATA_DIR / "envelopes.jsonl"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _stub_merkle_root(leaves: list[str], evidence_id: str) -> str:
    """
    Stub Merkle root. In production: real Merkle tree over sorted leaf hashes.
    Here: SHA-256 over sorted leaf strings + evidence_id for determinism.
    """
    sorted_leaves = sorted(leaves)
    payload = evidence_id + ":" + "|".join(sorted_leaves)
    return hashlib.sha256(payload.encode()).hexdigest()


def _stub_evidence_bundle(evidence_id: str, merkle_root: str, created_at: str) -> str:
    """
    Stub evidence bundle handle. In production: opaque Evidence Anchor-issued bundle ID.
    Here: base64url(SHA-256(evidence_id + merkle_root + created_at)).
    """
    raw = hashlib.sha256(f"{evidence_id}:{merkle_root}:{created_at}".encode()).digest()
    return _b64url_encode(raw)


def _stub_proof_jws(evidence_id: str, merkle_root: str) -> str:
    """
    Stub JWS compact proof. In production: Evidence Anchor operator Ed25519 over inclusion proof.
    Here: base64url(JSON header).base64url(JSON payload).stub_sig — not valid for crypto,
    but structurally correct for demo code paths that parse .split('.').
    """
    header  = _b64url_encode(json.dumps({"alg": "EdDSA", "typ": "ANCHOR-PROOF+JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "evidence_id": evidence_id,
        "merkle_root": merkle_root,
        "proof_depth": 3,
        "iss": "sapp-stub",
    }).encode())
    stub_sig = _b64url_encode(hashlib.sha256(f"{header}.{payload}".encode()).digest())
    return f"{header}.{payload}.{stub_sig}"


@app.route("/health")
def health():
    return jsonify({"status": "ok", "records": len(_store)})


@app.route("/v1/evidence/mint", methods=["POST"])
def mint_evidence():
    """
    Evidence Anchor mint endpoint.
    Accepts: {evidence_id, profile_id, leaves: [...], org_id?}
    Returns: {evidence_bundle, merkle_root, checkpoint_index, tree_size, created_at}
    """
    body = request.get_json(force=True)
    evidence_id = body.get("evidence_id") or str(uuid.uuid4())
    profile_id  = body.get("profile_id", "default")
    leaves      = body.get("leaves", [])
    org_id      = body.get("org_id", "")

    print(f"\n[anchor] ← /v1/evidence/mint  id={str(evidence_id)[:30]}…  profile={profile_id}  leaves={len(leaves)}")

    if not leaves:
        print(f"[anchor] ✗ rejected — empty leaves")
        return jsonify({"error": "leaves must be a non-empty array"}), 422

    # ── Profile validation ────────────────────────────────────────────────────
    required_by_profile = {
        "regulated":              {"producer_id", "event_time", "schema_ref"},
        "regulated_eu_finance":   {"producer_id", "event_time", "schema_ref"},
        "default":                set(),
    }
    required_prefixes = required_by_profile.get(profile_id, set())
    leaf_keys = {leaf.split(":", 1)[0] for leaf in leaves if ":" in leaf}
    missing_keys = required_prefixes - leaf_keys
    if missing_keys:
        print(f"[anchor] ✗ rejected — profile '{profile_id}' requires leaves: {missing_keys}")
        return jsonify({
            "error":           f"profile '{profile_id}' requires leaves",
            "missing_leaves":  sorted(missing_keys),
        }), 422

    # ── Idempotency — return existing receipt if already minted ──────────────
    if evidence_id in _store:
        existing = _store[evidence_id]["receipt"]
        print(f"[anchor] ↩  idempotent replay — returning existing receipt")
        return jsonify(existing), 200

    # ── Build receipt ─────────────────────────────────────────────────────────
    created_at        = datetime.datetime.now(datetime.timezone.utc).isoformat()
    merkle_root       = _stub_merkle_root(leaves, evidence_id)
    evidence_bundle   = _stub_evidence_bundle(evidence_id, merkle_root, created_at)
    checkpoint_index  = len(_store)            # monotonic counter (stub)
    tree_size         = checkpoint_index + 1

    receipt = {
        "evidence_bundle":   evidence_bundle,
        "merkle_root":       merkle_root,
        "checkpoint_index":  checkpoint_index,
        "tree_size":         tree_size,
        "created_at":        created_at,
        # ── extra metadata for inspection ──────────────────────────────────────
        "evidence_id":       evidence_id,
        "profile_id":        profile_id,
        "_note":             "stub receipt — production has real Merkle inclusion proof",
    }

    record = {"request": body, "receipt": receipt}
    _store[evidence_id] = record

    # Append to JSONL
    with ENVELOPE_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")

    print(f"[anchor] ✓ minted — merkle_root: {merkle_root[:20]}…  bundle: {evidence_bundle[:20]}…  idx: {checkpoint_index}")
    return jsonify(receipt), 201


@app.route("/evidence/<evidence_id>/proof", methods=["GET"])
def get_proof(evidence_id: str):
    """
    Signed Merkle proof for an anchored evidence record.
    Returns stub JWS: header.payload.sig (structurally valid, not cryptographically bound).
    """
    record = _store.get(evidence_id)
    if not record:
        return jsonify({"error": "evidence_id not found"}), 404

    merkle_root = record["receipt"]["merkle_root"]
    jws         = _stub_proof_jws(evidence_id, merkle_root)

    response = {
        "evidence_id":  evidence_id,
        "merkle_root":  merkle_root,
        "proof_depth":  3,
        "jws":          jws,
        "_note":        "stub JWS — production is Evidence Anchor operator Ed25519 over inclusion proof",
    }
    print(f"[anchor] → /evidence/{str(evidence_id)[:20]}…/proof  JWS: {jws[:30]}…")
    return jsonify(response)


# ── Legacy inspection routes ──────────────────────────────────────────────────

@app.route("/v1/envelopes", methods=["GET"])
def list_envelopes():
    summary = [
        {
            "evidence_id":  v["receipt"]["evidence_id"],
            "profile_id":   v["receipt"]["profile_id"],
            "merkle_root":  v["receipt"]["merkle_root"],
            "created_at":   v["receipt"]["created_at"],
        }
        for v in _store.values()
    ]
    return jsonify({"count": len(summary), "records": summary})


@app.route("/v1/envelopes/<evidence_id>", methods=["GET"])
def get_envelope(evidence_id: str):
    record = _store.get(evidence_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    return jsonify(record)


if __name__ == "__main__":
    port = int(os.environ.get("ANCHOR_PORT", 8080))
    print(f"[anchor stub] listening on :{port}")
    print(f"[anchor stub] records will be written to {ENVELOPE_LOG}")
    app.run(host="0.0.0.0", port=port)
