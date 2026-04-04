# ADR-010: Agent Instance Binding in OBO Credentials

**Status:** Accepted
**Date:** 2026-04-05
**Refs:** `schemas/obo-credential.json`, §3, ADR-002

---

## Context

The OBO Credential binds a principal to an agent via `agent_id`. The
`agent_id` identifies the **agent class** — the named agent, its type,
its published identity. It does not bind to a specific running instance
of that agent.

This leaves a narrow but real attack surface:

1. **Credential theft with instance substitution** — an attacker obtains
   a valid OBO Credential and presents it from a different agent binary
   or compromised runtime. The credential is valid; the presenting
   instance is not the one the principal authorized.

2. **Runtime substitution** — a legitimate agent's credential is
   replayed by a different process. Class-level binding cannot detect
   this.

The emerging A2A ecosystem includes runtime authorization schemes (e.g.
OATR) that address instance-level binding via short-lived signed JWTs
from the agent's runtime. However, these schemes require a shared
registry and cannot operate cross-org at first contact — the exact
scenario OBO is designed for.

OBO should close this gap natively, without requiring a shared registry,
by adding optional instance binding fields to the OBO Credential.

## Decision

Two optional fields are added to the OBO Credential:

**`agent_instance_id`** — a stable identifier for the specific agent
instance. Scheme is operator-defined (URN, DID, infrastructure ID).

**`agent_instance_pubkey`** — the Ed25519 public key of the instance.
The instance MUST sign the credential presentation with the
corresponding private key. Counterparties verify the presentation
signature against this field.

These fields are **optional**. When absent, class-level binding applies
— appropriate for lower-assurance corridors (Class A/B). When present,
instance-level binding is enforced — required for high-assurance
corridors (Class C/D in regulated or sovereign tiers).

The governance pack MAY declare `instance_binding_required: true` to
mandate these fields for all credentials issued under the pack.

## Mechanism

```
Issuance:
  1. Agent instance generates Ed25519 keypair at startup
  2. Instance public key included in OBO Credential as agent_instance_pubkey
  3. Credential issued and signed by operator (as before)
  4. Credential digest covers agent_instance_pubkey

Presentation:
  1. Agent instance presents OBO Credential to counterparty
  2. Instance signs the presentation payload with instance private key
     Payload: sha256(credential_digest || task_id || timestamp)
  3. Counterparty verifies:
     a. Credential valid (DNS anchor, expiry, governance) — as before
     b. Presentation signature verifies against agent_instance_pubkey
     c. Same instance that was credentialed is presenting

Attack resistance:
  - Stolen credential: useless without instance private key
  - Instance substitution: presentation signature fails
  - Replay: task_id + timestamp in signed payload prevents reuse
```

## Why This Subsumes External Runtime Authorization

Runtime authorization schemes (OATR and equivalents) solve the same
instance binding problem via a different mechanism: short-lived JWTs
issued by a registry, checked at runtime.

The OBO instance binding approach differs in three ways:

1. **No shared registry required** — the instance public key is in the
   credential itself, verified against the credential digest. DNS is
   the only infrastructure needed. Works cross-org at first contact.

2. **Durable binding** — the instance key is bound for the credential
   validity window, not 300 seconds. Appropriate for long-running
   agentic sessions without repeated re-authorization round-trips.

3. **Composable** — external runtime authorization schemes MAY be used
   alongside OBO instance binding for defence-in-depth in high-security
   deployments. They are not required.

For Pattern 2 deployments (cross-org, no shared AS), OBO instance
binding is sufficient. For Pattern 1 deployments (shared AS, enterprise
registry), both OBO and external runtime authorization may coexist.

## Action Class Guidance

| Action Class | Instance Binding | Rationale |
|-------------|-----------------|-----------|
| A (read-only) | Optional | Low risk, class-level binding sufficient |
| B (reversible write) | Recommended | Reversibility reduces exposure |
| C (regulated write) | Required | Irreversible, regulatory record |
| D (sovereign) | Required | Identity-bound, highest assurance |

## Consequences

- `agent_instance_id` and `agent_instance_pubkey` added as optional
  fields to `schemas/obo-credential.json`.
- `instance_binding_required` added as optional field to
  `schemas/obo-governance-pack.json`.
- Presentation verification protocol documented in §3 of the RFC.
- SHACL shape for credential updated to validate
  `agent_instance_pubkey` format when present.
- External runtime authorization schemes (OATR et al.) are composable
  but not required. OBO instance binding subsumes their function for
  cross-org deployments without a shared registry.
- Key rotation: when an agent instance is restarted, a new keypair is
  generated and a new credential must be issued. Short credential
  validity windows are RECOMMENDED for Class C/D instance-bound
  credentials.
