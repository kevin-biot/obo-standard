# Standard Family

OBO is one layer in a broader architecture for cross-organisation agentic trust.
Each layer can be adopted independently.

```text
RTGF  -> rationale and regulated "why"
PACT  -> bounded governance pack and execution vocabulary
OBO   -> credential plus evidence for delegated authority
aARP  -> intent routing and corridor admission
Evidence Anchor -> receipt, Merkle root, and settlement evidence
```

## Layer Roles

| Layer | Question | Relationship to OBO |
|---|---|---|
| RTGF | Why was this agent authorised? | Produces the rationale root carried by `why_ref`. |
| PACT | What vocabulary and actions are admissible? | Produces the governed pack referenced by `governance_framework_ref`. |
| OBO | Who is acting, for whom, within what limits, and what happened? | This repository. |
| aARP | Which corridor should this intent use? | May consume OBO credentials and emit route evidence. |
| Evidence Anchor | Can the evidence be independently timestamped and proven later? | Optional anchoring profile for OBO Evidence Envelopes. |

## Independence

The base OBO wire model does not require RTGF, PACT, aARP, or Evidence Anchor.
Those layers are useful when the deployment needs regulated rationale, bounded
policy packs, dynamic routing, or independently anchored receipts.

The minimum OBO implementation is still just:

1. An OBO Credential.
2. An OBO Evidence Envelope.
3. A trust anchor for the operator key, normally DNS.

## Composition With Existing Standards

OBO composes with existing identity, authorisation, and payment work:

| Existing layer | What it does well | Where OBO adds |
|---|---|---|
| OAuth / RFC 8693 | Delegated access where parties share an authorisation server. | Cross-organisation no-shared-AS evidence. |
| WIMSE / SPIFFE | Workload identity inside an organisation. | Portable accountability outside that trust domain. |
| W3C Verifiable Credentials | Portable identity and attribute claims. | Transaction-scoped authority and evidence. |
| A2A protocols | Agent discovery, task routing, and results. | Credential and accountability carried with the task. |
| Payment rails | Settlement and payment network accountability. | Agent delegation evidence before and after settlement. |

The design constraint is simple: use existing infrastructure inside a trust
domain, and use OBO at the boundary where the shared infrastructure stops.
