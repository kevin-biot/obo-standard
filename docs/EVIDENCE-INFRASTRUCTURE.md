# Evidence Infrastructure: What Is Coming and Why It Cannot Be Ignored

**Version:** 0.4.3
**Date:** 2026-04-04

---

## The Central Claim

Tamper-evident evidence for high-stakes automated decisions is coming whether
or not a standard exists. The regulatory direction is unambiguous, the
technical infrastructure is already built, and the economic incentive for
operators to anchor that evidence is growing. The only open question is who
defines what form the evidence takes.

OBO answers that question for agentic transactions.

---

## Evidence Is Already Mandatory at Adjacent Layers

OBO is not proposing something new. Tamper-evident evidence logs are already
operating at global scale in adjacent domains, and regulators have mandated
their use for years:

### Certificate Transparency (TLS, 2013–present)

RFC 6962 (2013) required that every publicly-trusted TLS certificate be logged
to an independent Merkle append-only log before browsers would trust it. This
was not optional and not phased in gradually — it was a hard requirement that
fundamentally changed how the TLS certificate ecosystem operates.

Today:
- Every TLS certificate trusted by Chrome, Firefox, or Safari is in a CT log
- Billions of certificates logged across dozens of independent log operators
- Log operators include Google (Argon, Xenon, Solera), Cloudflare (Nimbus),
  Let's Encrypt (Oak), DigiCert, Sectigo
- Any party can verify any certificate's inclusion proof without trusting the
  CA or the log operator
- The system has detected actual CA misbehaviour (Symantec, 2017) and produced
  the evidence to revoke trust in a major CA

CT proved that a mandatory, independently verifiable, Merkle-anchored evidence
requirement can be deployed globally at scale, with multiple competing log
operators, and works. It did not require blockchain. It did not require new
infrastructure concepts. It required a schema and a protocol — which OBO
provides for agentic transactions.

### Financial Services: Audit Trails Are Already Mandated

MiFID II (Markets in Financial Instruments Directive II, EU, 2018) requires
investment firms to maintain comprehensive records of all orders and
transactions sufficient to enable the competent authority to reconstruct the
order lifecycle. This includes algorithmic trading decisions.

PSD2 (Payment Services Directive 2, EU, 2019) requires Strong Customer
Authentication with dynamic linking — the authentication must be bound to the
specific transaction amount and beneficiary. This is an evidence requirement
embedded in a payment regulation.

DORA (Digital Operational Resilience Act, EU, 2025) requires financial entities
to maintain detailed ICT-related incident logs, including automated system
decisions that contributed to incidents.

These requirements exist and are enforced. The systems that satisfy them are
essentially private tamper-evident logs with regulatory access rights. OBO
provides an open, composable standard for this capability that works across
organisational boundaries.

### Healthcare: Evidence of AI Decisions Is Already Required

The EU Medical Device Regulation (MDR) and In Vitro Diagnostic Regulation
(IVDR) require post-market surveillance logs for AI-assisted diagnostic
devices. These logs must be tamper-evident and available for inspection by
notified bodies.

FDA 21 CFR Part 11 (US) requires audit trails for computer systems used in
clinical environments — specific to electronic records and signatures, the
requirement is that any change to a record must be logged and that prior
values are retrievable.

### GDPR: Records of Processing Are Already Required

GDPR Article 30 requires data controllers and processors to maintain records
of processing activities. For automated decision-making (Article 22), the
record must include the logic involved. For AI agents making decisions on
behalf of data subjects, the accountability record is not optional.

---

## The EU AI Act: The Trigger for Agentic Evidence

EU Regulation (EU) 2024/1689 (AI Act) is the most significant new mandate
for AI accountability in any jurisdiction. Article 12 requires:

> *Providers shall ensure that high-risk AI systems are technically designed
> and developed to ensure that their operation is sufficiently transparent
> to enable deployers to interpret the outputs and use them appropriately.
> High-risk AI systems shall be provided with instructions for use...
> including automatically recording events ('logs') over the lifetime of
> the system, to an extent appropriate to the intended purpose.*

"Automatically recording events" — this is a tamper-evident evidence
requirement for AI systems. The AI Act came into force in August 2024. The
technical standard for what those logs look like at the agentic transaction
level does not yet exist.

OBO is that technical standard.

