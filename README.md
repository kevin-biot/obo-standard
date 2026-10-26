# OBO - On Behalf Of

Minimum evidence standard for agentic transactions.

**Status:** Working Draft, `draft-obo-agentic-evidence-envelope-01`
**Goal:** implementation feedback, independent implementations, jurisdiction profiles

**Experimental release:** `v0.5.0-alpha.4`; stable reference: `v0.4.18`.
The [external-grant experiment](examples/integrations/external-grant/) adds a
separate operation-bound evidence profile and offline verifier. It preserves
the base credential/envelope formats. A [PocketBase integration](examples/integrations/pocketbase/)
exercises a real receiving service with persisted writes and restart tests.
The [Keycloak integration](examples/integrations/keycloak/) adds an independently
maintained issuer in one explicit service-account configuration, with a separate
signed operation mandate. A [separate Node verifier](implementations/node/)
checks the same profile and shared vectors without the Python implementation.
An externally maintained OBO evidence verifier, generic OAuth
interoperability and multi-hop delegation remain unproven.

**Maintenance review:** 26 October 2026. This repository is a working proposal
with a limited reference verifier, rather than a production authorization service.
Maintenance currently focuses on correctness and reproducibility. Interoperability
options remain under evaluation; see [Current Status](docs/CURRENT-STATUS.md).

## Releases

Repository releases use annotated Git tags such as `v0.4.18`, with changes and
compatibility notes in [CHANGELOG.md](CHANGELOG.md). A tag identifies a fixed
snapshot of the specification, schemas, examples and tools. The `draft-01`
identifier is tracked separately; a repository release does not renew an IETF
submission or change an artifact's wire version automatically. Published tags
are not moved. Use a tagged release when reproducing results or citing this work.

OBO defines the evidence an autonomous agent must carry and produce when it acts
on behalf of a human, organisation, or another machine across organisational
boundaries.

It is not an agent registry, reputation score, wallet, payment rail, or
authorisation server. It is the accountability layer that lets a counterparty
answer:

1. Who are you, and who sent you?
2. What are you authorised to do?
3. What did you actually do?
4. Can I prove all of this later without calling anyone?

## Why This Exists

OAuth, mTLS, WIMSE, SPIFFE, and platform workload identity provide established
building blocks. OAuth also has work for chaining across trust domains. OBO
examines portable transaction authority and evidence in settings with:

- no shared authorisation server
- no prior counterparty relationship
- cross-organisation or cross-border interaction
- agent acting under delegated authority
- post-transaction evidence needed for audit, dispute, or regulation

Example: a travel agent calls an airline, hotel, ticket vendor, car rental
provider, and payment service. None of those organisations has enrolled in the
agent operator's identity system. Each still needs to verify who the agent
represents, what it may do, and what happened afterward.

## The Two Artifacts

OBO is two JSON objects.

| Artifact | Moment | Purpose |
|---|---|---|
| OBO Credential | Before the transaction | Declares principal, agent, operator, bounded intent, action ceiling, governance, expiry, digest, and signature. |
| OBO Evidence Envelope | After the transaction | Records credential used, outcome, reason code, policy snapshot, executed action class, digest, and signature. |

Both artifacts are application-layer objects. They can be carried in A2A task
extensions, HTTP headers, request bodies, payment metadata, or profile-specific
transport fields.

## Canonical Wire Model

The public schemas are the normative JSON shape for this draft:

- [schemas/obo-credential.json](schemas/obo-credential.json)
- [schemas/obo-evidence-envelope.json](schemas/obo-evidence-envelope.json)

Credential highlights:

- `obo_credential_id`
- `principal_id`
- `agent_id`
- `operator_id`
- `binding_proof_ref`
- `intent_namespace`
- `intent_hash`
- `action_classes`
- `governance_framework_ref`
- `issued_at` / `expires_at` as Unix epoch seconds
- `credential_digest`
- `credential_sig`

Evidence envelope highlights:

- `evidence_id`
- `obo_credential_ref`
- `credential_digest_ref`
- `principal_id`
- `agent_id`
- `operator_id`
- `intent_hash`
- `intent_class`
- `action_class`
- `outcome`
- `reason_code`
- `policy_snapshot_ref`
- `governance_framework_ref`
- `sealed_at` as Unix epoch seconds
- `evidence_digest`
- `envelope_sig`

