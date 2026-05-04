# OBO - On Behalf Of

Minimum evidence standard for agentic transactions.

**Status:** Working Draft, `draft-obo-agentic-evidence-envelope-01`
**Goal:** implementation feedback, independent implementations, jurisdiction profiles

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

Inside one organisation, OAuth, mTLS, WIMSE, SPIFFE, and platform workload
identity already work. OBO is for the boundary case they do not solve:

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

The live demo fixture is:

```bash
dig +short TXT _obo-key.lane2.ai @8.8.8.8
# "v=obo1 ed25519=vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"
```

## Try It

Run the A2A reference demo:

```bash
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

- credential digest
- intent hash
- expiry unless `--ignore-expiry` is passed
- Ed25519 signature when `--dns` or `--public-key` is supplied

## Conformance

CI runs:

- schema validation for every JSON example
- stale draft-version checks
- live DNS fixture verification
- Python syntax checks
- signed demo credential verification
- full Docker A2A demo

Run the local checks:

```bash
python3 scripts/check_draft_version.py
python3 scripts/validate_examples.py
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

OBO does not replace OAuth inside a trust domain. If both parties already share
an authorisation server, use OAuth, OAuth Token Exchange, GNAP, mTLS, WIMSE, or
SPIFFE as appropriate.

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

Profiles:

- [profiles/payments-mastercard-vi.md](profiles/payments-mastercard-vi.md)
- [profiles/payments-swift-iso20022.md](profiles/payments-swift-iso20022.md)

Useful background:

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