The EU AI Act applies to high-risk AI systems in categories including:
biometric identification, critical infrastructure management, education,
employment, essential private and public services, law enforcement, migration,
justice administration, and democratic process management. Many of these
categories will involve AI agents acting autonomously on behalf of humans.
Every one of those agents will eventually be required to maintain evidence
logs. None of them have a standard for what those logs look like.

---

## The Infrastructure Already Exists

The key insight for adoption: **producing OBO-compatible evidence at scale
does not require new infrastructure investment by production operators.**

### Google Trillian

Google open-sourced Trillian in 2016 under the Apache 2.0 licence. Trillian is
a general-purpose Merkle log and Merkle map implementation — the same
technology that powers Google's Certificate Transparency log operations.

Trillian provides:
- Append-only Merkle log with cryptographic proofs of inclusion and consistency
- Signed tree heads at configurable intervals
- gRPC and REST APIs for log submission and proof retrieval
- Production-hardened: has operated CT logs at billion-entry scale

An organisation running Trillian today — or any CT log operator — can add OBO
Evidence Anchor support by implementing a new submission handler that:
1. Accepts OBO Evidence Envelope leaves (`tag:value` strings)
2. Submits them to Trillian as a new log entry
3. Returns a signed Evidence Anchor receipt

The OBO leaf schema and Evidence Anchor API (`POST /v1/evidence/mint`,
`GET /evidence/{id}/proof`) are the only additions needed. The log, the proof
generation, the signing, and the epoch anchoring infrastructure already exist
in Trillian.

This is not a theoretical claim. Trillian has been used as the backend for:
- Google's own CT log operations
- Certificate Transparency log pilots at multiple organisations
- Key Transparency (Google's experimental key distribution log)
- General-purpose audit log applications at enterprise scale

### Existing CT Log Operators

The organisations that currently operate CT logs have:
- Proven Merkle log infrastructure at scale
- Experience with inclusion proof generation and verification
- Signed tree head publication infrastructure
- Established relationships with auditors and regulatory bodies for log
  inspection
- Commercial infrastructure for log submission fees (the CT log fee model
  is already established with certificate authorities)

For these operators, adding an OBO Evidence Anchor endpoint is an extension
of existing operations, not a new line of business. The marginal cost of
adding OBO is low; the regulatory tailwind for evidence anchoring is
substantial and growing.

### The Independence Model: CT CAs and Log Operators as Analogy

Certificate Transparency works because log operators are independent of
Certificate Authorities. A CA cannot be the sole log for its own certificates
because the purpose of the log is to detect CA misbehaviour. Independence
is what makes the evidence credible.

The same logic applies to OBO:

- **OBO credential operators** (companies that issue OBO credentials to
  their AI agents) are the equivalent of Certificate Authorities
- **Evidence Anchor operators** (companies that run Merkle log services) are
  the equivalent of CT log operators
- The independence of these two roles is what makes the evidence credible to
  third parties — a regulator, a court, a counterparty — who has no prior
  relationship with either

OBO's architecture explicitly supports this separation. An operator submits
its evidence to an independent Evidence Anchor — one it did not build and
does not control. The Evidence Anchor issues a receipt with its own signature.
An auditor can verify the receipt against the Evidence Anchor's DNS-published
public key without trusting the credential operator.

This is the CT model. It works. It scales. The infrastructure exists.

---

## The Reference Implementation

OBO provides a reference Evidence Anchor server (`anchor_stub/`) that
implements the full Evidence Anchor API. It is intentionally minimal: a
Python Flask server that accepts leaf submissions, constructs a Merkle tree,
issues signed receipts, and serves inclusion proofs.

The reference server serves three purposes:
1. **Protocol validation:** Proves the API and leaf schema work end-to-end
   with real agents
2. **Developer testing:** Allows OBO credential and pipeline developers to
   test their evidence submission without standing up production infrastructure
3. **Specification anchor:** The reference implementation is the executable
   form of the Evidence Anchor API specification

The reference server is **not** the production path. It is not designed for
high availability, scale, or independent operation. It is the same role that
`openssl` plays relative to production TLS infrastructure — it implements
the protocol correctly and verifiably, enabling the ecosystem to develop
around the standard.

---

## What "Evidence Cannot Be Ignored" Means in Practice

The convergence of four forces makes accountable evidence for agentic AI
transactions inevitable:

### Force 1: Regulatory mandate

EU AI Act Article 12 is law. Compliance deadlines are in effect for high-risk
categories. The regulation does not specify the technical standard for
evidence logs — it specifies the requirement. OBO is positioned to be that
standard. National competent authorities (including ANTS in France, BSI in
Germany) will need to specify what "automatically recording events" means
technically for AI agents. OBO provides that answer.

### Force 2: Legal liability

When an AI agent causes harm — a wrong transaction, a missed medical alert,
a biased hiring decision — the question of accountability will be: who
authorised this, what did they authorise, and what did the agent actually do?
Without a tamper-evident evidence record, these questions are answered by
server logs (forgeable), contract terms (interpretive), and human testimony
(fallible).

With OBO, these questions have cryptographic answers. The legal system will
prefer cryptographic evidence over narrative reconstruction. Organisations
that can produce OBO evidence records will have a material advantage in
disputes. Organisations that cannot will face an evidential disadvantage
that grows as courts and regulators become familiar with what is possible.

### Force 3: Insurance and underwriting

Cyber insurers and professional liability underwriters are beginning to require
evidence of AI oversight controls as a condition of coverage. Evidence
anchoring — the ability to prove post-hoc that a specific agent acted within
its authorised scope — is exactly the kind of control that underwriters will
require as agentic AI exposure grows. The economics of AI liability insurance
will drive demand for accountable evidence infrastructure.

### Force 4: Counterparty trust

As AI agents interact across organisational boundaries — booking flights,
initiating payments, executing contracts — receiving organisations will
increasingly demand evidence that the agent was authorised before they accept
liability for the action. OBO's cross-org trust model (DNS-anchored, no shared
AS required) and post-transaction evidence provide exactly this. Early adopters
will use OBO compliance as a trust signal to counterparties.

