# Changelog

All notable changes to the OBO standard are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: IETF draft number (`-NN`) + semantic version (`vX.Y.Z`).

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
