# Current Status

Reviewed: 26 October 2026. Status: working draft and limited reference implementation.

The draft's original front matter gives an expiry of 4 October 2026. Repository
maintenance does not renew that submission or establish IETF adoption.

Stable reference: `v0.4.18`. The first interoperability experiment is released
separately as `v0.5.0-alpha.1`, profile `obo-interop/0.5-alpha.1`. It tests a narrow
JWT grant with an OBO private operation-binding claim and signed policy/receipts.
It does not select a replacement protocol or demonstrate third-party deployment.
See the [profile](../profiles/external-grant-evidence-v0.5.md) and
[reproducible example](../examples/integrations/external-grant/).
Release `v0.5.0-alpha.2` adds a real
[PocketBase receiving-service integration](../examples/integrations/pocketbase/)
using the same alpha.1 wire profile. Native persistence, readback, restart and
idempotency are exercised. Its original issuer and evidence verifier are our code.
Release `v0.5.0-alpha.3` adds a separately versioned
[Keycloak integration](../examples/integrations/keycloak/). Unmodified Keycloak
26.8.1 issues the original RS256 workload token. A separate signed mandate
binds the principal's declared delegation to that token and the exact operation.
The mandate authority and OBO verifier remain our harness/code; this is not
generic OAuth interoperability or proof of lawful delegation.
Release `v0.5.0-alpha.4` adds a [separate Node verifier](../implementations/node/)
for the unchanged alpha.3 wire profile. It uses a different JOSE/JCS/schema
stack and agrees on shared synthetic cases and live receiving-service evidence.
It is still maintained in this repository, not independent third-party validation.

## Implementation Coverage

| Surface | Available | Boundary |
|---|---|---|
| JSON Schemas | Credential and envelope structure, including draft delegation metadata | Structure is not signature verification, scope attenuation, or evidence of consent. |
| `obo verify` | Schema, digest, required signature verification, issuance/expiry checks, optional comparison with an intent phrase | No authorization decision, chain traversal, revocation, replay store, binding-proof validation, or instance presentation verification. Chain and instance-proof fields cause rejection. |
| Key lookup | Explicit trusted issuer key, or operator-domain DNS TXT | DNS mode requires issuer and operator equality. No DNSSEC validation or legal-entity identity proof. Key trust is a deployment responsibility. |
| A2A example | Single-hop credential checks and allow/deny evidence flow | Demo enforcement and stub anchor receipts; not a general production verifier. |
| Delegation chains | Draft requirements and credential metadata in the schema | CLI verification is not implemented. The multi-hop Sentinel experiment explicitly strips OBO and is not a delegation conformance demo. |
| Base evidence examples | JSON Schema validation | Placeholder digests/signatures illustrate shape; the signed credential demo and experimental grant bundles are cryptographic test fixtures. |
| Experimental `verify-bundle` | Original signed grant, JCS operation commitments, signed policy/decision/execution records, supplied historical grant status | Separate versioned profile; test fixtures only. Missing status is incomplete. No generic OAuth adapter, delegation, live authorization or independent timestamp proof. |
| PocketBase live integration | Gateway admission, real authenticated PATCH/readback, persisted reservations and restart tests against PocketBase v0.40.6 | Local trusted-host harness; backend token holders/admins can bypass OBO within native permissions. Uncertain writes require reconciliation; no distributed exactly-once claim. |
| Keycloak live integration | Actual client-credentials token, pinned RSA key and service-account subject, separate operation-bound mandate, signed decision/execution evidence | One Keycloak 26.8.1 configuration. No token exchange, live introspection, mandate revocation, externally maintained OBO verifier, or proof of possession. |
| Separate Node verifier | Original Keycloak-profile tokens, pinned trust, JCS bindings, policy and receipt checks; shared corpus and live evidence checked by both implementations | Same project maintainership, not independent third-party assurance. Keycloak alpha.3 only; no live issuer status or holder binding. |

The schema cannot compare `delegation_depth.current` with `max` or validate
parent/child authority. A chain verifier must enforce depth, expiry, principal
continuity, signatures, attenuation and applicable revocation rules. Supporting
the field names in JSON does not imply those checks exist.

`intent_hash` commits to the exact UTF-8 bytes supplied. It does not establish
that an operation implements that intent. The reference JSON digest encoding is
Python sorted-key compact JSON, not a claim of RFC 8785 JCS interoperability.
Independent implementations need an agreed byte encoding and test vectors.
The v0.5 experiment explicitly uses RFC 8785 JCS for structured digests, with
PyJWT for compact JWS verification, without changing legacy v0.4 encoding.

Signatures attribute statements to keys. A signed envelope alone does not prove
that an action occurred, that observations are complete, or that the issuer had
lawful authority. Those questions require independently assessed evidence and
deployment trust policy. OBO's accountability premise remains that workloads
exercise authority traceable to accountable people and organizations.

## External Work

These are dated scope comparisons, not interoperability or deployment claims.
Working-group adoption and publication do not demonstrate that every mechanism
is implemented or sufficient for a particular use case.

| Work reviewed | Status observed | Relevance and questions to assess |
|---|---|---|
| [AIMS](https://datatracker.ietf.org/doc/draft-ietf-wimse-aims/), `draft-ietf-wimse-aims-00` | WIMSE working-group draft, September 2026 | Agents as workloads, authorization and reconstructable audit context. Assess how policy decisions become portable dispute evidence. |
| [OAuth Identity Chaining](https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-chaining/), `-17` | RFC Editor queue at review | Authorization across separate trust domains. Requires appropriate issuer trust; a shared authorization server is not necessary. Assess fit for first-contact counterparties and durable evidence. |
| [Agent Delegation Chain](https://datatracker.ietf.org/doc/draft-asor-wimse-agent-delegation-chain/), `-02` | Individual Internet-Draft, October 2026 | Offline chain verification and attenuation. Assess holder binding, status checking, aggregate budgets and implementation coverage. |
| [AIP](https://datatracker.ietf.org/doc/draft-prakash-aip/), `-02` | Individual Internet-Draft, October 2026 | Delegation where no authorization server is on the path. Its implementation-status section discloses remaining checks; signed action outcomes are future work. |
| [AP2](https://ap2-protocol.org/ap2/specification/), v0.2 | Published protocol specification | Checkout/payment mandates, receipts, autonomous flows and dispute evidence. Agent-to-agent delegation is outside this version's scope. Assess generalization beyond payments. |
| [Agent Execution Evidence](https://datatracker.ietf.org/doc/draft-thaha-scitt-agent-execution-evidence/), `-00` | Individual Internet-Draft, October 2026 | SCITT statements, linked execution records, responsible entities and offline bundles. Assess operational burden, evidence completeness and trust assumptions. |
| [AuthZEN AARP and COAZ](https://openid.net/openid-foundation-advances-authorization-for-the-agent-era-with-new-authzen-working-group-drafts/) | Announced as working-group drafts, June 2026 | Authorization prerequisites and MCP authorization mappings. Assess how approval and policy records survive across operators. |

Individual Internet-Drafts are proposals, not IETF-endorsed standards. The April
AI identity paper and earlier composition notes remain historical analysis; they
should not be read as the current status of the entire standards landscape.

## Maintenance Checks

Install `requirements-dev.txt`, then run example validation and the unittest
suite as documented in the README. Missing `jsonschema` now fails explicitly.
Schema checks cover all JSON example files; capture artifacts have their own
structural checks. They do not certify production security or legal compliance.

Live DNS fixture checks and Docker demos exercise external infrastructure and
are separate from the deterministic local checks. A previous successful run is
not a current availability guarantee.
