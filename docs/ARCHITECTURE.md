# OBO Architecture

## Overview

OBO (On-Behalf-Of) is an accountability layer for agentic transactions. It does
not replace transport security, identity federation, or authorisation frameworks
— it adds the missing link: **cryptographic evidence that a specific human
authorised a specific agent to perform a specific action, recorded before and
after the transaction, independently verifiable by any party.**

---

## Core problem

When an agent acts on behalf of a human, five questions must be answerable after
the fact:

1. **Who authorised this?** — The human principal, identified and verified.
2. **What was authorised?** — The intent, in canonical form, hash-bound.
3. **On what authority?** — The delegation chain from issuing operator to acting
   agent.
4. **What happened?** — The transaction outcome, with outcome code.
5. **Is the record intact?** — Cryptographic proof that none of the above has
   been altered.

No existing standard answers all five together for multi-hop agentic
transactions. OBO answers all five.

---

## Component map

```
  ┌────────────────────────────────────────────────────────────────────┐
  │  PRE-TRANSACTION                                                   │
  │                                                                    │
  │  Human Principal                                                   │
  │       │  approves intent phrase                                    │
  │       ▼                                                            │
  │  Operator (Issuer)                                                 │
  │       │  issues OBO Credential (Ed25519 signed)                    │
  │       │  • intent_hash = SHA-256(intent_phrase)                    │
  │       │  • credential_sig over canonical fields                    │
  │       │  • action_class A/B/C/D                                    │
  │       │                                                            │
  │       │  optionally: Delegation Chain Artifact (§3.3)              │
  │       │              Intent Artifact (§3.4)                        │
  │       ▼                                                            │
  │  OBO Credential ──────────────────────────────────────────────►   │
  │                         (attached to A2A task or API call)        │
  └────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │  AT THE VERIFIER (Receiving Agent / Service)                       │
  │                                                                    │
  │  1. Resolve operator key via DNS                                   │
  │       _obo-key.<operator_id> IN TXT "v=obo1 ed25519=<pubkey>"     │
  │  2. Verify credential_sig                                          │
  │  3. Check action_class ≤ permitted for this endpoint               │
  │  4. Verify intent_hash matches presented intent                    │
  │  5. Check expiry, replay (seen credential_ids set)                 │
  │  6. For Class C/D: verify full delegation chain + intent artifact  │
  │                                                                    │
  │  ALLOW → execute task                                              │
  │  DENY  → HTTP 422 {error, reason_code: OBO-ERR-*}                 │
  └────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │  POST-TRANSACTION                                                  │
  │                                                                    │
  │  Operator                                                          │
  │       │  assembles OBO Evidence Envelope                           │
  │       │  • evidence_digest = SHA-256(canonical fields)             │
  │       │  • envelope_sig = Ed25519(evidence_digest)                 │
  │       │                                                            │
  │       ▼                                                            │
  │  Evidence Anchor POST /v1/evidence/mint                                       │
  │       │  leaves = [tag:value …] sorted lexicographically           │
  │       │  merkle_root = SHA-256 over all leaf hashes                │
  │       │  checkpoint_index monotonically increasing                 │
  │       │                                                            │
  │       ▼                                                            │
  │  Evidence Anchor Receipt                                                      │
  │       • evidence_bundle (opaque handle)                            │
  │       • merkle_root                                                │
  │       • checkpoint_index, tree_size, created_at                   │
  │                                                                    │
  │  Production: Evidence Anchor operator signs checkpoint (EdDSA JWS)           │
  │  Epoch root anchored in DNS / CT log                               │
  └────────────────────────────────────────────────────────────────────┘
```

---

## Two artifacts, two moments

OBO produces exactly two artifacts per transaction:

| Artifact | Moment | Signed by | Purpose |
|----------|--------|-----------|---------|
| **OBO Credential** | Before | Issuing operator | Authorises the action |
| **OBO Evidence Envelope** | After | Acting operator | Records what happened |

These are deliberately separate. The credential is a pre-commitment; the
envelope is a post-record. Neither alone is sufficient. Together they close the
accountability loop.

---

## Trust hierarchy

