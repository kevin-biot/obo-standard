# Keycloak Workload And Explicit Mandate

Profile: `obo-keycloak/0.5-alpha.3`.
Repository release: `v0.5.0-alpha.3`, 26 October 2026.
Status: experimental, one configured client-credentials flow, single hop.

## Authority Boundary

The independently maintained issuer is Keycloak 26.8.1. Its native token proves
that a configured service account obtained a scoped access token. The service
account is not the accountable human or organization. The decision to delegate
is represented by a **separate signed mandate** from an independently configured
authority key, not inferred from a client ID or a service-account token.

This preserves OBO's premise: accountable people and organizations delegate to
workloads. The machinery verifies attributable statements, bounded authority
and evidence; it does not decide lawful authority, legal capacity or duty of
care. Those judgments remain outside the workload and this verifier. The
test harness signs mandates automatically to exercise the protocol, not to
demonstrate a real business approval or an independent mandate issuer.

## Wire Objects And Trust

Schemas: [bundle](../schemas/keycloak-bundle-v0.5.json) and
[trust configuration](../schemas/keycloak-trust-v0.5.json).

The bundle contains `profile`, `operation`, `grant_jwt`, **`delegation_jwt`**,
`policy_jwt`, `decision_jwt` and, after allow, `execution_jwt` and `response`.
It is not a base OBO Credential or Evidence Envelope, nor an alpha.1 bundle.
Unknown profiles and fields fail. There is no fallback or lossy translation.

Trust is supplied out of band. `workload_issuer` pins Keycloak's exact issuer
and one public RSA JWK (`kty`, `kid`, `alg`, `use`, `n`, `e`). `issuer` is the
mandate authority, not Keycloak. `policy_authority` and `service` each have
separately pinned Ed25519 keys. `expected` pins principal, client ID (`agent_id`),
Keycloak service-account UUID (`workload_subject`), operator, audience and scope.
The live harness obtains that UUID from Keycloak's administrative service-account
API, not by trusting the presented token's unverified claims.

The original compact token is retained byte-for-byte. Token digests hash those
ASCII bytes. Structured digests use RFC 8785 JCS, as in alpha.1. JOSE headers
contain exactly `alg`, `typ`, `kid`; embedded/discovered keys, critical headers,
duplicate JSON members and noncanonical base64url encodings are rejected.

## Claim Rules

### Native Workload Grant

Only RS256 with an RSA key of at least 2048 bits and JOSE `typ: JWT` is accepted.
Required claims are `iss`, `sub`, `aud`, `iat`, `exp`, `jti`, `typ`, `azp`,
`scope` and `client_id`. Only `clientHost` and `clientAddress` may additionally
appear; these are issuer metadata, not identity/authority proof.

- `iss` and `kid` match the pinned issuer/key; `aud` is exactly the configured
  single audience string, not a multi-audience list.
- `sub` is the pinned service-account UUID, not the legal principal.
- `azp` and `client_id` both equal the expected workload client ID.
- Payload `typ` is `Bearer`; scope is exactly `supplier:update`.
- Integer `iat`/`exp` are nonnegative safe integers; `iat <= at < exp`.
- Other claims, including `act`, `cnf`, `nbf`, role maps and rich authorization
  details, are unsupported and rejected rather than stripped.

This intentionally excludes most other Keycloak configurations. It is not a
generic JWT/OIDC validator or an RFC 9068 token relabelling exercise.

### Explicit Mandate

The Ed25519 mandate has JOSE `typ: obo-delegation+jwt`. It requires the common
claims `iss`, `sub`, `aud`, `iat`, `exp`, `jti` and exactly these additional claims:

| Claim | Required interpretation |
|---|---|
| `profile` | This exact profile identifier. |
| `sub` | Independently expected originating principal. |
| `workload_subject` | Exact authenticated Keycloak service-account subject. |
| `client_id` | Exact authenticated and expected client ID. |
| `operator_id` | Independently expected operator. |
| `scope` | Same supported scope as the native token. |
| `grant_digest` | Digest of the original native token bytes. |
| `operation_digest` | JCS digest of the entire operation, including request ID. |

The mandate issuer/audience/key must match trust. Its validity is contained
within the grant: `grant.iat <= mandate.iat <= at < mandate.exp <= grant.exp`.
The signed mandate is the cryptographic relationship declaration; possession
alone is not proof of legal authority or proof of possession of a workload key.

### Policy And Receipts

Policy/decision/execution claim sets and field-allowlist evaluation are those
of the [external-grant experiment](external-grant-evidence-v0.5.md), except
that their `profile` is this profile and **the decision additionally requires
`delegation_digest`**, binding the exact mandate bytes. Decision and execution
subjects name the principal from the mandate, never the native service-account
subject. All original tokens remain in the evidence bundle.

The execution window is bounded by the mandate, workload grant, policy and
decision. An allow requires a bound execution receipt and response; a policy
denial forbids them. Backend uncertainty yields no final execution assertion
and no automatic retry. Native validation failures produce a signed `failed`
execution; they are not successful updates.

## Status And Unresolved Work

The optional `status` snapshot refers only to Keycloak `(issuer, grant jti)`
under the configured issuer. The harness creates this **local test snapshot**;
it does not obtain live revocation state from Keycloak. Missing status returns
`incomplete` (CLI exit 2), contradictory/unsupported evidence returns `failed`
(exit 1), and all supported checks passing returns `verified` (exit 0).
Neither an arbitrary caller-supplied snapshot nor the report establishes
that Keycloak currently accepts the token. Mandate revocation and key-history
distribution are not implemented. Trust/status are loaded at gateway startup.

The gateway reserves request/grant IDs durably before dispatch and returns
cached completed results for identical retries while authorization remains
valid. It does not implement distributed exactly-once execution. The bearer
token and mandate can still be stolen and presented together: there is no DPoP
or other holder binding. No multi-hop attenuation, token exchange, trusted
timestamp, complete audit coverage, independently implemented OBO verifier,
or production authorization service is claimed.

Next evidence needed: a verifier maintained outside this repository, explicit
issuer-status/key lifecycle tests, and a holder-bound transport. These are
separate acceptance gates, not features implied by this experiment.
