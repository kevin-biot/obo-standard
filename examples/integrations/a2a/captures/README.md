# Captured Evidence — Live Run 2026-04-04

> **Note on terminology:** The records in this directory were captured against
> **SAPP (Secure Agent Payment Protocol)**, the internal reference
> implementation of the Evidence Anchor interface used in this project.
> SAPP is a product of Lane2. The Evidence Anchor interface it implements
> is defined generically in the OBO spec (§4); any conforming Evidence Anchor
> may be substituted. References to SAPP throughout this directory reflect the
> actual product used in the captured run and are left unchanged as historical
> record.

Evidence Anchor (SAPP) mint records from the reference implementation run against `lane2.ai`.
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

## Verification — OBO envelope signature (issuer key)

The `obo_envelope_sig` in each file is an Ed25519 signature by the **issuing
operator** (TravelAgent / lane2.ai) over `obo_evidence_digest`. Verifiable
against the live DNS key right now:

```python
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Issuer public key — live in DNS:
#   dig +short TXT _obo-key.lane2.ai @8.8.8.8
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

---

## Extended evidence — delegation and intent artifacts

The 14 leaves in these captures are the **minimum viable OBO evidence
set**. The architecture is designed as a carrier: operators and agents
can bind arbitrarily rich evidence into the same Merkle root by adding
leaves. Two artifacts defined in the spec (§3.3 and §3.4) are the most
important extensions — they are what make OBO evidence useful for
regulated industries and legally meaningful in dispute resolution.

### What the demo leaves don't show

The current 14 leaves establish:
- *Who* acted (`obo_operator_id`, `obo_principal_id`)
- *What* was intended (`obo_intent_hash`)
- *What happened* (`obo_outcome`, `obo_task_ref`)
- *That the record is intact* (`obo_evidence_digest`, `obo_envelope_sig`)

What they do not establish:
- *On what authority* the principal was delegated to act
- *That a human explicitly approved* this specific intent
- *How* the principal's identity was verified
- *What constraints* the principal imposed at authorisation time

The Delegation Chain Artifact (§3.3) and Intent Artifact (§3.4) fill
these gaps. Together they turn `obo_principal_id: did:key:z6Mk…` — a
cryptographic identifier — into a full accountability record that a
regulator, court, or compliance auditor can work with.

### What a rich evidence set looks like

The following shows what the Scenario 1 leaf set would look like with
both artifacts fully bound. New leaves are marked `(§3.3)` or `(§3.4)`:

```
# ── Regulated profile required ────────────────────────────────
event_time:2026-04-04T11:55:07.038933+00:00
producer_id:lane2.ai
schema_ref:draft-obo-agentic-evidence-envelope-00

# ── OBO credential provenance ─────────────────────────────────
obo_credential_id:urn:obo:cred:1d8d3842-…
obo_governance_ref:https://example.com/obo/v1/policy
obo_operator_id:lane2.ai
obo_principal_id:did:key:z6MkhaXgBZ…

# ── Delegation chain (§3.3) ───────────────────────────────────
delegation_id:urn:obo:del:9f4e2a1b-…              (§3.3)
delegation_chain_digest:7f3a9b2c8e…               (§3.3)
delegation_depth:1                                 (§3.3)
delegation_issuer_sig:Ed25519-base64url…           (§3.3)

# ── Intent artifact (§3.4) ────────────────────────────────────
intent_id:urn:obo:intent:3c7d5f2a-…               (§3.4)
intent_authorised_at:2026-04-04T11:54:58Z          (§3.4)
intent_authorisation_method:explicit_approval      (§3.4)
intent_principal_sig:Ed25519-base64url…            (§3.4)
intent_operator_sig:Ed25519-base64url…             (§3.4)
obo_intent_hash:b98d4238ecb978415a30…

# ── Authorisation evidence / biometric (§3.4.4) ───────────────
biometric_method:face_id                           (§3.4)
biometric_provider:apple_faceid                    (§3.4)
biometric_score:0.987                              (§3.4)
biometric_verified_at:2026-04-04T11:54:55Z         (§3.4)
kyc_level:enhanced                                 (§3.4)
kyc_ref:jumio-kyc-abc123                           (§3.4)

