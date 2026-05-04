# Changelog

All notable changes to the OBO standard are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: IETF draft number (`-NN`) + semantic version (`vX.Y.Z`).

---

## [draft-01 / v0.4.17] — 2026-05-04

**AI identity paper mapping — delegation remains legal-entity to workload.**

### Added
- **`docs/AI-IDENTITY-2604-23280-MAPPING.md`**: maps OBO to the
  April 2026 arXiv paper *AI Identity: Standards, Gaps, and Research
  Directions for AI Agents*. The note positions OBO as the declaration and
  evidence substrate inside the paper's declaration/observation/confidence
  model.

### Clarified
- OBO's legal premise: every software service call is a delegation event from a
  legal entity to a workload. AI agents increase autonomy and risk, but do not
  create legal standing for the workload.
- Courts and regulators test the legal entity's authority, controls, duty of
  care, governance, and evidence. A workload cannot determine the legal basis of
  its own delegation; it can only carry authority, operate within policy, and
  emit evidence.
- OpenID/OAuth OBO and OBO Standard are distinct: OAuth OBO is an intra-AS token
  exchange pattern; OBO Standard is a cross-organization delegation and evidence
  format.

### Notes
- No schema changes. This is a public positioning and research-mapping update.

---

## [draft-01 / v0.4.16] — 2026-04-26

**Public offering hardening — canonical wire model, conformance, and verifier path.**

This release turns the OBO public repository from a narrative-heavy draft into
a more testable public offering: one canonical wire model, examples that validate
against it, CI checks that prevent drift, and a small verifier path for people
who want to see a credential checked rather than just read about it.

### Added
- **`docs/OBO-8-MAPPING.md`**: public bridge from the market framing around
  "OBO 8" to the concrete OBO Credential and Evidence Envelope fields.
- **`docs/STANDARD-FAMILY.md`**: moved the longer standards-family narrative
  out of the README so the public entry point can stay focused.
- **`obo` verifier CLI**: `obo verify credential.json --intent "..." --dns`
  verifies credential digest, intent hash, expiry, DNS key lookup, and Ed25519
  signature checks.
- **`examples/credentials/signed-demo.json`**: signed credential fixture for
  verifier and CI use.
- **Conformance scripts**:
  - `scripts/validate_examples.py`
  - `scripts/check_draft_version.py`
  - `scripts/check_dns_fixture.py`
- **GitHub Actions conformance workflow** running schema validation, draft drift
  checks, live DNS fixture verification, verifier CLI checks, Python compile
  checks, and the Docker A2A reference demo.

### Changed
- **Canonical wire model frozen across spec, schemas, examples, and demo**:
  - credential identifiers use `obo_credential_id`
  - timestamps use Unix epoch integers
  - `intent_hash` is a required credential and evidence field
  - `credential_sig` and `envelope_sig` are required Ed25519 signature fields
  - `operator_id` and `reason_code` are required in evidence envelopes
  - DNS operator keys use `_obo-key.<operator-domain>` TXT records shaped as
    `v=obo1 ed25519=<base64url-public-key>`
- **A2A integration demo** now emits canonical OBO Credentials and Evidence
  Envelopes, validates failure scenarios with typed `OBO-ERR-*` reason codes,
  and mints both allow and deny evidence.
- **README** rewritten as a public entry point: problem statement, two artifacts,
  canonical wire model, 10-minute demo, verifier path, conformance status,
  optional versus required fields, and "what OBO is not."
- **Payment lifecycle and SWIFT examples** now use base envelope fields plus
  `profile_id` and `profile_evidence` for profile-specific data.
- **DNS templates and public docs** updated to the canonical `_obo-key` operator
  key shape and draft `-01` references.

### Notes
- This is a wire-model and public-conformance release. It intentionally favors
  fewer names, fewer aliases, and executable examples over broader explanatory
  surface area in the repository root.

---

## [draft-01 / v0.4.15] — 2026-04-17

**Identity is delegation of a legal entity — AGNTCY positioning.**

Fixes a framing error that entered earlier material: describing OBO as
"doing evidence" while a separate layer (CoSAI AIAM, AGNTCY, etc.)
"does identity." That framing concedes too much. An agent has no
independent legal standing (§1.9), so an agent identifier without a
delegation is a workload tag, not an identity. *Identity* in the
legally meaningful sense — the sense that matters to a counterparty,
a regulator, or a court — is always the delegation itself: on whose
authority is this agent currently acting, within what limits, under
what governance. OBO therefore does identity, and does so more
completely than the workload-identity systems it is sometimes
contrasted with.

This release reflects that correction across the draft and the
CoSAI composition note, and adds an explicit relationship section
for AGNTCY Identity (the Linux Foundation project CoSAI WS4 is
currently evaluating).

### Added
- **§1.2.1 — third framing error**: extended with the
  identity-as-separable-from-delegation error. Workload-identity
  primitives (SPIFFE SVIDs, service accounts, agent badges) are
  inputs to `agent_id`/`operator_id`; they do not constitute the
  identity that matters across a transaction.
- **§1.9 — new principle**: *"An agent identifier without a
  delegation is a workload tag, not an identity."* Sits with the
  existing *"Agents execute under delegated authority"* principle.
  States that the OBO Credential *is* the identity, expressed as a
  delegation of a legal entity, not "delegation wrapped around an
  identity."
- **§8.5 Relationship to AGNTCY Agent Identity Badges**: new
  section. Positions AGNTCY as a workload-identity primitive that
  composes into OBO's `agent_id`/`operator_id` fields, with the
  AGNTCY Badge → OBO Credential → OBO Evidence Envelope stack made
  explicit. Notes the trust-anchor option of publishing an AGNTCY
  Issuer's signing key in DNS (§E.3) to resolve the
  centralised-CA-vs-W3C-DIDs tension visible in AGNTCY discussions.