```
  DNS  ─────────────────────────────────────────────────────────┐
  (operator public keys, corridor predicates, Evidence Anchor epoch roots)  │
                                                                  │
  Issuing Operator                                                │
       │  issues credential, signs envelope                       │
       │  anchors key in DNS                                      │
       ▼                                                          │
  Acting Agent                                                    │
       │  presents credential to verifier                         │
       │  submits evidence to Evidence Anchor                               │
       ▼                                                          │
  Verifier (Receiving Agent / Service)                            │
       │  resolves key from DNS ◄──────────────────────────────┘ │
       │  verifies credential sig                                  │
       │  enforces action class                                    │
       ▼                                                          │
  Evidence Anchor (Settlement / Audit / Proof Provider)                      │
       │  anchors merkle_root                                      │
       │  signs checkpoint (production)                           │
       │  epoch root in DNS / CT                                  │
```

No component trusts another on assertion alone. Every trust relationship has a
cryptographic verification step backed by a DNS-anchored public key or a
Merkle-anchored log entry.

---

## Action classes

OBO defines four action classes that govern verification stringency:

| Class | Description | Delegation chain required | Intent artifact required |
|-------|-------------|--------------------------|--------------------------|
| **A** | Read-only, informational | No | No |
| **B** | Write, reversible | No | No |
| **C** | Write, irreversible | Yes | Yes |
| **D** | Regulated / high-value | Yes | Yes (+ authorisation evidence) |

The action class is set in the credential by the issuing operator. Verifiers
MUST enforce that the requested action does not exceed the class bound. Scope
MUST NOT widen at any delegation hop.

---

## Evidence layers

Each evidence layer adds auditability. All layers share the same `merkle_root`:

```
Layer 0 — Minimum viable (14 leaves)
  who acted, what was intended, what happened, record integrity

Layer 1 — + Delegation chain (§3.3, +4 leaves)
  on what authority, depth of delegation, delegating-party signature

Layer 2 — + Intent artifact (§3.4, +12 leaves)
  human approval proof, authorisation method, timestamp, biometric facts, KYC

Total: up to 30 leaves, one merkle_root
```

A compliance auditor receives one hash that commits to the complete picture. No
component can be presented or withheld independently.

---

## DNS anchoring

OBO uses DNS as a decentralised public key registry. No central OBO registry
exists or is required.

```
Operator key:     _obo-key.<operator_id>     IN TXT  "v=obo1 ed25519=<pubkey>"
Evidence Anchor key: _anchor-key.<anchor_domain>  IN TXT  "v=anchor1 ed25519=<pubkey>"
Corridor gate:    _obo-corridor.<domain>     IN TXT  "v=obo1 permit=<class>"
Epoch root:       _anchor-epoch-<N>.<domain> IN TXT  "v=anchor1 root=<root> size=<n>"
```

TTL guidance: 60–300 s for operator keys (stale cached keys are a liability for
Class C/D). Epoch roots are append-only; TTL can be longer.

See ADR-001 for the rationale for DNS over a centralised registry.

---

## Integration with A2A

OBO attaches to A2A tasks via the `extensions` map on `TaskSendParams`. The
receiving agent's Agent Card signals OBO requirement at the protocol level:

```json
{
  "authentication": {
    "schemes": ["obo"]
  }
}
```

The receiving agent fetches the Agent Card on startup, discovers the OBO
requirement, and enforces it before processing any task. This makes OBO
requirement machine-readable rather than out-of-band.

See `examples/integrations/a2a/` for the Docker reference implementation.

---

## Spec sections map

| Topic | Spec section |
|-------|-------------|
| OBO Credential fields | §3.1, §3.2 |
| Delegation Chain Artifact | §3.3 |
| Intent Artifact | §3.4 |
| Signing requirements | §3.5 |
| Evidence Envelope fields | §4.1–§4.5 |
| Error codes | §5 |
| Profiles | §6 |
| Verification algorithm | §7 |
| Relationship to existing standards | §8 |
| Security considerations | §9 |
| Privacy considerations | §10 |
| DNS Anchoring Profile | Appendix E |
| DID Profile | Appendix F |
