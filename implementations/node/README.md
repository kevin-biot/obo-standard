# Separate Node Verifier

Repository/package release: `v0.5.0-alpha.4`.
Supported wire profile: **`obo-keycloak/0.5-alpha.3` only**, unchanged.
Requires Node.js 22 or later. This private package is not published to npm.

This verifier does not import, wrap, shell out to, or communicate with the Python
verifier. It uses [jose](https://github.com/panva/jose) for compact JWS signatures,
[Ajv](https://ajv.js.org/json-schema.html) for the public JSON Schemas,
[canonicalize](https://github.com/erdtman/canonicalize) for RFC 8785 JCS and
[jsonc-parser](https://github.com/microsoft/node-jsonc-parser) to detect duplicate
members and preserve numeric-lexeme checks. Comments and trailing commas are
disabled; native `JSON.parse` also checks the input grammar. The npm lockfile
pins direct/transitive packages and integrity hashes; no install scripts run.

It is a **second implementation maintained by this project**, not an external
maintainer, security audit, clean-room implementation or third-party endorsement.
It shares the published schemas and public test inputs, not verification logic.

## Run

From the repository root:

```bash
npm ci --prefix implementations/node --ignore-scripts --no-fund --no-audit
npm test --prefix implementations/node
node implementations/node/verify.mjs --version
node implementations/node/verify.mjs /path/to/bundle.json \
  --trust /path/to/independently-trusted-config.json --at 1793016000
```

Use the actual independently established historical decision time, not the
example number. No network access, issuer lookup or Python environment is
needed to verify a bundle after npm installation. Trust is supplied separately;
never accept it merely because the bundle producer provided it.

| Exit | Result | Meaning |
|---|---|---|
| 0 | `verified` | All supported evidence checks and supplied status passed; may include a refusal or failed execution. |
| 1 | `failed` | Invalid, unsupported, contradictory or rejected input. |
| 2 | `incomplete` | Supported checks passed, but historical status was absent. |

Several positional bundle paths check duplicate request IDs and `(issuer, grant
jti)` within that supplied set, not across an unseen fleet or persistent store.

The verifier checks pinned issuer/role keys, original token bytes, exact claim
sets, principal/workload/operator separation, mandate and operation commitments,
historical validity, policy evaluation, decisions, receipts and response digests.
It does not accept alpha.1 bundles, base v0.4 credentials, new claims, other
algorithms or multi-audience tokens by dropping fields or translating formats.
JWT `iat`/`exp` must use integer JSON lexemes, not `1.0`/`1e0`. The parser also
rejects unsafe integer lexemes anywhere before JavaScript could round them;
this is intentionally stricter than Python for otherwise unused metadata.
JCS supports valid IEEE-754 fractional/exponent values in operation/response
data and rejects nonfinite numbers and lone Unicode surrogates.

## Shared And Live Checks

The checked-in [corpus](../../tests/vectors/keycloak/) has explicit expected
results and retains each bundle/trust input as a JSON string. This lets every
implementation consume the same original bytes, including malformed JSON and
signed duplicate-member inputs. Both languages must pass their own tests;
neither implementation's output is used as the expected verdict for the other.

The corpus is synthetic. It includes JCS edge cases that test structured data,
not realistic supplier email values. The intentionally public TEST-ONLY keys
must never be used to establish real authority.

CI also enables `OBO_NODE_VERIFY=1` in the
[live Keycloak/PocketBase harness](../../examples/integrations/keycloak/).
Python and a separate Node CLI process check the exact completed, denied and
failed bundles; their supported checks/outcomes must agree. Node also rejects
an incorrect pinned workload subject. Public runtime artifacts contain separate
Node reports beside the original bundles and Python reports.

## Remaining Limits

Matching results are implementation evidence, not proof that the profile or
both implementations have no shared design errors. There is no holder binding,
live Keycloak introspection, mandate revocation, key-history distribution,
trusted timestamp, multi-hop attenuation or complete audit coverage.
Signed execution receipts remain service assertions. The verifier does not
determine legal authority, legal capacity, duty of care or the validity of the
principal's decision to delegate. See the
[profile](../../profiles/keycloak-mandate-v0.5.md) for the full authority boundary.

The next independent gate is a verifier maintained outside this repository
running these public inputs and separately chosen adversarial cases.