- **References**: added [AGNTCY-ID] and [OASF].
- **README**: AGNTCY added to the "composes with" list alongside
  OAuth, WIMSE/SPIFFE, W3C VCs, and A2A.
- **`docs/COSAI-COMPOSITION.md`**: new *A note on "identity"*
  subsection at the top correcting the earlier identity/evidence
  split; new *AGNTCY Badges as a workload-identity input* section
  at the end mirroring draft §8.5.

### Notes
- No schema changes. No normative changes to the credential or
  evidence envelope. Alignment is documentary and positions the
  specification correctly against adjacent work.

---

## [draft-01 / v0.4.14] — 2026-04-17

**CoSAI AIAM alignment — and the deeper category error it exposes:
the agent-operator IS an authorization server.**

Incorporates analysis of CoSAI Workstream 4 *Agentic Identity and
Access Management* (OASIS Open, v1.0, 20 March 2026). The alignment
work surfaced a framing error that was implicit in earlier drafts:
"cross-organisation verification without a shared AS" still pictures
the AS as a separate enterprise service the agent is a client of.
This release corrects the framing. Every agent-operator is itself an
authorization server — it holds the signing key, issues its own
credentials, binds its own governance pack, publishes verifying key
material into DNS. DNS is the federation layer. The "no shared AS"
problem dissolves because the specification does not presume ASes
were ever shared in the first place.

A related clarification: the LLM is execution substrate, not
protocol. The identity, delegation, and evidence layers are
substrate-independent — the same credential, corridor admission,
and sealed envelope apply whether the agent is a large language
model, a rule engine, or a compiled binary. Treating the LLM as a
central protocol concern is a category error.

### Added
- **§1.2.1 *The Deeper Category Error: The Agent Is Not a Client of
  an AS***: new sub-section promoting the agent-is-not-a-client-of-
  an-AS framing to a first-class structural claim. Names the operator
  as an AS, DNS as the federation layer, and the large body of "agent
  registry" work as workarounds for an absent shared AS that was
  never actually required.
- **§1.9 — the LLM is execution substrate, not protocol**: new
  design principle alongside *"the LLM is not the judge."* Clarifies
  that OBO's protocol surface contains no model identifiers, model
  versions, or prompt content; attestation binds the execution
  environment but does not make the model a party to the protocol.
- **§8.4 CoSAI Agentic Identity and Access Management**: relationship
  section describing convergence points (distinct agent/OBO rights,
  attestation scope, cascade revocation, HITL, fail-closed gateways)
  and divergences. Divergence #1 rewritten in the "operator-as-AS,
  DNS-as-federation-layer" framing — not "OBO removes the AS
  requirement" but "OBO does not presume ASes are shared."
- **§C.4 Correspondence with CoSAI AIAM OBO-JWT Claims**: claim-level
  mapping for `sub`, `act.sub`, `scope`, `authorization_details`,
  `azp`, `csc`, with coexistence pattern for agents that carry both
  an OBO-JWT inside the operator's perimeter and an OBO Credential
  across it.
- **§G.9 RFC 7009 interoperation note**: when an OBO Credential is
  bound to an OAuth token obtained via token exchange, RFC 7009
  revocation MUST propagate to the nullifier sink so internal and
  peer revocation converge.
- **References**: added RFC 7009, RFC 9396, [COSAI-AIAM],
  [COSAI-MCP-SEC], [NIST-SP-800-63].
- **`docs/COSAI-COMPOSITION.md`**: informative companion document.
  Peer-to-peer topology (not stacked): each operator is an AS,
  interoperation is peer-to-peer mediated by DNS. Includes
  convergence/divergence table and the combined-deployment pattern.

### Notes
- No normative changes to credential or evidence envelope schemas.
- No schema file changes; alignment is documentary.

---

## [draft-01 / v0.4.13] — 2026-04-05

**Transactional lessons §9: automation limits and the human decision layer.**

### Changed
- **`docs/TRANSACTIONAL-LESSONS.md`**: Added §9 *"Automation Has
  Limits — and the Agent Cannot Choose For You"* with five sub-sections:
  - §9.1 *Selection vs execution* — execution within declared scope is
    what agents are for; selection above a consequence threshold is what
    humans are for; accountability chain breaks when the agent selects
    and the agent has no legal personhood
  - §9.2 *Reputation signals are not selection criteria* — signals
    aggregate past behaviour across contexts different from the current
    one; treating reputation as selection criteria is accountability
    laundering
  - §9.3 *The regulatory direction of travel* — EU AI Act mandates
    human oversight for high-risk decisions; direction of travel is
    toward broader requirements, not narrower; systems built assuming
    autonomous agent selection may find that assumption in tension with
    future regulation
  - §9.4 *The anti-pattern* — precisely stated: automated selection of
    consequential counterparties using reputation signals is an
    anti-pattern; the correct pattern is agents present options, humans
    decide, agents execute, evidence sealed
  - §9.5 *A note on aspiration* — respectful acknowledgment that the
    work is real and the aspiration is understandable; the concern is
    the assumption that sufficient signal quality makes autonomous
    selection safe; that assumption has not been tested at scale under
    adversarial conditions in regulated contexts

---

## [draft-01 / v0.4.12] — 2026-04-05

**Transactional lessons — educational reference for the agentic ecosystem.**