# ── Evidence envelope binding ─────────────────────────────────
obo_envelope_id:urn:obo:env:523068f5-…
obo_envelope_sig:nvrois4PEAUNY-…
obo_evidence_digest:f07160c23ddd9b9f…
obo_outcome:allow
obo_reason_code:none
obo_task_ref:task-0fe230c3-…
```

That is 30 leaves vs 14. All 30 are committed into a single
`merkle_root`. A compliance auditor receives one hash that commits to
the complete picture — the delegation chain, the biometric check, the
principal's explicit approval signature, and the transaction outcome.
No component can be presented or withheld independently.

### Why this matters for regulated industries

| What is provable with 14 leaves | What is additionally provable with 30 |
|---------------------------------|---------------------------------------|
| An agent acted under operator `lane2.ai` | Acme Corp delegated to the agent, within scope £500 economy only |
| The intent matched the credential | Alice Chen signed this specific intent at 11:54:58 |
| The outcome was `allow` | Alice's face ID matched at 11:54:55 with score 0.987 |
| The record has not been tampered | Alice is KYC-verified at `enhanced` level (Jumio ref: abc123) |

The 14-leaf version is technically auditable. The 30-leaf version is
**legally producible** — to a regulator under PSD2 Art. 74, to a court
in a dispute, to a compliance officer under EU AI Act Art. 12. The
difference is not the cryptography (both use the same Merkle root); it
is what the root commits to.

### The `--rich` demo mode

The reference implementation does not yet emit these extended leaves.
A future `--rich` flag for TravelAgent will add delegation chain +
intent artifact + stub biometric leaf to the SAPP submission, showing
extensibility concretely. See §3.3 and §3.4 of the spec for the full
canonical schemas and signing requirements.

---

## SAPP Merkle signing — what the demo omits and best practice

### What the stub does (and does not do)

The `merkle_root` in each receipt is a real SHA-256 commitment over all 14
sorted leaf hashes — the binding is genuine. However, the JWS returned by
`GET /evidence/{id}/proof` in the stub is **not cryptographically signed**:
it is computed as `SHA-256(header.payload)` with no SAPP operator key. The
`merkle_root` therefore has no independent attestation — only the issuer's
word that it was anchored.

This is intentional for a self-contained demo stub. It does **not** reflect
production requirements.

### Why the SAPP operator must sign the checkpoint

Without a SAPP operator signature, a malicious issuer could fabricate a
`merkle_root` value and claim it was returned by SAPP. The issuer's
`obo_envelope_sig` proves *they* committed to the record; it does not prove
SAPP *received* it. The SAPP operator's signature is a **second independent
party** attesting: "I received this record at this position in my log."

This closes the accountability chain:

```
Issuer Ed25519         → obo_envelope_sig     proves intent + outcome
       ↓
SAPP merkle_root       → SHA-256 over 14 leaves  commits the full record
       ↓
SAPP operator Ed25519  → JWS over checkpoint     attests SAPP received it
       ↓
Epoch root in DNS / CT → anchors the log root    prevents retroactive rewrite
```

### Production JWS payload (ADR-181 E7)

The SAPP operator signs a compact checkpoint structure:

```json
{
  "alg": "EdDSA",
  "typ": "SAPP-PROOF+JWT"
}
.
{
  "evidence_id":     "urn:obo:env:523068f5-…",
  "merkle_root":     "4f29251a3d5a565c53a1…",
  "checkpoint_index": 0,
  "tree_size":        1,
  "created_at":      "2026-04-04T11:55:07Z",
  "iss":             "sapp.example.com"
}
```

The `sig` part of the compact JWS (`header.payload.sig`) is a real Ed25519
signature over `base64url(header) + "." + base64url(payload)` — not a hash.

### SAPP operator key DNS anchor

The SAPP operator publishes its verifying key using the same DNS pattern as
OBO issuers:

```
_sapp-key.sapp.example.com  IN TXT  "v=sapp1 ed25519=<base64url pubkey>"
```

Verifiers resolve this record to check the JWS. TTL should be short (60–300 s)
for the same reasons as `_obo-key`: stale cached keys are a liability for
high-value transactions.

### Epoch root anchoring (prevents retroactive rewrite)

Periodically (every N minutes or every N records), the SAPP operator publishes
the current epoch root to a public transparency log or DNS:

```
_sapp-epoch-<N>.sapp.example.com  IN TXT  "v=sapp1 root=<merkle_root> size=<tree_size>"
```

Once the epoch root is externally witnessed, no record in the log can be
silently removed or reordered — any such change would produce a different
root. This is the same guarantee Certificate Transparency provides for TLS
certificates.

### What a real receipt looks like

In production, `GET /evidence/{id}/proof` returns:

```json
{
  "evidence_id":      "urn:obo:env:523068f5-…",
  "merkle_root":      "4f29251a3d5a565c53a1…",
  "inclusion_proof":  ["<sibling hash 0>", "<sibling hash 1>", "…"],
  "proof_depth":      14,
  "checkpoint_index": 0,
  "tree_size":        1,
  "jws":              "<base64url header>.<base64url payload>.<Ed25519 sig>"
}
```

The `inclusion_proof` array lets a verifier recompute the `merkle_root` from
the single leaf hash and the sibling path — without trusting the SAPP operator
to have included the correct root. The `jws` then attests to that root.

The captures in this directory have the `merkle_root` and `checkpoint_index`;
they are missing the `inclusion_proof` and the real `jws`. That is the gap
between this demo and a production settlement anchor.
