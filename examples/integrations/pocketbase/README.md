# PocketBase Receiving Service

Repository release: `v0.5.0-alpha.2`.
Wire profile retained: `obo-interop/0.5-alpha.1`.
Pinned third-party service: PocketBase `v0.40.6` (MIT).

This integration replaces the in-memory supplier store with an unmodified
PocketBase process, its authenticated HTTP record API, and its persistent SQLite
database. OBO verification runs in a separate gateway before the API write.
PocketBase is not modified to understand OBO and this is not a vendor endorsement.

## Selection

PocketBase provides a small independently maintained receiving service that can
be reproduced locally and in CI. Its native collection rules, field validation,
authenticated PATCH API and persistent storage let us test enforcement and real
effects separately from OBO's signed assertions. It is a generic record backend,
not an ERP or procurement system; the test provisions a supplier collection.
ERPNext is a possible later business-system integration but requires a larger
deployment and application-specific record model.

Primary references:

- [Official v0.40.6 release](https://github.com/pocketbase/pocketbase/releases/tag/v0.40.6)
- [Record update API](https://pocketbase.io/docs/api-records/)
- [Collection configuration](https://pocketbase.io/docs/api-collections/)
- [Native API rules](https://pocketbase.io/docs/api-rules-and-filters/)

`download.py` pins the official release archive SHA-256 values published with
the release metadata for macOS arm64 and Linux amd64. It verifies the archive
before extracting only the binary and license. Other platforms fail explicitly.
Downloaded binaries are local dependencies, not vendored source or release files.

## Flow

```text
Test issuer signs the exact supplier update
    -> OBO gateway verifies grant, signed policy, identity and current status
    -> durable SQLite request/grant reservation
    -> restricted PocketBase account performs authenticated PATCH
    -> gateway reads back the record through PocketBase's API
    -> signed execution receipt and durable cached evidence
    -> separate CLI process verifies the exported evidence offline
```

The test issuer and policy authority remain part of our harness. This exercises
a real third-party receiving service, not an independent OAuth issuer or an
independently implemented OBO verifier. PocketBase's native token is used only
between the gateway and PocketBase; it is not relabelled as an OBO grant.

## Run

From the repository root, using the project's Python environment:

```bash
python -m pip install -r requirements-dev.txt
python examples/integrations/pocketbase/download.py --output-dir /tmp/obo-pocketbase
POCKETBASE_BINARY=/tmp/obo-pocketbase/pocketbase \
  OBO_POCKETBASE_RESULTS=/tmp/obo-pocketbase-evidence \
  python -m unittest discover -s tests -p test_pocketbase_live.py -v
```

The harness selects free loopback ports, provisions an isolated database and
service account, generates fresh test signing keys, starts the backend and
gateway, exercises the integration, and stops both processes. Private keys and
backend credentials remain in a mode-0700 temporary directory; they are not
exported. The database is removed after the tests. Restart tests reuse the same
on-disk database and ledger before cleanup.

Without `POCKETBASE_BINARY`, the live tests are explicitly skipped. CI has a
separate mandatory step which downloads the pinned Linux binary and runs them.
`OBO_POCKETBASE_RESULTS` optionally retains public trust inputs, signed test
bundles and reports for the completed, denied and failed cases. These are test
artifacts. CI retains them for seven days; no real credentials are uploaded.

## Tested Behavior

| Case | Observed requirement |
|---|---|
| Allowed contact-email update | Native API readback matches submitted data. |
| PocketBase restart | Updated record persists in SQLite. |
| Gateway restart and identical retry | Original signed receipt returned; no second PATCH. |
| Credit-limit change | Gateway returns signed policy refusal; record unchanged. |
| Invalid email value | PocketBase rejects it; gateway emits a signed failed execution record; record unchanged. |
| Tampered parameters or forged grant | Rejected before dispatch; record unchanged. |
| Grant identifier reused for another request | Rejected as conflict; record unchanged. |
| Unauthenticated direct PATCH | PocketBase refuses it independently of the gateway. |
| Direct credit-limit PATCH with gateway's native account | PocketBase's own collection rule refuses it. |
| Reserved but unfinished request | No automatic redispatch. |
| Backend outage | Indeterminate state is retained; retry requires reconciliation. |
| PATCH succeeded but readback fails | Fault-injection test ensures the gateway does not misreport a definite failed execution. |

## Boundaries And Recovery

The runtime reservation is separate from the offline bundle's duplicate-set
check. It atomically reserves both request ID and `(issuer, grant jti)` before
dispatch. Identical completed requests return the existing result while the
grant/status remain valid. Reuse with different content, in-flight requests,
and uncertain outcomes return a conflict. Refused operations are also retained.

PocketBase and the gateway ledger are separate transactions. There is no claim
of distributed exactly-once execution. A crash or timeout after a write but
before evidence is committed can leave an unresolved reservation. The gateway
does not guess whether the update happened and does not automatically retry.
It returns an error without a final verifiable execution bundle; an operator
must reconcile the record and ledger. The alpha.1 wire profile has no
`indeterminate` execution outcome, so it is not silently extended here.

This local setup trusts its host and administrators. PocketBase is loopback-only,
and the restricted native token stays in the gateway's configuration. A party
that steals that token can bypass the gateway for operations the native rules
allow. Production deployment needs an enforced backend access boundary,
protected credentials, TLS, rate limits and an appropriate server deployment.
The Flask development server here is solely a loopback test harness.

The service signing key is checked against its configured public key at startup.
Trust, policy and status are pinned configuration loaded at startup; status is
not fetched from an independent issuer or refreshed during a run. Expired,
revoked, malformed or unsupported grants fail admission. Those early errors and
replay/indeterminate errors currently have no signed refusal bundle. Policy
refusals under a valid grant do. No claim of a complete audit log is made.

Real readback and restart checks strengthen the experiment, but a signature
still attributes a service assertion; it does not prove legal authority, lawful
delegation, duty of care, or independently attested physical execution. The
existing profile's limitations remain in every offline verification report.