Signatures are Ed25519. Digests are `sha256:<lowercase-hex>`.

## DNS Trust Anchor

OBO uses the operator's DNS namespace as the default public key anchor:

```text
_obo-key.<operator-domain>  TXT  "v=obo1 ed25519=<base64url-public-key>"
```

Any counterparty that can resolve DNS can verify the operator key. No central
OBO registry, approved network, or co-signature service is required.

DNS publishes a key under a domain. Authenticating the lookup, identifying the
legal entity behind that domain, and accepting its authority are separate trust
decisions. The reference CLI does not establish legal identity or validate DNSSEC.

The live demo fixture is:

```bash
dig +short TXT _obo-key.lane2.ai @8.8.8.8
# "v=obo1 ed25519=vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"
```

## Try It

Run the A2A reference demo:

```bash
python3 -m pip install -r requirements-dev.txt
cd examples/integrations/a2a
python3 keygen.py --operator-id your-domain.com
cp .env.example .env
# paste TRAVEL_AGENT_OPERATOR_ID, TRAVEL_AGENT_PRIVATE_KEY_B64, and TRAVEL_AGENT_PUBKEY
docker compose up --build
```

The demo runs three containers:

- `travel-agent`: issues OBO Credentials and seals Evidence Envelopes
- `flight-search`: verifies OBO before executing A2A tasks
- `anchor`: mints Merkle-style evidence receipts

It exercises seven scenarios: two accepted requests and five fail-closed
rejections for missing OBO, expired credential, invalid signature, intent hash
mismatch, and replay.

## Verify A Credential

This repo includes a tiny verifier CLI:

```bash
./obo verify examples/credentials/signed-demo.json \
  --intent "search flights from LHR to JFK on 2026-06-15" \
  --public-key m2OHbJ8-t7ch8YxL5vFU7K7ysDQfi8SJ58PDHxcc2qw
```

For deployed operators, use DNS:

```bash
./obo verify credential.json --intent "<canonical intent phrase>" --dns
```

The verifier checks:

- credential structure against the JSON Schema (requires `jsonschema`)
- credential digest
- intent hash when `--intent` is supplied
- issuance time, a valid time window, and expiry (exclusive expiry boundary)
- Ed25519 signature using exactly one required source: `--dns` or `--public-key`

`--ignore-expiry` is for archived credentials and skips only the current expiry
check. DNS mode currently requires `issuer_id` to equal `operator_id`; otherwise
supply an independently trusted issuer key. Success means credential integrity
was verified. It does not verify consent, legal authority, binding proofs,
revocation, replay state, or execution policy. Credentials carrying delegation
chain or instance-proof fields are rejected because those verifications are not
implemented by this CLI. Profile payloads and scope constraints require a separate
policy verifier. See [Current Status](docs/CURRENT-STATUS.md) for coverage.

## External Grant Experiment

An issuer-signed JWT can be retained unchanged alongside signed service policy,
decision and execution receipts. The supplier-update fixtures cover acceptance
and refusal with independently supplied trust keys and historical status.

```bash
./obo --version
./obo verify-bundle examples/integrations/external-grant/accepted.json \
  --trust examples/integrations/external-grant/trust.json --at 1793016000
```

Install `requirements-dev.txt` first. This command selects an explicitly supported
experimental profile, including operation/response binding and the local field-allowlist
policy. It does not implement generic OAuth ingestion, delegation chains, proof
of possession or live replay control. The report always includes its limits;
missing historical status returns `incomplete` (exit 2). All bundled keys are
public test keys. See the [profile](profiles/external-grant-evidence-v0.5.md).

The [PocketBase receiving-service harness](examples/integrations/pocketbase/)
adds live admission, native API writes/readback, durable request reservations
and idempotent retries. It uses the same experimental wire profile. Run its
documented live tests to exercise a pinned third-party backend rather than
only generated fixtures.

