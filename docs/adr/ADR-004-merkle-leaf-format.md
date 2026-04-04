# ADR-004: tag:value Strings as Merkle Leaf Format

**Status:** Accepted
**Date:** 2026-04-02
**Deciders:** OBO working group
**Spec ref:** §4.3, Evidence Anchor mint API

---

## Context

The OBO Evidence Envelope is submitted to Evidence Anchor as a set of leaves that the Evidence Anchor
hashes into a Merkle tree. Each leaf becomes one node in the tree; the
`merkle_root` is a SHA-256 commitment over all leaves sorted lexicographically.

A format must be chosen for the leaf strings. The choice affects:
- Canonicalisation (deterministic serialisation)
- Human readability
- Implementation complexity
- Extensibility

---

## Decision

**Each leaf is a UTF-8 string in `tag:value` format, where `tag` is a short
ASCII identifier and `value` is the data. Leaves are sorted lexicographically
before Merkle construction. No quoting, no escaping, no nesting.**

Examples from the reference implementation:
```
event_time:2026-04-04T11:55:07.038933+00:00
obo_credential_id:urn:obo:cred:1d8d3842-…
obo_intent_hash:b98d4238ecb978415a30…
obo_outcome:allow
producer_id:lane2.ai
```

The Evidence Anchor API accepts these as a JSON array of strings in any order; Evidence Anchor sorts
them before constructing the tree.

---

## Rationale

### Canonicalisation is the critical property

A Merkle tree is only as useful as its canonicalisation is deterministic. If two
parties can produce different byte representations of the same logical record,
they will compute different `merkle_root` values and verification fails. This is
the central failure mode of JSON-based Merkle designs: JSON serialisation is not
canonical (key ordering, whitespace, number formatting all vary).

`tag:value` strings have exactly one canonical representation for any given tag
and value. There is no JSON serialiser to configure, no float formatting edge
case, no Unicode normalisation ambiguity. The canonical form is the string
itself.

### Why not JSON objects

JSON is the natural choice for structured data. It was considered and rejected:

**No canonical serialisation.** JSON does not define key ordering. Two
serialisers producing `{"outcome": "allow", "reason": "none"}` and
`{"reason": "none", "outcome": "allow"}` both produce valid JSON but different
bytes and different hashes. Working around this requires a canonicalisation
profile (JCS — RFC 8785) that adds implementation complexity and is not
universally supported.

**Nesting invites disputes.** Nested JSON structures create ambiguity about
what exactly is committed to. A nested object can be serialised at multiple
levels of granularity. Flat `tag:value` strings eliminate this: every leaf
is independently hashable and independently attestable.

**Verbose for the common case.** The majority of leaves are simple scalar
values (timestamps, identifiers, hashes, outcome codes). JSON wrapping adds
no information and requires parsing for verification.

### Why not CBOR

CBOR (RFC 7049) has a canonical form (CBOR Core Deterministic Encoding) and
is more compact than JSON. It was not chosen because:

- CBOR is not human-readable. A Merkle leaf in CBOR requires a decoder to
  inspect. `tag:value` strings can be read, logged, and verified in a terminal.
- CBOR library support is less uniform than JSON across languages.
- Human readability of evidence records is a design principle, not just a
  convenience — it reduces the barrier to independent audit.

### Why not `tag=value` (equals) or `tag::value` (double colon)

The colon separator is consistent with existing DNS record formats
(`v=obo1 ed25519=…`) and RFC-style parameter notation. It is unambiguous
because tag names are restricted to alphanumeric + underscore (no colons), so
the first colon is always the separator. Double-colon or equals signs introduce
potential confusion with base64, URLs, or other encoded values that use those
characters.

### Lexicographic sort by the Evidence Anchor

Sorting is done by the Evidence Anchor, not the submitter, for a specific reason: it
eliminates any possibility that the submitter can influence which leaves appear
adjacent in the tree (and therefore which sibling hash paths are used in
inclusion proofs). The submitter can submit leaves in any order; the tree
structure is deterministic regardless.

### Extensibility

New leaves can be added by any operator without coordination. A delegation
chain leaf (`delegation_id:urn:obo:del:…`) and a biometric leaf
(`biometric_score:0.987`) are both first-class leaves with no schema
registration required. All leaves for a transaction are committed into the same
`merkle_root`. The spec defines a set of REQUIRED leaves for each profile and a
set of NAMED optional leaves (§3.3, §3.4); operators may add further leaves
with their own tag prefixes.

---

## Consequences

**Positive:**
- Canonicalisation is trivial — the leaf string is its own canonical form.
- Leaves are human-readable in logs, captures, and audit trails.
- Extensible without schema registration.
- Lexicographic sort by Evidence Anchor makes the tree structure independent of submission
  order.

**Negative / watch points:**
- Values containing colons (URIs, timestamps) require that the parser splits on
  the first colon only. Implementations must use `split(":", 1)` not
  `split(":")`.
- No strong typing — a leaf value is always a string. Numeric values
  (`biometric_score:0.987`) must be normalised to a canonical decimal
  representation by the submitter to ensure consistent hashing.
- No built-in schema validation for individual leaves. The spec defines required
  leaves per profile; enforcement is at the Evidence Anchor profile validation layer.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| JSON objects as leaves | No canonical serialisation; nesting ambiguity |
| JCS (RFC 8785) canonical JSON | Implementation complexity; not universally supported |
| CBOR deterministic encoding | Not human-readable; library support less uniform |
| Protocol Buffers | Schema registration required; binary; no human readability |
| Key-value with `=` separator | Conflicts with base64 and URL-encoded values |
