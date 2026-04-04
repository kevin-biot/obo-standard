# Captured Evidence — Live Run 2026-04-04

SAPP mint records from the reference implementation run against `lane2.ai`.
Key resolved live from public DNS — verifiable independently at any time:

```bash
dig +short TXT _obo-key.lane2.ai @8.8.8.8
# → "v=obo1 ed25519=vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"
```

## Files

| File | Scenario | Outcome | checkpoint_index |
|------|----------|---------|-----------------|
| `scenario-1-flight-search.json` | Flight search LHR→JFK | `allow` | 0 |
| `scenario-2-hotel-search.json` | Hotel search New York | `allow` | 1 |

Scenarios 3–7 (tampered intent, missing OBO, expired, forged sig, replay) were
all rejected with HTTP 422 before reaching SAPP — no evidence was minted for
those cases, which is itself the correct behaviour.

## What each file contains

Each file is the verbatim SAPP request + receipt as written to
`/data/envelopes.jsonl` inside the SAPP container, with leaves sorted
lexicographically (the order SAPP uses for Merkle construction) and a
`_capture` block added for context.

### Request (what TravelAgent submitted)

- `evidence_id` — stable URN, doubles as idempotency key
- `profile_id: regulated` — requires `producer_id`, `event_time`, `schema_ref`
- `leaves` — 14 `tag:value` strings that SAPP hashes into the Merkle tree:

  | Leaf | Binds |
  |------|-------|
  | `producer_id` | Operator identity |
  | `event_time` | Transaction timestamp |
  | `schema_ref` | Spec version |
  | `obo_credential_id` | Credential URN |
  | `obo_operator_id` | Issuing operator |
  | `obo_principal_id` | Acting principal (DID) |
  | `obo_intent_hash` | SHA-256 of the canonical intent phrase |
  | `obo_governance_ref` | Policy framework URL |
  | `obo_envelope_id` | Evidence envelope URN |
  | `obo_outcome` | `allow` / `deny` / `escalate` |
  | `obo_reason_code` | OBO-ERR-* code or `none` |
  | `obo_task_ref` | A2A task correlation ID |
  | `obo_evidence_digest` | SHA-256 pre-image of the envelope |
  | `obo_envelope_sig` | Ed25519 signature over the digest |

### Receipt (what SAPP returned)

- `evidence_bundle` — opaque handle for proof retrieval
- `merkle_root` — SHA-256 commitment over all 14 sorted leaf hashes
- `checkpoint_index` — monotonically increasing position in the Merkle log
- `tree_size` — total records at time of mint
- `created_at` — UTC timestamp of anchoring

The `checkpoint_index` incrementing from 0 → 1 across the two transactions
confirms the Merkle log is append-only and accumulates across calls.

## Verification

The `obo_envelope_sig` in each file is an Ed25519 signature over
`obo_evidence_digest`. To verify against the live DNS key:

```python
import base64, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

pubkey_b64 = "vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"
raw = base64.urlsafe_b64decode(pubkey_b64 + "==")
pubkey = Ed25519PublicKey.from_public_bytes(raw)

# From scenario-1-flight-search.json:
digest  = "f07160c23ddd9b9f111e0bf9d58f8f29bc2cc14f0cd58c40008f38b1a743b616"
sig_b64 = "nvrois4PEAUNY-3MFX8246enO18c-9MxwwAYL03nqJbPmnQRNjtYXiw1ZvhOkXMtmXKe3lbOfPsrwVFQK8xrBA"

sig = base64.urlsafe_b64decode(sig_b64 + "==")
pubkey.verify(sig, digest.encode())   # raises InvalidSignature if tampered
print("✓ envelope_sig valid")
```
