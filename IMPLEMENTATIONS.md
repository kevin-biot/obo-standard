# Known Implementations

This file tracks known implementations of the OBO specification and
the interlinked standards it connects to.

To register an implementation, open a pull request adding a row to
the relevant table.

---

## Reference Implementation — Lane2 Architecture

The Lane2 reference implementation covers the full five-layer stack.
Every layer is built and running in Go. The specifications in this
family are distillations of what the running code required — not
forward-looking proposals.

| Layer | Standard | Implementation | Language | Status |
|---|---|---|---|---|
| Rationale / governance | RTGF | `rtgf` service — token issuance, DNS root publication, epoch rotation | Go | Running |
| Execution contract | PACT | `ontology` service — pack compilation, SHACL validation, intent mapping, OBT signing | Go | Running |
| Credential + evidence | **OBO** (this standard) | DOP pipeline — Stages 0–8, EvidenceContract, credential issuance, envelope sealing | Go | Running |
| Routing / admission | aARP | `aARP-router` — corridor admission predicates, DNS resolution, route proof per hop | Go | Running |
| Payment settlement | Evidence Anchor | `sapp` service — PSP receipt signing, RRMT/IMT/CORT/PSRT token verification, Merkle anchoring | Go | Running |

The full chain — RTGF rationale → PACT pack → OBO Credential →
aARP corridor admission → OBO Evidence Envelope → Evidence Anchor settlement
receipt — has been exercised end-to-end.

---

## OBO Credential Issuers

| Implementation | Language | Organisation | Profile | Status | Link |
|---|---|---|---|---|---|
| DOP pipeline (Stage 0–3) | Go | Lane2 Architecture | Regulated lane, multi-step, why_ref | Reference | Internal |

## OBO Evidence Envelope Producers

| Implementation | Language | Organisation | Profile | Status | Link |
|---|---|---|---|---|---|
| DOP pipeline (Stage 5–8) | Go | Lane2 Architecture | Regulated lane, why_ref, corridor-bound | Reference | Internal |

## OBO Credential Verifiers

| Implementation | Language | Organisation | Notes | Status | Link |
|---|---|---|---|---|---|
| aARP admission gate | Go | Lane2 Architecture | Verifies credential at corridor entry via DNS key lookup | Reference | Internal |

## DNS Anchoring Deployments

| Sub-profile | Operator | DNSSEC | Status |
|---|---|---|---|
| D.1 `obo-dns-key` | Lane2 Architecture | Planned | Reference deployment |
| D.2 `obo-dns-gov` | Lane2 Architecture | Planned | Reference deployment |
| D.3 `obo-dns-null` (Evidence Anchor nullifier) | Lane2 Architecture | Planned | Reference deployment |

## Corridor Implementations

| Implementation | Organisation | Tiers supported | Status | Link |
|---|---|---|---|---|
| aARP router | Lane2 Architecture | open, regulated, domain-gated | Running | Internal |

## Payment Profile Implementations

| Profile | Implementation | Organisation | Status |
|---|---|---|---|
| payments-mastercard-vi | Evidence Anchor + DOP pipeline | Lane2 Architecture | Running (internal, non-normative) |

---

## Adding your implementation

Open a pull request adding a row to the relevant table above.
Include: implementation name, language, organisation, which OBO
profile(s) it conforms to, and a link if public.

Independent implementations are the path to IETF submission.
See [CONTRIBUTING.md](CONTRIBUTING.md).
