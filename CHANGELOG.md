# Changelog

## draft-00 — 2026-04-02

Initial publication.

### Specification
- OBO Credential: 12 required fields, 4 optional fields (§3)
- OBO Evidence Envelope: 13 required fields, 6 optional fields (§4)
- Four profiles: regulated lane (why_ref), local/offline, corridor-bound, multi-step (§5)
- Verification algorithm: credential and envelope (§6)
- Relationship to RFC 8693, W3C VCs, A2A protocols (§7)
- Security considerations: replay, intent manipulation, action class escalation, rationale revocation (§8)
- Open standard philosophy and contributor invitation (§9)

### Appendices
- Appendix A: OBO Credential JSON example
- Appendix B: OBO Evidence Envelope JSON example
- Appendix C: Mapping to DOP EvidenceContract (reference implementation)
- Appendix D: DNS Anchoring Profile
  - D.1 obo-dns-key: operator signing key (DKIM pattern, deployable now)
  - D.2 obo-dns-gov: governance pack digest anchor
  - D.3 obo-dns-null: nullifier epoch root (SAPP-backed sparse Merkle tree)
  - D.4a obo-dns-domain-proof: Ed25519 domain control proof (deployable now)
  - D.4b obo-dns-ptx: gnark PLONK suffix privacy proof (Phase 2)
  - D.7 corridor mutual verification and aARP binding

### Repository
- JSON Schema: obo-credential.json, obo-evidence-envelope.json
- Examples: open lane credential, regulated lane credential, basic envelope, regulated envelope with why_ref
- DNS zone templates: operator key, governance pack, corridor predicates (open, regulated, domain-gated)
- Profiles directory with contribution template
- IMPLEMENTATIONS.md registry

### Known issues / open questions for contributors
- D.4b suffix privacy circuit: gnark PLONK construction needs independent cryptographic review
- Jurisdiction profiles: none yet — contributions welcome
- Multi-corridor federation: proof composition across multi-hop paths unspecified