The [Keycloak issuer harness](examples/integrations/keycloak/) additionally uses
real native RS256 service-account tokens and a separate signed mandate in
`obo-keycloak/0.5-alpha.3`. This keeps workload authentication distinct from the
principal's declaration of delegated authority. It is one tested configuration,
not a claim of generic OAuth compatibility or lawful delegation.

The [Node verifier](implementations/node/) is a second implementation, not a
third-party assurance claim. It checks the same retained live evidence and
[shared public vectors](tests/vectors/keycloak/) with a separate JOSE stack.

## Conformance

CI runs:

- schema validation for every JSON example
- verifier regression tests, including rejection cases and missing dependencies
- stale draft-version checks
- live DNS fixture verification
- Python syntax checks
- signed demo credential verification
- reproducible external-grant fixtures and offline evidence verification
- a pinned real PocketBase receiving service, including persistence and restart tests
- a digest-pinned Keycloak issuer, explicit mandates and the same receiving-service workflow
- separate Python/Node verification of shared vectors and live Keycloak evidence
- full Docker A2A demo

Run the local checks:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/check_draft_version.py
python3 scripts/validate_examples.py
python3 -m unittest discover -s tests -v
python3 scripts/check_dns_fixture.py
python3 -m py_compile obo examples/integrations/a2a/agents.py
```

## What Is Optional

| Capability | Required for | Status |
|---|---|---|
| OBO Credential and Evidence Envelope | All OBO use cases | Required |
| `_obo-key.<operator-domain>` DNS record | Cross-organisation verification | Required unless another profile defines an equivalent trust anchor |
| Evidence Anchor / Merkle anchoring | Regulated or dispute-heavy audit trails | Optional profile |
| `why_ref` | Regulated rationale chain | Optional profile field |
| `profile_evidence` | Domain-specific evidence such as VI or ISO 20022 fields | Optional profile payload |
| aARP / routing corridors | Dynamic intent routing | Separate protocol |

## What OBO Is Not

OAuth and OAuth Token Exchange remain useful within trust domains, and OAuth
identity chaining addresses interaction between domains with separate trusted
authorization servers. OBO's proposed evidence objects can be evaluated alongside
those mechanisms. An interoperability mapping has not yet been implemented.

OBO does not replace Verifiable Credentials. VCs are useful for portable
identity claims. OBO adds transaction-scoped delegation and post-transaction
evidence.

OBO is not reputation. Reputation can help with discovery and routing, but it
does not prove authority, scope, liability, or what happened in a dispute.

OBO is not a payment rail. Payment profiles can carry OBO evidence, but OBO does
not move money.

## Profiles And Examples

Examples:

- [examples/credentials/](examples/credentials/)
- [examples/envelopes/](examples/envelopes/)
- [examples/integrations/a2a/](examples/integrations/a2a/)
- [examples/integrations/external-grant/](examples/integrations/external-grant/)
- [examples/integrations/pocketbase/](examples/integrations/pocketbase/)
- [examples/integrations/keycloak/](examples/integrations/keycloak/)

Profiles:

- [profiles/external-grant-evidence-v0.5.md](profiles/external-grant-evidence-v0.5.md)
- [profiles/keycloak-mandate-v0.5.md](profiles/keycloak-mandate-v0.5.md)
- [profiles/payments-mastercard-vi.md](profiles/payments-mastercard-vi.md)
- [profiles/payments-swift-iso20022.md](profiles/payments-swift-iso20022.md)

Useful background:

- [Current Status and External Work](docs/CURRENT-STATUS.md)
- [AI Identity Paper Mapping](docs/AI-IDENTITY-2604-23280-MAPPING.md)
- [OBO 8 Mapping](docs/OBO-8-MAPPING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [The Scope Problem](docs/THE-SCOPE-PROBLEM.md)
- [Security Guide](docs/SECURITY.md)
- [FAQ](docs/FAQ.md)
- [Standard Family](docs/STANDARD-FAMILY.md)

## Contributing

Implementation reports are the most valuable contribution:

- Which fields did you implement?
- Which semantics were ambiguous?
- Which use case or jurisdiction did you target?
- What broke when you tried to verify across an organisational boundary?

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHARTER.md](CHARTER.md).

This is an open standard. There is no approved network. There is no
co-signature gate.