### Added
- **`docs/TRANSACTIONAL-LESSONS.md`**: Eight-section educational
  document offering lessons from thirty years of transactional
  infrastructure to the agentic AI ecosystem. Tone: respectful and
  historical, not preachy. Sections: (1) The $5 problem — volume
  multiplies harm, consumer protection law does not scale with
  transaction value, small transactions teach architecture; (2) Failure
  modes are designed not discovered — the question before building is
  what happens when it fails, not when it works; (3) Authorisation is
  explicit or it does not exist — capability is not permission, prior
  behaviour is not standing permission, scope matters, authorisation
  must be counterparty-verifiable; (4) If it is not recorded it did
  not happen — tamper-evident, independent, temporally anchored,
  complete; (5) Liability must be assigned before execution — agents
  are not legal persons, "the AI did it" is not a defence, liability
  assignment must precede capability; (6) Automation amplifies
  everything — errors, fraud, and harm scale with the same multiplier
  as correct behaviour; (7) Discovery is not trust — the SWIFT
  correspondent model applied to agent discovery; (8) The moment of
  understanding — offered without the incident.

---

## [draft-01 / v0.4.11] — 2026-04-05

**Reputation paper: admission/adherence precedent and human decision layer.**

### Changed
- **`docs/REPUTATION-SYSTEMS-AND-AGENT-ACCOUNTABILITY.md`**: Added new
  §6 *"The Precedent: How Financial Networks Actually Work"* with two
  sub-sections:
  - §6.1 *Admission and Adherence for Agents* — SWIFT/Visa model:
    no reputation scores, only admission (legal entity, bound by
    rules) and adherence (conformant message). Applied to OBO:
    admission = OBO Credential, adherence = governance pack + sealed
    evidence. The model that works at global scale in financial
    infrastructure, applied to agents.
  - §6.2 *The Human Decision Layer* — high-consequence counterparty
    selection (which agent handles my finances, which contractor is
    admitted) is a human decision, not an agent optimisation.
    Reputation scores launder human decisions through automated
    proxies, removing humans from accountability chains at precisely
    the point their presence matters most.
  - Two new design principles added (§8.6, §8.7): use admission and
    adherence as primary trust signals for regulated corridors; do not
    delegate high-consequence selection decisions to agents.

---

## [draft-01 / v0.4.10] — 2026-04-05

**Reputation systems analysis paper — educational reference.**

### Added
- **`docs/REPUTATION-SYSTEMS-AND-AGENT-ACCOUNTABILITY.md`**: Full
  analysis paper on why reputation systems are insufficient for
  accountable agentic transactions. Eight sections covering: the
  fundamental distinction between reputation and accountability; what
  reputation systems actually measure; the severity collapse problem
  (99% success rate hides catastrophic domain-specific failure); the
  base rate problem; five concrete attack vectors (Sybil attack with
  full multi-phase playbook, collusion rings, success rate
  manufacturing via strategic omission, temporal gaming, cold-start
  inversion); what OBO provides instead (declared authority + sealed
  evidence); complementary stack model (reputation for discovery,
  accountability for regulated transactions); seven design principles
  for agentic systems in regulated domains.

- **`docs/FAQ.md`**: Added entry *"Can't we just use reputation scores?"*
  with pointer to the full paper.

### Design note
Motivated by analysis of emerging A2A ecosystem reputation proposals
(MoltBridge, OATR, attestation graphs). The paper does not attack
reputation systems — it defines precisely what they do and do not
provide, and why accountability is not a stronger form of reputation
but a structurally different thing.

---

## [draft-01 / v0.4.9] — 2026-04-05

**Agent instance binding — closes runtime authorization gap natively.**

### Added
- **`docs/adr/ADR-010-agent-instance-binding.md`** (Accepted): Agent
  instance binding via `agent_instance_id` and `agent_instance_pubkey`
  in the OBO Credential. Instance signs all presentations with its
  Ed25519 private key; counterparties verify against the credentialed
  public key. No shared registry required — works cross-org at first
  contact. Subsumes external runtime authorization schemes (OATR et al.)
  for Pattern 2 deployments. Instance binding optional for Class A/B,
  required for Class C/D. Guidance on key rotation (new keypair on
  restart, new credential required).

