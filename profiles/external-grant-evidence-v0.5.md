# External Grant Evidence Profile

Version: `obo-interop/0.5-alpha.1`.
Repository release: `v0.5.0-alpha.1` (26 October 2026).
Status: experimental, single-hop, offline evidence verification.

Runtime implementation update: repository `v0.5.0-alpha.2` adds a
[real PocketBase receiving-service test](../examples/integrations/pocketbase/)
without changing this alpha.1 wire profile or its archived fixtures. The issuer
and verifier are still maintained in this repository.

The subsequent [Keycloak mandate experiment](keycloak-mandate-v0.5.md) in
`v0.5.0-alpha.3` uses a separate wire profile for a native service-account token
plus explicit mandate. It does not change the claim semantics defined here.

This profile tests whether OBO can preserve an external grant, a receiving
service's policy decision and its execution assertion in one independently
verifiable bundle. Authority remains attributable to people and organizations;
the verifier does not adjudicate lawful delegation or duty of care.

## Compatibility And Scope

The base `draft-01` credential/envelope schemas and legacy `obo verify` command
retain their v0.4 behavior. This profile uses separate schemas and the new
`verify-bundle` command. Its objects are not base OBO Credentials or Evidence
Envelopes. They must not be passed to a base verifier as equivalent objects.

