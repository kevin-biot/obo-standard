# Independent Keycloak Issuer

Release `v0.5.0-alpha.3`. Profile `obo-keycloak/0.5-alpha.3`.

Repository `v0.5.0-alpha.4` adds a [separate Node verifier](../../../../implementations/node/)
for this unchanged profile. It is maintained in the same project, not by an
independent third party.

This experiment joins an unmodified Keycloak issuer to the real
[PocketBase receiving service](../pocketbase/) through an OBO admission gateway.
It selects a working integration rather than requiring every other project to
adopt OBO's credential format.

## Why Keycloak

Keycloak has a reproducible local container, native OAuth service accounts,
administrative provisioning and signed JWT access tokens with published public
keys. Version 26.8.1 is pinned by digest in
[the test harness](../../../../tests/keycloak_support.py). No custom Keycloak
provider or OBO token mapper is installed. The configured audience and scope
are standard client configuration. This is not a Keycloak endorsement.

Primary references, reviewed 26 October 2026:

- [Official Keycloak 26.8.1 release](https://www.keycloak.org/2026/10/keycloak-2681-released)
- [Official container guide](https://www.keycloak.org/server/containers)
- [Service accounts](https://www.keycloak.org/docs/latest/server_admin/index.html#_service_accounts)
- [OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers)

## Flow

```text
Keycloak signs a native RS256 service-account token
    -> configured mandate authority signs principal + workload + exact operation + token digest
    -> gateway verifies both documents and signed service policy
    -> durable request/grant reservation
    -> native PocketBase PATCH and independent API readback
    -> signed decision and execution receipts
    -> separate CLI process checks the retained evidence offline
```

The Keycloak subject is the machine account, **not** the legal principal.
The mandate authority and policy authority are still test-harness roles.
Automatically creating a test mandate does not demonstrate human consent or
the legal validity of a delegation. See the exact
[profile and limitations](../../../../profiles/keycloak-mandate-v0.5.md).

## Run

Requires Python, Docker and a supported PocketBase download platform. From the
repository root:

```bash
python -m pip install -r requirements-dev.txt
npm ci --prefix implementations/node --ignore-scripts --no-fund --no-audit
python examples/integrations/pocketbase/download.py --output-dir /tmp/obo-pocketbase
OBO_KEYCLOAK_LIVE=1 \
  OBO_NODE_VERIFY=1 \
  POCKETBASE_BINARY=/tmp/obo-pocketbase/pocketbase \
  OBO_KEYCLOAK_RESULTS=/tmp/obo-keycloak-evidence \
  python -m unittest discover -s tests -p test_keycloak_live.py -v
```

The harness pulls/runs the digest-pinned Keycloak image, provisions an isolated
realm/client/service account and captures its public key and administrative
subject mapping. It starts loopback PocketBase/gateway processes with random
test credentials. Tests clean up the dedicated container, processes and private
temporary directory; they do not change other Docker containers.
Startup can take a few minutes on the first image download. Neither development
HTTP nor this administrative provisioning flow is a production deployment.

Without both opt-in environment variables, live tests skip. CI explicitly
enables them in a mandatory step. Offline adversarial adapter tests always run.

Exported results contain the original **test bearer tokens**, mandates, public
trust inputs and signed bundles/reports for completed, denied and failed cases.
No private signing keys, Keycloak administrator/client secrets or PocketBase
credentials are exported. Treat these as disposable test credentials, never
production examples; their isolated issuer/services are deleted after testing.
CI retains these artifacts for seven days. Results verify historically after
token expiry using the signed decision time as a supplied test reference:

```bash
AT=$(python -c 'import json, jwt; b=json.load(open("/tmp/obo-keycloak-evidence/completed.json")); print(jwt.decode(b["decision_jwt"], options={"verify_signature":False})["iat"])')
./obo verify-bundle /tmp/obo-keycloak-evidence/completed.json \
  --trust /tmp/obo-keycloak-evidence/trust.json --at "$AT"
```

This extracts a reference time for reproducing a test, not independent proof
that a service actually executed before revocation. Real verification must
establish reference-time and historical trust independently.

`OBO_NODE_VERIFY=1` requires Node.js 22+ and the installed Node dependencies.
The harness additionally verifies the same live bundles in a Node CLI process
and exports `*-node-report.json`. Without this flag the original Python-only
harness remains available. CI requires both verifiers.

## Acceptance Gates

Tests exercise real native tokens and writes, restarts/persistence, identical
retries, policy refusals, backend validation failures, native backend controls,
reused grants and uncertain outcomes. They additionally reject missing mandates,
swapped valid tokens and incorrect pinned workload subjects. Forged signatures
and changed operation parameters must not write.

This demonstrates one configured issuer/receiver path, not generic Keycloak
compatibility, cross-organization trust negotiation, independently written OBO
verification, multi-hop delegation, live issuer revocation, or proof of possession.
PocketBase still does not understand OBO itself. Its native token holders can
bypass the gateway within native permissions; production requires an enforced
backend/credential boundary. Remaining work is explicit in the profile.