- **`docs/adr/ADR-009-domain-shacl-profiles.md`** (Accepted): Formalises
  the domain SHACL profile decision: emitter responsibility, corridor-
  declared, ISO 20022 reference for payments. Documents why SHACL over
  OWL (closed-world conformance, not open-world inference), why emitter
  responsibility (anchor hot path performance), and why corridor-declared
  (regulatory domain evolution is the corridor operator's concern).

### Changed
- **`schemas/obo-credential.json`**: Added optional fields
  `agent_instance_id` (instance identifier, operator-defined scheme) and
  `agent_instance_pubkey` (Ed25519 public key, base64url, covered by
  `credential_digest`).

- **`schemas/obo-governance-pack.json`**: Added optional field
  `instance_binding_required` (boolean, default false). When true, all
  credentials under the pack MUST include instance binding fields.
  Implied true for regulated and sovereign admission tiers.

### Design note
The instance binding mechanism was motivated by analysis of the A2A
ecosystem's emerging runtime authorization layer (OATR). OATR solves
instance binding via short-lived JWTs from a shared registry — which
cannot operate cross-org at first contact. OBO instance binding uses
the credential itself as the binding artifact: the instance public key
is credentialed at issuance, the instance proves liveness by signing
presentations. No registry, no round-trip, offline-verifiable.

---

## [draft-01 / v0.4.8] — 2026-04-05

**AGNTCY composability integration guide.**

### Added
- **`docs/integrations/AGNTCY-COMPOSABILITY.md`**: Integration guide
  positioning OBO as the accountability layer above AGNTCY's Internet
  of Agents infrastructure (Linux Foundation; formative members: Cisco,
  Dell, Google Cloud, Oracle, Red Hat). Covers: layer diagram showing
  AGNTCY (infrastructure) vs OBO (accountability); composability map
  across all six AGNTCY components (OASF, Agent Directory, SLIM, A2A,
  MCP, Observability); full transaction flow for a regulated payment
  agent; explicit gap analysis (AGNTCY has no evidence record, no
  authority contract, no EU AI Act Article 12 coverage); identity
  composability (AGNTCY answers *who is the agent*, OBO answers *on
  whose authority*); OASF vs governance pack distinction; four known
  open questions (identifier alignment, SLIM transport, OASF
  capability advertisement, observability trace correlation).

### Design note
AGNTCY is the internet for agents. OBO is the audit trail of what
happened on it. The gap in AGNTCY's scope — evidence, accountability,
governance, EU AI Act Article 12 — is OBO's scope exactly. The two
standards are non-overlapping and compose cleanly.

---

## [draft-01 / v0.4.7] — 2026-04-05

**Governance pack schema and Appendix J.**

### Added
- **`schemas/obo-governance-pack.json`**: normative JSON Schema for the
  governance pack — the document resolved by `governance_framework_ref`
  in credentials and evidence envelopes. Covers: pack identity and
  integrity (`pack_id`, `pack_version`, `pack_digest`); corridor
  declaration (`corridor_id`, `corridor_admission_tier`,
  `action_classes`, `intent_namespace`); domain SHACL profile
  declaration with digest binding; evidence anchor endpoint; KYC and
  EUDI acceptance flags; scope constraints (jurisdictions, currencies,
  max transaction value); write-bearing policy reference; nullifier
  epoch root; pack lifecycle (`supersedes`, `expires_at`).
  Conditional: `domain_shacl_profile_digest` required when
  `domain_shacl_profile` is present.

- **`Appendix J`** (Normative): Governance Pack Structure. Defines
  pack identity and integrity verification, corridor declaration,
  domain SHACL profile binding, evidence anchor declaration, KYC
  requirements, scope constraints, and pack lifecycle rules. §J.9
  explicitly enumerates what the governance pack does not define:
  runtime resolution, profile caching, write-bearing enforcement,
  intent normalisation, and reference implementation detail.

### Design note
The governance pack is the corridor's published contract. Publishing
the schema and format completes the open surface of the standard:
RFC (evidence contract) + SHACL shapes (conformance) + governance pack
(corridor semantics). Runtime implementation of pack resolution,
domain validation, and write-bearing enforcement remains outside the
scope of this specification.

---

## [draft-01 / v0.4.6] — 2026-04-04

**Domain evidence shape taxonomy — informative appendix.**

### Added
- **`Appendix I`** (Informative): Domain Evidence Shape Taxonomy.
  Establishes four domain families — Financial, Health, Commerce,
  Identity/Sovereign — and maps each to existing reference standards
  (ISO 20022, HL7 FHIR R4, schema.org/GS1, EUDI/eIDAS 2.0). Includes
  governance pack `domain_shacl_profile` declaration pattern.
  Two normative sentences only: implementations in financial or health
  domains SHOULD validate against a domain profile before emitting
  evidence; this specification does not define how. §I.5 explicitly
  names what is out of scope: profile content, runtime resolution,
  caching, intent normalisation, and reference implementation detail.

### Design note
The taxonomy signals the domain space and points at existing standards
without prescribing implementation. Intent normalisation and runtime
domain validation are named as non-trivial implementation concerns.
No further guidance is provided by this specification.

---

## [draft-01 / v0.4.5] — 2026-04-04

**SHACL conformance shapes — closed-world semantic validation.**

### Added
- **`schemas/obo-evidence-envelope.shacl.ttl`**: SHACL 1.0 shapes file
  providing closed-world semantic validation of OBO Evidence Envelopes.
  Complements the existing JSON Schema (structural validation) with:
  - `obo:EvidenceEnvelopeShape` — all required fields, `sha256:<hex>`
    patterns, closed enumerations for `action_class`, `outcome`,
    `eudi_presentation_alg`, `corridor_admission_tier`
  - `obo:ClassDKYCShape` — cross-field constraint: Class D envelopes
    MUST include `kyc_ref` (ADR-007, §3.4.4.1)
  - `obo:EUDICompletenessShape` — cross-field constraint:
    `eudi_presentation_alg` requires `eudi_pid_issuer`
  - `obo:WhyRefShape` — nested `why_ref` object validation
  - Minimal vocabulary declarations (`obo:EvidenceEnvelope`,
    `obo:ActionClass`, `obo:AdmissionTier`) giving RDF identity to
    core OBO concepts without requiring an OWL reasoner
- **`Appendix H`** added to RFC: normative reference to SHACL shapes,
  shapes summary table, validation requirement, and relationship to
  JSON Schema.

### Design note
SHACL was chosen over OWL for the formal layer: OBO evidence validation
is a closed-world conformance problem, not an open-world inference
problem. No reasoner required. A SHACL 1.0 processor reporting zero
violations constitutes machine-readable compliance evidence.

---

## [draft-01 / v0.4.3] — 2026-04-04

**Lane2 commercial Evidence Anchor, public PoC endpoint, and performance context.**

### Added
- **`docs/PUBLIC-ANCHOR-ENDPOINT.md`**: complete integration guide for the
  Lane2 public Evidence Anchor endpoint (`https://anchor.lane2.ai`). Covers:
  all API paths, DNS trust material, mint/proof request/response examples,
  independent receipt verification (Python snippet, no Lane2 trust required),
  code examples in Python and Go, A2A integration wiring, terms of use (90-day
  retention, 100 req/min, free for PoC). Performance note: sub-5ms p99 minting
  latency for standard OBO submissions from co-region AWS.

### Changed
- **`docs/EVIDENCE-INFRASTRUCTURE.md`**: added two new sections:
  - *The Lane2 Evidence Anchor: Purpose-Built, Not Trillian-Wrapped* —
    comparison table (latency, architecture, OBO leaf schema awareness, epoch
    anchoring, operational complexity) vs. Trillian. The commercial model is
    compatible with the open standard; the spec was stress-tested against a
    real production implementation at real transaction volumes.
  - *Public Reference Endpoint* — pointer to the public PoC endpoint with
    terms, rate limits, DNS key resolution instructions, and enterprise PoC
    contact path.

---

## [draft-01 / v0.4.2] — 2026-04-04

**Evidence infrastructure context: Merkle log over blockchain rationale, CT
analogy, regulatory mandate, and the case that evidence cannot be ignored.**

### Added
- **`docs/adr/ADR-008-merkle-log-over-blockchain.md`**: technical decision
  record for the Evidence Anchor architecture. Explains why blockchain/DLT was
  rejected (wrong problem, wrong latency, wrong privacy model, Byzantine
  overhead not needed) and why Merkle append-only log was chosen (CT precedent
  at global scale since 2013, sub-100ms minting, DNS epoch anchoring, no
  per-transaction fees). Documents the production path: Google Trillian and CT
  log operators have the infrastructure today; OBO provides the schema.
  Includes independence requirement (Evidence Anchor operators SHOULD be
  independent of credential operators for Class C/D, analogous to CT log
  operators being independent of CAs).
- **`docs/EVIDENCE-INFRASTRUCTURE.md`**: strategic context document. Makes the
  case that tamper-evident evidence for agentic transactions is coming whether
  or not a standard exists, driven by: EU AI Act Article 12 (law since 2024),
  MiFID II / PSD2 / DORA (financial), MDR/IVDR (healthcare), GDPR Article 30,
  and legal/insurance/counterparty trust forces. Documents that the
  infrastructure already exists (Google Trillian, CT log operators), that OBO
  provides the missing schema and protocol, and that the CT analogy is exact.
  Includes the reference implementation's role: protocol validation and
  developer testing, not production deployment.

---

## [draft-01 / v0.4.1] — 2026-04-04

**EUDI Wallet composability, selective disclosure alignment, EU sovereignty framing.**

### Added
- **`docs/adr/ADR-007-selective-disclosure.md`**: normative decision that PID
  attributes MUST NOT enter the Merkle tree. `kyc_ref` MUST be
  `sha256:<hex>` of the EUDI presentation bytes for selective-disclosure
  credentials. Rationale: GDPR Article 5(1)(e), GDPR Article 25, and the
  end-to-end preservation of EUDI selective disclosure guarantees.
- **`docs/integrations/EUDI-WALLET-COMPOSABILITY.md`**: full technical and
  strategic integration reference. Covers: EUDI + OBO composability table,
  transaction flow, selective disclosure alignment, PSD2 SCA mapping, EU AI
  Act Article 12 compliance map, known limitations. Includes strategic section
  "EU Digital Sovereignty and the Agentic Layer" — EUDI as the EU's sovereign
  answer to Google/Apple ID, and OBO as the agentic accountability layer that
  makes EUDI useful beyond human-to-service interactions.
- **`docs/USE-CASES.md` — D4**: new Class D use case: EU citizen (Marie) uses
  ANTS-issued EUDI Wallet + AI travel agent for a regulated cross-border
  booking across UK airline, Dutch corporate card, French operator platform.
  Demonstrates: selective disclosure (name + nationality only), `kyc_ref` as
  hash not attribute, PSD2 SCA satisfaction, Article 12 audit chain across 3
  countries with 0 PID attributes in the Merkle tree.

### Changed
- **Spec §3.4.4 `authorisation_evidence`**: updated field definitions:
  - `kyc_ref`: now MUST be `sha256:<hex>` for EUDI/selective-disclosure
    presentations; opaque refs remain valid for non-SD KYC providers
  - `provider`: clarified to use PID issuer domain for EUDI integrations
  - `kyc_level`: `qualified` maps to eIDAS Level of Assurance High
  - Added `eudi_pid_issuer` (OPTIONAL): domain of EUDI PID issuing authority
  - Added `eudi_presentation_alg` (OPTIONAL): `sd-jwt` or `mdoc`
- **Spec §3.4.4.1** (new sub-section): normative selective disclosure rule —
  operators MUST NOT include raw PID attributes as Merkle leaves; `kyc_ref`
  is the only permitted identity commitment; rationale and GDPR alignment.
- **Spec §3.4.6 Evidence Anchor Leaves example**: updated to show EUDI format
  (`kyc_ref:sha256:…`, `eudi_pid_issuer:ants.gouv.fr`, `eudi_presentation_alg:sd-jwt`);
  replaced `apple_faceid` with `ants.gouv.fr` as biometric provider example;
  added explanatory note on selective disclosure.
- **Spec §3.4.2 schema example**: `kyc_ref` now shows `sha256:<hex>` format;
  `provider` updated to `ants.gouv.fr`; `kyc_level` updated to `qualified`;
  `eudi_pid_issuer` and `eudi_presentation_alg` fields added.

---

## [draft-01 / v0.4.0] — 2026-04-04

**SAPP → Evidence Anchor: remove proprietary product name from normative text.**
No normative spec changes — field names, API paths, and wire format unchanged.

### Changed
- **Spec:** all normative references to "SAPP" replaced with "Evidence Anchor".
  Section headings (§3.3.5, §3.4.6), OBO-REQ-015/017, error code descriptions
  (`anchor_submission_failed`), and boundary references updated.
- **`examples/integrations/a2a/sapp_stub/` → `anchor_stub/`**: directory
  renamed; `server.py` header updated; env vars `SAPP_PORT`/`SAPP_DATA_DIR`
  → `ANCHOR_PORT`/`ANCHOR_DATA_DIR`; log prefix `[SAPP]` → `[anchor]`;
  JWS typ `SAPP-PROOF+JWT` → `ANCHOR-PROOF+JWT`. Attribution note retained:
  *"This stub is based on SAPP (Secure Agent Payment Protocol), the internal
  reference implementation."*
- **`docker-compose.yml`**: service `sapp` → `anchor`; build context updated;
  env vars and volume `sapp_data` → `anchor_data`.
- **`agents.py`**: `SAPP_URL`/`SAPP_ORG_ID`/`SAPP_PROFILE_ID` →
  `ANCHOR_URL`/`ANCHOR_ORG_ID`/`ANCHOR_PROFILE_ID`; `self.sapp_url` →
  `self.anchor_url`; all log/comment references updated.
- **All docs/** (`ARCHITECTURE.md`, `SECURITY.md`, `THE-SCOPE-PROBLEM.md`,
  `USE-CASES.md`, `FAQ.md`, ADRs, profiles, examples): "SAPP" → "Evidence
  Anchor" throughout.
- **`captures/README.md`**: added attribution note at top — records were
  captured against SAPP (the internal reference implementation); SAPP name
  retained throughout the file and in all `.json` captures as historical record.
- **CHANGELOG.md entries** prior to this release: left unchanged as historical
  record.

---

## [draft-01 / v0.3.8] — 2026-04-04

**FAQ: "How technically sophisticated people arrive here" section.**
No normative spec changes.

### Changed — Documentation
- `docs/FAQ.md`: added "How technically sophisticated people arrive here" —
  the four-step arc experts follow: OAuth → RFC 8693 → OpenID4VP → "compose
  technologies." Each step is correct on its own terms and stops at the same
  boundary. Step 4 ("there is no single answer, compose") is the arrival point
  — OBO is that composition, specified and running. Closes with why the journey
  takes four steps: existing standards were designed for systems calling systems
  in established trust relationships; OBO is designed for agents acting for
  humans at runtime across unknown counterparties.

---

## [draft-01 / v0.3.7] — 2026-04-04

**FAQ: DIDComm and GNAP entries added (pre-emptive).**
No normative spec changes.

### Changed — Documentation
- `docs/FAQ.md`: added DIDComm entry — both-parties-must-be-DID-based
  excludes existing HTTPS APIs; still no scope fence; still no post-transaction
  evidence; async mediator model doesn't fit synchronous API calls.
- `docs/FAQ.md`: added GNAP (RFC 9635) entry — more expressive than OAuth
  but still requires a shared AS; no intent_hash equivalent; no post-transaction
  evidence. Includes OAuth RAR (RFC 9396) footnote as the nearest thing to
  intent_hash in the OAuth ecosystem — same AS dependency, same evidence gap.

---

## [draft-01 / v0.3.6] — 2026-04-04

**FAQ: OpenID4VP entry added.**
No normative spec changes.

### Changed — Documentation
- `docs/FAQ.md`: added OpenID4VP entry — flow is backwards for M2M APIs
  (verifier-initiated VP request doesn't fit calling-agent-initiates pattern);
  VP carries identity claims not scope fence (no `intent_hash`); OpenID4VP
  ends at presentation, no post-transaction evidence equivalent. Composability
  note: use OpenID4VP for wallet/VC infrastructure, compose with OBO when
  scope-fencing and post-transaction evidence are also required.

---

## [draft-01 / v0.3.5] — 2026-04-04

**FAQ document.**
No normative spec changes.

### Added — Documentation
- `docs/FAQ.md` — short answers to the most common pushbacks:
  "But doesn't X already do this?" (RFC 8693, OAuth, WIMSE/SPIFFE, W3C VCs,
  A2A, mTLS, audit logs); "Why not just..." (central registry, human approval
  for everything, encryption, RSA); "What about..." (DNS compromise, GDPR,
  key theft, composability table). Each answer in 3–5 sentences.

---

## [draft-01 / v0.3.4] — 2026-04-04

**The scope problem document.**
No normative spec changes.

### Added — Documentation
- `docs/THE-SCOPE-PROBLEM.md` — why a certificate is not enough; the scope
  fence OBO adds (`intent_hash`, `action_class`, `principal_sig`); what happens
  in each out-of-scope case (no credential, hash mismatch, class exceeded);
  scope MUST NOT widen across delegation hops; DNS vs scope (two different
  problems); the payment dispute resolved in one paragraph without anyone
  testifying.

---

## [draft-01 / v0.3.3] — 2026-04-04

**Problem framing in USE-CASES, README draft identifier fix.**
No normative spec changes.

### Changed
- `docs/USE-CASES.md`: replaced generic opener with full trip-planning problem
  framing — five organisations, three countries, four questions, single-org
  case already solved, growth area is cross-org cross-border no shared AS.
- `README.md`: corrected stale draft identifier `-00` → `-01` in header.

---

## [draft-01 / v0.3.2] — 2026-04-04

**Use cases document with no-AS assumption clarification.**
No normative spec changes.

### Added — Documentation
- `docs/USE-CASES.md` — nine concrete scenarios across all four action classes
  (A1/A2 read-only, B1/B2 reversible write, C1/C2 irreversible, D1/D2/D3
  regulated). Each case: parties, before-OBO situation, after-OBO credential +
  evidence, accountability value. Covers travel (live demo), finance/PSD2,
  healthcare, legal, DevOps, and infrastructure.
  - **No-AS assumption section** — OBO assumes no shared Authorization Server
    between agents; if an AS exists, use OAuth / OIDC instead. OBO and OAuth
    are composable: internal legs use OAuth (shared AS), external legs use OBO
    (no shared AS). Includes ASCII diagram of the split-trust pattern.
  - Two-agent first contact problem section updated to reinforce the AS
    boundary: "If a shared AS does exist, use it. OBO is the answer to what
    do we do when it doesn't."
  - Summary table.

---

## [draft-01 / v0.3.1] — 2026-04-04

**Documentation: architecture, security, and design decision records.**
No normative spec changes.

### Added — Documentation
- `docs/ARCHITECTURE.md` — system component map, two-artifact model,
  trust hierarchy, action class table, evidence layer comparison,
  DNS anchoring patterns, A2A integration notes, spec section index.
- `docs/SECURITY.md` — implementer threat model (forgery, replay, intent
  substitution, scope escalation, tampered evidence, fabricated receipts);
  explicit non-goals table; key management guide (generation, storage,
  rotation); verifier and issuer hardening checklists; error code quick
  reference.
- `docs/adr/ADR-001-dns-trust-anchor.md` — why DNS over a central registry;
  operator autonomy; TTL guidance; Class C/D curated-registry requirement.
- `docs/adr/ADR-002-ed25519-only.md` — no algorithm agility; Ed25519
  rationale (deterministic, compact, no padding oracle); rejected RSA/ECDSA.
- `docs/adr/ADR-003-fail-closed.md` — all verification errors → deny;
  asymmetry of consequences; fail-open as attack surface; availability
  handled at deployment not protocol.
- `docs/adr/ADR-004-merkle-leaf-format.md` — tag:value strings as Merkle
  leaves; canonicalisation over JSON; CBOR rejected; first-colon split rule;
  extensibility without schema registration.
- `docs/adr/ADR-005-action-classes.md` — graduated A/B/C/D model; binary
  allow/deny rejected; mapping of classes to artifact requirements; scope
  MUST NOT widen at delegation hops.
- `docs/adr/ADR-006-intent-hash.md` — SHA-256(phrase) in credential not
  phrase itself; privacy by default; binding preserved; Intent Artifact
  (§3.4) carries full phrase for Class C/D audit.

---

## [draft-01 / v0.3.0] — 2026-04-04

**Material additions to normative content.**
Commits: `ceac769` ← `7b3e88a` ← `da33a49` ← `dad44df`

### Added — Spec
- **§3.3 Delegation Chain Artifact** — canonical JSON schema for the
  multi-hop delegation chain document. Each link carries `link_sig`
  (Ed25519 by the delegating party) and operator `issuer_sig` over
  `chain_digest`. Scope MUST NOT widen at any hop.
  OBO-REQ-004: credential must carry `binding_proof_ref` +
  `delegation_chain_digest`. OBO-REQ-005: Class C/D require full chain
  verification — deferred verification not permitted.
  SAPP leaves: `delegation_id`, `delegation_chain_digest`,
  `delegation_depth`, `delegation_issuer_sig`.

- **§3.4 Intent Artifact** — canonical JSON schema for the signed intent
  document. Carries `phrase` (the exact string behind `intent_hash`),
  `structured` decomposition, `constraints`, `principal_sig` (human
  authorisation proof), and `operator_sig` countersignature.
  `authorisation_evidence` sub-object: `method`, `provider`, `session_id`,
  `match_score`, `verified_at`, `kyc_ref`, `kyc_level`. REQUIRED for
  Class C/D. OBO-REQ-006/007.
  SAPP leaves: `intent_id`, `intent_authorised_at`,
  `intent_authorisation_method`, `intent_principal_sig`,
  `intent_operator_sig`, `kyc_level`, `kyc_ref`, `biometric_*`.

- **§3.5 Signing** — renumbered from §3.3 (no content change).

### Added — Reference Implementation
- `examples/integrations/a2a/captures/` — SAPP mint records from live
  run (2026-04-04, operator: `lane2.ai`, `source=dns-txt`).
  - `scenario-1-flight-search.json` — 14 leaves, `checkpoint_index: 0`
  - `scenario-2-hotel-search.json` — 14 leaves, `checkpoint_index: 1`
  - `captures/README.md` — leaf table, inline Ed25519 verification
    snippet, extended evidence section (14-leaf vs 30-leaf comparison,
    legal accountability table), SAPP Merkle signing best practice.

- **SAPP Merkle signing best practice** — explains the unsigned Merkle
  gap in the stub, production JWS payload format (ADR-181 E7),
  `_sapp-key.<domain>` DNS anchor pattern, epoch root anchoring.

### Changed
- Spec filename: `draft-obo-agentic-evidence-envelope-00.md` →
  `draft-obo-agentic-evidence-envelope-01.md`
- Spec header: version `0.1` → `v0.3.0`, date `2026-04-02` →
  `2026-04-04`, expiry updated, `Replaces:` field added.
- §4.4 cross-reference updated: `§3.3` → `§3.5`.
- All filename and draft-identifier references updated across README,
  schemas, and examples.

---

## [draft-00 / v0.2.2] — 2026-04-04

**Reference implementation with live DNS key verification.**
Commit: `dad44df`

### Added
- `agents.py`: `resolve_obo_key_from_dns()` — live
  `_obo-key.<operator_id>` TXT lookup per transaction (dnspython≥2.4);
  env var fallback. FlightSearchAgent logs `source=dns-txt|env` per
  request.
- `sapp_stub/server.py` rewritten to ADR-153: `POST /v1/evidence/mint`
  returns `{evidence_bundle, merkle_root, checkpoint_index, tree_size,
  created_at}`; `GET /evidence/{id}/proof` returns stub JWS. Profile
  validation (`regulated` requires `producer_id`, `event_time`,
  `schema_ref`), idempotency on `evidence_id`.
- `requirements.txt`: `dnspython≥2.4` added.
- `examples/integrations/a2a/README.md`: full runbook with architecture
  diagram, Route 53 setup steps, unedited captured output, SAPP leaf
  listing, DNS resolution notes, error code table, production gaps table.
- Root `README.md`: `## Reference implementation` section — live DNS
  verifier (`dig +short TXT _obo-key.lane2.ai @8.8.8.8`), scenario
  results table, evidence chain walkthrough. Roadmap phase 2a added.

### Changed
- Operator domain: `lane2.io` → `lane2.ai` (live Route 53 hosted zone).
- Docker host ports restored to `8080`/`8081` with conflict comment.

---

## [draft-00 / v0.2.1] — 2026-04-03

**§5 Error Taxonomy, Agent Cards, and 7-scenario demo.**
Commits: `4350123` ← `b52afe2` ← `d89503b`

### Added
- **§5 Error Taxonomy**: 22 error codes `OBO-ERR-001` through
  `OBO-ERR-022`; HTTP response format (§5.3); `reason_code` binding in
  evidence envelope (§5.4); retry semantics (§5.5). Former §5 Profiles
  renumbered to §6.
- `OBOEvidenceEnvelope.reason_code` field included in `evidence_digest`
  pre-image. `obo_reason_code` SAPP leaf.
- **A2A Agent Cards**: FlightSearchAgent serves
  `GET /.well-known/agent.json`. `authentication.schemes: ["obo"]` is
  the machine-readable OBO requirement signal. TravelAgent fetches the
  card on startup before sending any task.
- **7 demo scenarios**: 2 allow (flight search LHR→JFK, hotel search
  NYC) + 5 failure modes (tampered intent `OBO-ERR-005`, missing OBO
  extension `OBO-ERR-001`, expired credential `OBO-ERR-003`, forged
  signature `OBO-ERR-004`, replayed credential `OBO-ERR-008`).
- Replay detection via `_seen_credential_ids` set in FlightSearchAgent.
- `_reject()` helper: standardised HTTP 422 with `{error, reason_code}`.

### Changed
- `agents.py` wired to real SAPP `POST /v1/evidence/mint` (ADR-153)
  and `GET /evidence/{id}/proof` (ADR-181 E7).

---

## [draft-00 / v0.2.0] — 2026-04-03

**Framing and trust model clarifications (community feedback).**
Commits: `f2ed93a` ← `8dc1a3f`

### Changed
- Root `README.md`: new "Start here — two artefacts, zero
  infrastructure" section. Optional vs required table. "How OBO fits"
  → "How OBO composes with other work". Composition table with "Where
  OBO adds" column. "existing standards fail" →
  "OBO adds the accountability layer they were not designed to provide."
- **§8.6 trust anchor**: for high-value known counterparties the curated
  registry IS the real-time check. DNS is trip-wire. MUST NOT rely
  solely on cached DNS for Class C/D actions.

---

## [draft-00 / v0.1.0] — 2026-04-02

**Initial publication.**
Commits: `e13813c` and earlier

### Added
- **§1 Introduction**: four questions no existing standard answers
  together, two-agent first contact problem, minimal trust and
  progressive deepening, evidence/authorisation/intent not separable
  (§1.8), design principles (§1.9).
- **§2 Terminology**.
- **§3 OBO Credential**: required fields (§3.1) including
  `binding_proof_ref`, `delegation_depth`, `parent_credential_ref`;
  optional fields (§3.2); signing requirements (§3.3, now §3.5).
- **§4 OBO Evidence Envelope**: required fields (§4.1), optional fields
  (§4.2), integrity (§4.3), submission integrity via HTTP Message
  Signatures RFC 9421 (§4.4), multi-party HITL approval evidence (§4.5).
- **§6 Profiles**: regulated lane, local/offline, corridor-bound,
  multi-step transaction, multi-hop assertion model (§6.5).
- **§7 Verification**: credential verification, envelope verification,
  fail-closed behaviour.
- **§8 Relationship to Existing Standards**: OAuth 2.0 Token Exchange
  (RFC 8693), W3C Verifiable Credentials, A2A Agent Protocols.
- **§9 Security Considerations**: replay, intent manipulation, action
  class escalation, upstream rationale revocation, model identity
  (attestation not proof of computation), cross-domain trust
  bootstrapping, high-impact operations, LLM output not the
  authorization boundary.
- **§10 Privacy Considerations**: minimum disclosure, identifier
  construction, intent phrase minimization, rationale reference opacity,
  DNS-published corridor predicates, evidence envelope sharing, E.4b
  suffix privacy circuit.
- **Appendix E**: DNS Anchoring Profile.
- **Appendix F**: DID Profile (did:web, did:key, did:ebsi).
- `examples/integrations/a2a/`: Docker demo — TravelAgent +
  FlightSearchAgent + SAPP stub. Real Ed25519 signing, three containers,
  Docker health checks, SAPP evidence log.
- `schemas/obo-credential.json`, `schemas/obo-evidence-envelope.json`.
- `examples/credentials/`, `examples/envelopes/`,
  `examples/dns-zone-templates/`.