The grant follows a deliberately narrow subset of the
[RFC 9068 JWT access-token profile](https://www.rfc-editor.org/rfc/rfc9068.html),
with a private `obo` claim for exact operation binding. This is not a generic
OAuth adapter or implementation of OAuth issuance, identity chaining, AIP,
AP2, DPoP or SCITT. The fixtures are locally issued test tokens from a separate
issuer role, not a third-party interoperability result. A real issuer would
need to support this private claim or a separately specified binding mechanism.

All cryptographic verification uses PyJWT and cryptography. New structured
digests use [RFC 8785 JCS](https://www.rfc-editor.org/rfc/rfc8785.html) through
the `rfc8785` library. Legacy v0.4 digest encoding is unchanged. Compact signed
JWTs are retained byte-for-byte and hashed over their exact ASCII serialization.

## Wire Objects

Bundle schema: [interop-bundle-v0.5.json](../schemas/interop-bundle-v0.5.json).
Independent trust configuration: [interop-trust-v0.5.json](../schemas/interop-trust-v0.5.json).

| Bundle field | Purpose |
|---|---|
| `profile` | Exact version; unknown versions fail. |
| `operation` | Request identifier, action, resource and all submitted parameters. |
| `grant_jwt` | Original issuer-signed authorization token. |
| `policy_jwt` | Policy-authority-signed policy snapshot. |
| `decision_jwt` | Receiving-service-signed allow/deny receipt binding the grant, policy and operation. |
| `execution_jwt` | Service-signed result assertion binding the decision, operation and response. Required after allow; forbidden after deny. |
| `response` | Structured service response committed to by the execution receipt. |

Bundled JWT headers contain exactly `alg`, `typ`, and `kid`. This experiment
pins `EdDSA` with Ed25519 keys. It rejects alternative algorithms, critical
headers, embedded keys and key-discovery URLs. The verifier makes no network
requests and obtains keys only from its independently trusted configuration.

Every JWT requires nonempty `iss`, `sub`, string `aud`, `jti`, and integer
`iat`/`exp` with `iat < exp`. Header `kid`, issuer and audience must match the
role's trusted configuration. Duplicate JSON members, unsupported claims and
noncanonical base64url segments fail. The allowed additional claims are closed:

| JWT type | Additional claims |
|---|---|
| `at+jwt` | `client_id`, `scope`, `obo` |
| `obo-policy+jwt` | `profile`, `action`, `resource`, `allowed_fields`, `scope` |
| `obo-decision+jwt` | `profile`, `grant_digest`, `policy_digest`, `operation_digest`, `request_id`, `client_id`, `operator_id`, `outcome`, `reason_code` |
| `obo-execution+jwt` | `profile`, `decision_digest`, `operation_digest`, `response_digest`, `request_id`, `outcome` |

The grant's `obo` object contains exactly `profile`, `operator_id` and
`operation_digest`. `sub` is the expected originating principal; `client_id`
is the acting workload. The verifier independently pins both and the operator,
audience and scope. These identifiers are accepted assertions under supplied
trust policy, not legal-entity identity proofing.

The policy's subject is the operator. The decision and execution subjects are
the originating principal. Service signatures identify the receiving service.
Delegation, confirmation (`cnf`), `nbf` and rich authorization details are
unsupported in this revision and rejected rather than discarded.

## Operation And Policy Evaluation

The first workflow is a supplier-record update. `operation.action` is
`supplier.update`, and the only supported token scope is `supplier:update`.
The grant commits to the whole operation, including its request identifier.
Changing the target or any parameter invalidates that commitment.

The local policy checks exact action, scope and resource equality, then requires
all submitted parameter names to belong to `allowed_fields`. This is a field
allowlist example; it is not a general policy language or value-validation
engine. The service's actual API must validate parameter types and values.
Unknown policy constraints fail instead of being silently ignored.

The verifier recomputes the decision. The signed outcome and reason must be
`allow` / `policy.allow` or `deny` / `policy.deny` accordingly. Acceptance must
have a linked execution receipt with outcome `completed` or `failed`; refusal
must have no execution receipt or response. A verified refusal is a valid
evidence result, not permission to execute.

## Historical Verification And Trust

`--at` supplies the historical decision time independently of the bundle. The
decision's `iat` must equal it; grant and policy validity must include it.
Execution must occur no earlier than that decision and before grant, policy and
decision expiry. Receipt times are signed assertions, not trusted timestamps.
The caller must establish why this reference time and these historical keys
are trustworthy. A caller-chosen time cannot establish that execution really
preceded a revocation.

The trust file supplies keys separately for issuer, policy authority and service,
plus expected principal, agent, operator, audience and scope. Do not accept a
trust file merely because the bundle producer supplied it. Demo files deliberately
contain publicly known test keys; they confer no real authority.

An optional, independently trusted `status` snapshot contains `as_of`,
`valid_until` and `revoked_grant_ids` for the configured issuer. It must cover
the decision and execution times. A listed grant is rejected; stale/future status is rejected;
missing status is reported as unknown. This is supplied archival evidence,
not a standard status-list protocol, live revocation lookup or assurance of
the current status of any key. Key acceptance is the trust-file owner's decision.

| CLI exit | Result | Meaning |
|---|---|---|
| 0 | `verified` | Supported signatures, bindings, policy decision, receipts and supplied historical grant status verified. |
| 1 | `failed` | Malformed, unsupported, tampered, contradictory or rejected evidence/trust inputs. |
| 2 | `incomplete` | Supported checks pass but historical grant status was not supplied. |

Every successful/incomplete report preserves limitations: no legal adjudication,
proof of possession, live replay control, independent timestamp, or proof that
the service's execution assertion is true or complete. The report checks
statements, not the physical supplier database. Refusals also require a valid
grant in this profile; recording malformed or expired-grant refusals is future work.

Supplying several bundles checks duplicate `(issuer, grant jti)` and request IDs
within that set. This is an offline consistency check, not a durable replay store.
No caller-supplied bundle can establish that other omitted requests do not exist.

## Evidence Needed Before Further Release

The next step is a second, independently maintained issuer or verifier running
the same accepted, denied and adversarial cases. The alpha does not certify
interoperability. Additional grant formats must have explicit, versioned claim
and constraint semantics; no automatic lossy translation is permitted.

Delegation-chain verification, real proof of possession, durable replay state,
key-history/status distribution, evidence retrieval and SCITT representation
remain separate experiments. Stable `v0.4.18` remains available unchanged.
