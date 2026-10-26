# External Grant Evidence Experiment

Release: `v0.5.0-alpha.1`. Profile: `obo-interop/0.5-alpha.1`.

A buyer's procurement workload asks a different organization's service to
update a supplier record. The issuer grants the exact operation. The receiving
service applies its own signed policy and signs its decision and result.
`demo.py` simulates that service with an isolated in-memory supplier record;
there is no network service or real supplier system behind these fixtures.

Two deterministic fixtures are included:

- `accepted.json`: a contact-email update is allowed and execution is asserted.
- `denied.json`: a credit-limit change is outside the receiving service's policy
  and is refused without execution evidence.

All private seeds used by `demo.py` are intentionally public TEST keys. These
are reproducible test statements, not real permissions or a live API deployment.
`trust.json` is trusted only for this fixture exercise. In real use the verifier
must obtain trust configuration and historical status independently.

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python examples/integrations/external-grant/demo.py --check
./obo --version
./obo verify-bundle examples/integrations/external-grant/accepted.json \
  --trust examples/integrations/external-grant/trust.json --at 1793016000
./obo verify-bundle examples/integrations/external-grant/denied.json \
  --trust examples/integrations/external-grant/trust.json --at 1793016000
python -m unittest discover -s tests -v
```

The fixed reference time is 26 October 2026, 12:00 UTC. Verification intentionally
uses that historical context rather than the workstation's current clock.
After acceptance the report says `completed`; after refusal it says `denied`.
Both return 0 when the supported evidence checks pass. Missing status returns 2,
and failed verification returns 1. No live request is authorized by these results.

Run `demo.py` without `--check` to regenerate the fixtures. Repeated generation
must produce byte-identical JSON. The generator and verifier use separate
modules, but share cryptographic dependencies; this is not an independently
implemented interoperability result.

The regression suite publishes negative cases for changed parameters/resources,
principal/agent/operator/audience substitution, scope widening, unknown claims
and policies, forged signatures, wrong signing roles, duplicate members, missing
or spliced receipts, inconsistent decisions, changed responses, execution after
expiry, stale/revoked/missing status and duplicates within a supplied bundle set.

See the [profile](../../../profiles/external-grant-evidence-v0.5.md) for exact
semantics and limitations. In particular, original signed grant bytes are
preserved and referenced, not converted into a supposedly equivalent OBO grant.
