# Public Keycloak-Profile Vectors

Suite: `obo-keycloak-vectors/0.5-alpha.4`.
Wire profile: `obo-keycloak/0.5-alpha.3`.

**TEST DATA ONLY.** The RSA private key in `TEST-ONLY-RSA.pem` was generated for
this public corpus. It and the fixed Ed25519 test seeds are intentionally
public and confer no real identity, authority or confidentiality. No production
key, Keycloak client secret or backend credential is present here.

`corpus.json` contains 71 named cases. Each includes `at`, `bundle_json`,
`trust_json` and explicit expected `result` and, when applicable, `outcome`.
The JSON strings retain the original inputs, including duplicate JSON members;
do not parse and reserialize them before feeding your verifier. Expectations
are declared in the generator, not learned from either verifier's verdicts.

Coverage includes completed/failed execution, valid refusal, unknown status,
identity/key/audience substitution, unsupported constraints, missing or spliced
receipts, revoked/stale status, signed duplicate members and decimal/exponent
timestamp encodings. A structured-data case checks Unicode UTF-16 key ordering,
escaping, floating-point JCS formatting and prototype-like member names. It is
not a realistic supplier-update payload or evidence of a real issuer execution.

From the repository root:

```bash
python scripts/keycloak_vectors.py --check
python -m unittest discover -s tests -p test_keycloak_vectors.py -v
npm ci --prefix implementations/node --ignore-scripts --no-fund --no-audit
npm test --prefix implementations/node
```

Regenerate intentionally with `python scripts/keycloak_vectors.py`. Generation
uses the test fixture/signing helpers, not either verifier as an expected-result
oracle. The fixed test key makes the corpus byte-reproducible. Keep released
suite snapshots immutable by citing the repository tag; future changes require
a new repository release and explicit suite version.

This corpus is a compatibility baseline, not a complete security certification.
External implementations should add independently selected adversarial cases.
