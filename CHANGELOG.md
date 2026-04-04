# Changelog

All notable changes to the OBO standard are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: IETF draft number (`-NN`) + semantic version (`vX.Y.Z`).

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
