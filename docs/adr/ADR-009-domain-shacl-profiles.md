# ADR-009: Domain SHACL Profiles — Emitter Responsibility, Corridor-Declared

**Status:** Accepted
**Date:** 2026-04-05
**Refs:** Appendix I, Appendix J, `schemas/obo-governance-pack.json`

---

## Context

The OBO Evidence Envelope is domain-agnostic. It records that an action
occurred, under what governance, with what outcome. It does not constrain
the semantic structure of the action itself — what a payment looks like,
what a clinical event contains, what a purchase basket requires.

As OBO corridors are deployed in regulated domains (payments, health,
securities), semantic validation becomes a compliance concern. ISO 20022,
HL7 FHIR, and equivalent standards define what well-formed domain actions
look like. A mechanism is needed to bind domain semantic constraints to
corridor governance without embedding domain knowledge in the OBO core.

## Decision

Domain semantic validation is expressed as **SHACL 1.0 shapes graphs**
and declared in the **governance pack** via `domain_shacl_profile` and
`domain_shacl_profile_digest`.

Validation against domain SHACL profiles is the **emitter's
responsibility** — it occurs before evidence is emitted, not at the
anchor. The anchor does not run SHACL on the hot path.

Domain profiles are **corridor-declared, not OBO-defined**. The OBO
standard defines no domain profiles. It defines the mechanism by which
corridors declare and bind them.

## Rationale

**Why SHACL over OWL:**
OBO evidence validation is a closed-world conformance problem, not an
open-world inference problem. SHACL validates whether a document
satisfies declared constraints. OWL reasons over incomplete information
to infer new facts. The former is what regulators, auditors, and dispute
arbiters need. No reasoner required.

**Why emitter responsibility:**
Running a full SHACL processor on every anchor submission at production
throughput (30,000+ RPS) is not viable. SHACL validation involves
JSON-to-RDF conversion, shape graph loading, and pattern matching — cost
is milliseconds per envelope. At scale this collapses throughput.

Emitter-side validation is the right architectural boundary: the emitter
pays the cost, validates once per session or credential window using
caching, and submits conformant envelopes. Non-conformant envelopes that
reach the anchor are minted but logged — the immutable record is itself
the accountability mechanism at dispute time.

**Why ISO 20022 for payments:**
OWL serialisations of ISO 20022 message schemas already exist (see
reference work by Chris Day and the ISO 20022 revision team). Domain
SHACL profiles for payment corridors SHOULD layer on top of these
serialisations rather than redefining payment vocabulary. This composes
OBO accountability with existing financial industry semantic
infrastructure.

**Why corridor-declared:**
Domain semantics vary by jurisdiction, regulatory framework, and
counterparty agreement. A payment corridor in the EU under PSD2 has
different semantic constraints than a securities corridor under MiFID II.
Centralising domain profiles in the OBO standard would require the
standard to track every domain's regulatory evolution — an unsustainable
maintenance burden. Corridor operators are the right owners.

## Consequences

- Governance pack schema includes `domain_shacl_profile` and
  `domain_shacl_profile_digest` fields.
- OBO standard publishes Appendix I (domain taxonomy, informative) and
  Appendix J (governance pack structure, normative).
- OBO standard defines no domain profiles. The taxonomy in Appendix I
  points at existing standards (ISO 20022, HL7 FHIR R4, schema.org,
  EUDI) without specifying profile content.
- Runtime resolution, caching, and enforcement of domain profiles is
  outside the scope of this specification. The distance between this
  specification and a production-grade domain validation implementation
  is non-trivial.
- Intent normalisation — mapping natural language intent to governed
  `intent_class` values — is implementation-defined and explicitly out
  of scope.
