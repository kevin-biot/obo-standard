# OBO Security Guide

This document is for **implementers** — operators building OBO-issuing agents,
developers building OBO-verifying services, and operators deploying SAPP
settlement anchors. It complements §9 (Security Considerations) and §10
(Privacy Considerations) of the spec, which are written for protocol reviewers.

---

## Threat model

OBO operates at the intersection of three threat surfaces:

| Surface | Primary threat |
|---------|---------------|
| **Credential** | Forgery, replay, scope escalation |
| **Evidence envelope** | Tampering, omission, fabrication |
| **Trust anchor (DNS)** | Key substitution, cache poisoning, staleness |

OBO's cryptographic guarantees are only as strong as the weakest of these three.

---

## What OBO protects against

### Forged credentials
An attacker who does not hold the operator's Ed25519 private key cannot produce
a valid `credential_sig`. Verification fails immediately at the verifier.

**Requirement:** The private key must never leave the operator's signing
infrastructure. Treat it as a CA signing key.

### Replayed credentials
A credential that has been used once can be replayed by anyone who intercepts
it. OBO verifiers MUST maintain a `seen_credential_ids` set and reject any
`credential_id` already in the set.

**Requirement:** Implement replay detection. A credential is single-use by
design — its `intent_hash` binds it to a specific intent, which prevents
legitimate reuse.

### Intent substitution
An agent presents a credential whose `intent_hash` was computed over a different
intent phrase than the actual request. The verifier MUST recompute
`SHA-256(presented_intent_phrase)` and compare it to `intent_hash` in the
credential. A mismatch is `OBO-ERR-005`.

**Requirement:** Never skip intent hash verification. It is the binding between
authorisation and action.

### Scope escalation
A credential issued for Class A (read-only) is presented at an endpoint that
performs a Class D (regulated/high-value) action. The verifier MUST check that
the action class of the requested operation does not exceed the `action_class`
in the credential. Use `OBO-ERR-010` on violation.

**Requirement:** Every endpoint must have a declared action class. Verify before
executing.

### Tampered evidence
An operator alters an evidence envelope after the fact to change `outcome` or
`reason_code`. The `evidence_digest` pre-image is defined over all normative
fields including `reason_code` (§4.3); any alteration invalidates
`envelope_sig`.

**Requirement:** Include `reason_code` in the `evidence_digest` pre-image.
Verifiers MUST check `envelope_sig` before accepting any evidence as valid.

### Fabricated SAPP receipts
Without a SAPP operator signature on the `merkle_root`, an issuer could claim
a `merkle_root` was returned by SAPP when it was computed locally and never
submitted. The `obo_envelope_sig` proves the issuer committed to the record;
only the SAPP operator's EdDSA JWS proves SAPP received it.

**Requirement (production):** Do not accept settlement evidence without a valid
SAPP operator JWS over the checkpoint. See ADR-004 and `captures/README.md §
SAPP Merkle signing`.

---

## What OBO does not protect against

These are explicit non-goals. Implementers must address them separately.

| Non-goal | Why it is out of scope | Mitigation |
|----------|----------------------|-----------|
| **Model identity** | OBO cannot prove which model produced output — only that the operator signed | Operator is accountable for its model's output regardless |
| **Computation integrity** | The agent may have hallucinated or been manipulated | HITL approval for Class C/D; independent verification for critical outputs |
| **Private key compromise** | If the operator key is stolen, all credentials it issues are valid | Key rotation via DNS update; short credential TTLs; HSM storage |
| **DNS MITM** | A network-level attacker between verifier and DNS resolver | DNSSEC where available; pinned resolvers; curated registry as Class C/D primary check (§8.6) |
| **Colluding operator + SAPP** | If both parties collude, fabricated evidence cannot be detected by the parties alone | Epoch roots in Certificate Transparency or public logs; independent audit |
| **LLM prompt injection** | An adversarial payload causes the agent to act outside its credential scope | Intent verification at verifier; action class enforcement; HITL for Class C/D |

---

## Key management

### Private key generation

Use a cryptographically secure random source. Ed25519 keys are 32 bytes of
random seed material. Do not derive keys from passwords or other keys without
a proper KDF.

```bash
# Reference keygen (from the repo)
python examples/integrations/a2a/keygen.py
# Outputs: private_key.pem (PKCS8), public_key.b64 (base64url, 43 chars)
```