---

## The Strategic Position

OBO is not asking anyone to build new infrastructure. It is defining the schema
and protocol that makes existing infrastructure — Trillian, CT log operations,
enterprise audit log stacks — applicable to the accountability problem in
agentic AI.

The analogy to Certificate Transparency is exact:
- CT did not invent Merkle trees, hash functions, or append-only logs
- CT defined the schema for what a certificate log entry contains, the API
  for submitting and proving inclusion, and the policy requirement that made
  it mandatory
- The infrastructure was built by the CT log operators on top of CT's schema
  and protocol

OBO does not invent Merkle trees, hash functions, or append-only logs.
OBO defines the schema for what an agentic evidence entry contains, the API
for submitting and proving inclusion, and the evidence chain that regulatory
requirements will eventually mandate.

The infrastructure will be built by Evidence Anchor operators — starting with
CT log operators who already have the stack — on top of OBO's schema and
protocol.

Evidence is coming. The infrastructure exists. OBO provides the missing piece.

---

## The Lane2 Evidence Anchor: Purpose-Built, Not Trillian-Wrapped

OBO defines the Evidence Anchor API. It does not mandate the implementation.
Any conformant server that accepts `tag:value` leaf submissions, constructs a
Merkle tree, issues signed receipts, and serves inclusion proofs is a valid
Evidence Anchor.

Lane2 built one. It is the commercial implementation that OBO was designed
alongside — the standard and the implementation informed each other
throughout development. It is called SAPP (Secure Agent Payment Protocol
Evidence Anchor) internally, and it is a production-grade commercial product.
The OBO standard is open; the implementation is ours.

### Why not wrap Trillian?

Trillian (Google, Apache 2.0) is an excellent general-purpose Merkle log.
It powers Certificate Transparency log operations at scale. But it is designed
as a distributed, multi-tenant infrastructure component — not as a
purpose-built Evidence Anchor for the OBO workload. The architectural
differences matter:

| Dimension | Trillian | Lane2 Evidence Anchor |
|-----------|----------|----------------------|
| Architecture | Separate log server process + external storage backend (MySQL / Spanner / PostgreSQL) + gRPC internal transport | Single-process, embedded storage, direct in-memory Merkle construction |
| Minting latency (single leaf batch) | 10–50 ms typical (storage roundtrip + gRPC) | Sub-millisecond (in-process, batched Merkle) |
| Inclusion proof generation | External RPC to log server | In-process, no network hop |
| OBO leaf schema awareness | None — leaves are opaque bytes | Native: validates `tag:value` format, enforces required leaf sets per action class |
| Epoch anchoring | Not built in; requires separate tooling | First-class: DNS TXT record publication per epoch |
| Operational complexity | Requires log server + storage + personality + front-end | Single binary, single config |
| Licence | Apache 2.0 (implementation open; you operate it) | Commercial (Lane2-operated or licensed) |

The performance gap exists because Trillian was designed to be general —
a Merkle log for any data, at any scale, operated by any party. Lane2's
implementation was designed to be specific: the OBO Evidence Anchor API,
and nothing else, as fast as possible.

For PoC work, the reference stub (`anchor_stub/`) is sufficient. For
production deployments where minting latency feeds into real-time agent
transaction pipelines, the sub-millisecond path matters. An agent transaction
must await the Evidence Anchor receipt before proceeding — every millisecond
of anchor latency is latency the human experiences.

### The commercial model is compatible with the open standard

SAPP is a commercial product built on an open standard. This is the same
model as:
- Nginx (open source) → Nginx Plus (commercial)
- Let's Encrypt (open, free CT log) → DigiCert (commercial CA with paid CT logging)
- OpenSSL (open source) → commercial TLS appliances

OBO defines the interface. Anyone can implement it — including using Trillian
as the backend. Lane2's implementation competes on performance, operational
simplicity, and support — not on protocol lock-in. The receipts Lane2 issues
are verifiable by anyone with the OBO spec and the Evidence Anchor's public
key. There is no proprietary wrapper around the evidence itself.

This matters for the open standard: the existence of a high-performance
commercial implementation demonstrates that the standard is production-viable,
not merely academically correct. The spec was stress-tested against a real
implementation, at real transaction volumes, under real latency constraints.
That is why the leaf schema is `tag:value` strings rather than JSON (ADR-004),
why the sort is done by the Evidence Anchor not the submitter (ADR-004), and
why epoch anchoring uses DNS rather than a blockchain (ADR-008) — these
decisions were made by people running the system, not only designing it.

---

## Public Reference Endpoint: PoC and Validation

Lane2 operates a public Evidence Anchor endpoint for the OBO community:

```
POST https://anchor.lane2.ai/v1/evidence/mint
GET  https://anchor.lane2.ai/v1/evidence/{id}/proof
GET  https://anchor.lane2.ai/v1/status
```

**This endpoint is available for:**
- PoC development against the live OBO Evidence Anchor API
- Integration testing of OBO Credential pipelines end-to-end
- Validation of Evidence Envelope construction and leaf schemas
- Demonstration to counterparties, regulators, and auditors that OBO works

**Terms:**
- No SLA. Best-effort availability.
- Evidence records are retained for 90 days then purged.
- Rate limited: 100 requests/minute per IP.
- Not for production use. Do not submit real personal data.
- The endpoint's Ed25519 public key is published at
  `_anchor-key.lane2.ai IN TXT "v=anchor1 ed25519=<pubkey>"` and in
  `/.well-known/obo-anchor` on the endpoint itself.

**To use it in your implementation:**

Set your Evidence Anchor URL to `https://anchor.lane2.ai` in your agent
or pipeline configuration. The endpoint accepts the standard OBO Evidence
Anchor submission format (§4.4) and returns signed receipts with Merkle
roots, checkpoint indices, and inclusion proof paths.

Any receipt issued by this endpoint can be independently verified by:
1. Resolving the Lane2 anchor public key from DNS
2. Verifying the `envelope_sig` in the receipt
3. Recomputing the Merkle root from the submitted leaves
4. Comparing against the checkpoint

This is the same verification path any Evidence Anchor receipt follows,
regardless of the operator. The verification is the proof — not trust in Lane2.

**To request increased rate limits or a dedicated PoC environment**, open a
discussion at `https://github.com/kevin-biot/obo-standard/discussions` or
contact Lane2 directly. Enterprise PoC environments with dedicated capacity,
extended retention, and priority support are available.

See [`docs/PUBLIC-ANCHOR-ENDPOINT.md`](PUBLIC-ANCHOR-ENDPOINT.md) for full
integration instructions, key material, and example receipts.
