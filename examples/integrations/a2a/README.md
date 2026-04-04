# OBO + A2A Composition Example

**Illustrative reference — not a production implementation.**

This example shows how OBO credentials and evidence envelopes compose with
the [A2A task protocol](https://github.com/a2aproject/A2A). Two synthetic
agents exchange tasks across a trust boundary with no shared OAuth
authorisation server.

---

## The Problem This Solves

A2A's authentication model (OAuth 2.0 / OIDC) works well inside a single
trust domain with a shared authorisation server. It does not cover:

- First-contact between two organisations that have never met
- Agent-to-agent interactions where no shared AS exists
- Post-hoc audit and non-repudiation of what agent acted, on whose behalf

OBO is not a replacement for OAuth inside a trust domain. OBO is the
accountability layer for the case where no shared AS is the right answer —
the boundary itself is the authority.

---

## What the Example Shows

```
TravelAgent (travel-agent.example.com)          FlightSearchAgent (flight-search.example.com)
       │                                                    │
       │  emit_task(intent, payload)                        │
       │  ─────────────────────────────────────────────────►│
       │  A2A Task                                          │
       │    extensions.obo.credential_id                   │  verifies:
       │    extensions.obo.operator_id     ────────────────►│  · OBO fields present
       │    extensions.obo.principal_id                     │  · intent_hash consistent
       │    extensions.obo.intent_hash                      │  · not expired
       │    extensions.obo.credential_sig                   │  · (prod: Ed25519 sig verify)
       │                                                    │
       │  ◄─────────────────────────────────────────────────│
       │  Completed A2A Task (task.id anchors evidence)     │
       │                                                    │
       │  seal_evidence(completed_task)                     │
       │  OBO Evidence Envelope                             │
       │    task_correlation_ref = task.id   ─────────────► audit / SAPP / Merkle
```

### OBO → A2A field mapping

| OBO Credential field        | A2A Task location                        |
|-----------------------------|------------------------------------------|
| `credential_id`             | `extensions.obo.credential_id`           |
| `operator_id`               | `extensions.obo.operator_id`             |
| `principal_id`              | `extensions.obo.principal_id`            |
| `intent_hash`               | `extensions.obo.intent_hash`             |
| `issued_at` / `expires_at`  | `extensions.obo.issued_at/expires_at`    |
| `credential_sig`            | `extensions.obo.credential_sig`          |

### A2A → OBO Evidence Envelope mapping

| A2A Task field   | OBO Evidence Envelope field              |
|------------------|------------------------------------------|
| `task.id`        | `task_correlation_ref`                   |
| `task.status`    | `outcome` (`completed` → `allow`)        |
| `task.result`    | included in `evidence_digest` pre-image  |

---

## Running

```bash
# No dependencies — stdlib only
python3 agents.py
```

Expected output (three scenarios):

```
────────────────────────────────────────────────────────────
SCENARIO: Cross-org flight search (clean)
────────────────────────────────────────────────────────────
[TravelAgent] → emitting task abc123…
[FlightSearchAgent] ← received task abc123…
[FlightSearchAgent] ✓ OBO credential accepted
[FlightSearchAgent] ⚙  searching LHR → JFK on 2025-06-15
[FlightSearchAgent] ✓ task completed — 2 flights found
[TravelAgent] ✓ evidence envelope sealed

────────────────────────────────────────────────────────────
SCENARIO: Tampered intent (should be rejected)
────────────────────────────────────────────────────────────
[TAMPER] intent changed: 'search flights from LHR to JFK…' → '…LHR to CDG…'
[FlightSearchAgent] ✗ REJECTED — OBO intent_hash mismatch (tampered or drift)
```

---

## What Is Simplified Here

This example uses stdlib only (no external dependencies) and synthetic
signatures. A production implementation would:

| This example | Production |
|---|---|
| SHA-256 "synthetic sig" | Ed25519 signature with operator private key |
| Structural OBO field check | DNS resolution of `_obo-key.<operator_id>` TXT (Appendix E) or `did:web` DID Document (Appendix F), then Ed25519 verify |
| In-memory task passing | HTTP POST with A2A task schema over the wire |
| No SAPP/Merkle submission | POST evidence envelope to SAPP/Merkle with HTTP Message Signature [RFC 9421] per §4.4 |

---

## Two Patterns for A2A + OBO

**Pattern 1 — within a trust domain (shared AS)**
OAuth 2.0 / OIDC works. OBO is optional. If used, the evidence envelope
provides a post-hoc audit record that OAuth alone does not.

**Pattern 2 — cross-org, no shared AS (first-contact)**
OAuth requires a shared trust anchor. When none exists, OBO is the
accountability layer. The receiving agent verifies the OBO credential
against the sending operator's published key (DNS or DID). No AS required.

This example demonstrates Pattern 2.

---

## Spec References

- [draft-obo-agentic-evidence-envelope-00](../../draft-obo-agentic-evidence-envelope-00.md)
- §3.1 — OBO Credential structure
- §3.2 — OBO Evidence Envelope structure
- §4.4 — Submission Integrity (HTTP Message Signatures)
- Appendix E — DNS Anchoring (`_obo-key` TXT record)
- Appendix F — DID Profile (did:web, did:key, did:ebsi)