### Private key storage

- **Development:** PEM file on disk, gitignored.
- **Production:** HSM (FIPS 140-2 Level 3 minimum for Class C/D), or a secrets
  manager (AWS Secrets Manager, HashiCorp Vault) with key never materialised in
  application memory longer than needed for signing.
- **Never:** hardcoded in source, committed to git, logged, or sent over the
  wire.

### Public key publication (DNS)

```
_obo-key.<operator_id>  IN TXT  "v=obo1 ed25519=<base64url pubkey>"
```

- The `<base64url pubkey>` is the raw 32-byte Ed25519 public key, base64url
  encoded without padding (43 characters).
- **TTL:** 60–300 seconds for production. Short TTL allows timely key rotation
  and limits the window during which a stolen or compromised key remains
  operationally valid to verifiers.
- **For Class C/D:** §8.6 states verifiers MUST NOT rely solely on cached DNS.
  Maintain a curated registry of high-value known counterparties and use DNS
  as a trip-wire, not the primary check.

### Key rotation

1. Generate new key pair.
2. Update DNS TXT record with new public key.
3. Wait for TTL to expire (all verifiers now use new key).
4. Re-issue any long-lived credentials signed with the old key.
5. Retain old private key offline for audit purposes (to verify historical
   signatures); never use it to issue new credentials.

There is no revocation mechanism in the current spec (v0.3.0). Rotation via
DNS is the primary mitigation. Implementers requiring hard revocation should
track `credential_id` blocklists out-of-band.

---

## Verifier hardening checklist

- [ ] Verify `credential_sig` before any other check. Fail-closed on any
      verification error.
- [ ] Resolve operator key from DNS on every transaction (not cached
      indefinitely). For Class C/D: consult curated registry as primary.
- [ ] Maintain `seen_credential_ids` set. Reject replays with `OBO-ERR-008`.
- [ ] Recompute `SHA-256(intent_phrase)` and compare to `intent_hash`. Reject
      mismatches with `OBO-ERR-005`.
- [ ] Enforce action class ceiling for every endpoint. Reject escalation with
      `OBO-ERR-010`.
- [ ] Check `not_before` / `not_after` validity window. Reject expired
      credentials with `OBO-ERR-003`.
- [ ] For Class C/D: require and verify Delegation Chain Artifact (§3.3).
      Deferred verification is not permitted.
- [ ] For Class C/D: require and verify Intent Artifact (§3.4) including
      `principal_sig` and `authorisation_evidence`.
- [ ] Emit `reason_code` in all rejection responses. Include `obo_reason_code`
      leaf in evidence for rejected transactions.

---

## Issuer hardening checklist

- [ ] Store private key in HSM or secrets manager for Class C/D use.
- [ ] Set short credential TTLs (minutes, not hours) for Class C/D.
- [ ] Set `action_class` to the minimum required for the intended operation.
      Never over-provision.
- [ ] Include `reason_code: none` in the `evidence_digest` pre-image even for
      allow outcomes (ensures field is always covered by the signature).
- [ ] Submit evidence to SAPP immediately post-transaction. Do not batch.
- [ ] For production: require SAPP operator JWS on checkpoint before treating
      evidence as settled.
- [ ] For Class C/D with delegation: sign the delegation chain document
      (`link_sig`) at each hop. Verify chain integrity before issuing
      descendant credentials.

---

## Error codes quick reference

Full taxonomy in §5 of the spec. Most security-relevant codes:

| Code | Meaning | Verifier action |
|------|---------|----------------|
| `OBO-ERR-001` | Missing OBO extension | Reject, 422 |
| `OBO-ERR-003` | Credential expired | Reject, 422 |
| `OBO-ERR-004` | Invalid signature | Reject, 422 |
| `OBO-ERR-005` | Intent hash mismatch | Reject, 422 |
| `OBO-ERR-006` | Operator key not found | Reject, 422 |
| `OBO-ERR-008` | Credential replayed | Reject, 422 |
| `OBO-ERR-010` | Action class exceeded | Reject, 422 |

All codes return `{"error": "<message>", "reason_code": "OBO-ERR-NNN"}` in the
response body. Log every rejection with the `reason_code` for audit purposes.
