# ADR-006: Intent Hash in Credential, Not Intent Phrase

**Status:** Accepted
**Date:** 2026-04-02
**Deciders:** OBO working group
**Spec ref:** §3.1, §3.4, §10.3

---

## Context

An OBO credential must bind the authorised action to the credential in a way
that is verifiable by a third party. The "intent" — what the principal approved
— must be represented in the credential.

Two approaches were considered:

1. **Include the full intent phrase** in the credential (e.g.
   `"intent": "Book the cheapest economy flight from LHR to JFK on 15 April"`).
2. **Include only the hash of the intent phrase** (e.g.
   `"intent_hash": "b98d4238ecb978415a30…"` where
   `intent_hash = SHA-256(intent_phrase)`).

The intent phrase and its full detail can also be included separately in the
Intent Artifact (§3.4) when Class C/D accountability is required.

---

## Decision

**The credential carries `intent_hash = SHA-256(intent_phrase)`, not the phrase
itself. The full intent phrase is carried in the Intent Artifact (§3.4), which
is optional for Class A/B and required for Class C/D.**

Verification at the verifier: recompute `SHA-256(presented_intent_phrase)` and
compare to `intent_hash`. A mismatch is `OBO-ERR-005`.

---

## Rationale

### Privacy by default

The intent phrase may contain personally identifiable information or
commercially sensitive detail. Examples:

- `"Transfer £47,250 to account GB29NWBK60161331926819 for invoice INV-20482"`
  — contains an IBAN and an amount.
- `"Book appointment for Alice Chen at oncology clinic 14 April 14:00"`
  — contains a name, a medical context, and a timestamp.
- `"Cancel subscription for customer ID 8471820"`
  — contains a customer identifier.

If the full phrase were embedded in the credential, it would be visible to
every party that handles the credential — the verifier, any logging
infrastructure, any proxy, and any party that intercepts the credential in
transit. The credential is not encrypted by default (it is a signed but
public document, similar to a JWT).

Replacing the phrase with its SHA-256 hash exposes nothing about the content
of the intent to parties who handle the credential. The hash commits to the
phrase without revealing it.

### The binding is preserved

The hash retains the full cryptographic binding. If the agent presents a phrase
that does not match the hash, verification fails. The phrase cannot be
substituted, extended, or modified without breaking the binding. The security
property — that the verifier can confirm the action matches the authorised
intent — is identical whether the phrase or its hash is in the credential.

### The phrase is available where needed

For Class C/D accountability (dispute resolution, regulatory audit), the full
intent phrase is required. OBO provides this via the Intent Artifact (§3.4),
which carries `phrase` (the exact string), `structured` decomposition, and
`constraints`, signed by both the principal and the operator. This artifact is
submitted alongside the evidence envelope when required.

This separates the audiences:
- **Verifier** needs only the hash to perform the binding check.
- **Auditor / regulator** receives the full Intent Artifact with the phrase,
  the structured decomposition, and the authorisation proof.

### Canonical form for hashing

The phrase is hashed as a UTF-8 string with no leading or trailing whitespace,
Unicode-normalised to NFC. This is the canonical form. Any deviation in
whitespace or normalisation produces a different hash, which is the correct
behaviour — the phrase a principal approves must be exactly the phrase the
agent presents.

This also prevents subtle substitution attacks where an attacker modifies
whitespace or normalisation to change meaning while producing the same hash.
Since the canonical form is tightly defined, there is no ambiguity about what
was authorised.

### Comparison to OAuth / OIDC

OAuth 2.0 PKCE uses a similar pattern: the code verifier (the secret) is not
sent in the authorisation request; only `code_challenge = SHA-256(code_verifier)`
is sent. The actual value is presented later. OBO applies the same principle:
the credential carries the commitment; the phrase is presented at verification.

---

## Consequences

**Positive:**
- Credentials can be logged, proxied, and inspected without revealing intent
  content.
- The binding between authorisation and action is cryptographically identical
  to embedding the phrase.
- The full phrase is available in the Intent Artifact for Class C/D without
  being unnecessarily exposed for Class A/B.

**Negative / watch points:**
- Verifiers must receive the full intent phrase from the presenting agent (as
  well as the credential) in order to verify the hash. This is an additional
  field in the request. Implementations must ensure this field is present and
  not empty before attempting verification.
- The canonical form for hashing (NFC, no surrounding whitespace) must be
  precisely documented and consistently applied. A discrepancy between how the
  issuer computed the hash and how the verifier normalises the phrase will
  produce false `OBO-ERR-005` rejections. The spec defines the canonical form
  in §3.1.
- Hash preimage attacks: SHA-256 is currently considered collision-resistant for
  this use. If SHA-256 is weakened in future, the pre-image resistance that
  underpins privacy (an attacker can't recover the phrase from the hash) would
  also be affected. Migration to SHA-3 or a longer digest would be a spec
  revision.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Full phrase in credential | PII/sensitive content exposed to all credential handlers; violates §10.3 minimum disclosure |
| Encrypted phrase in credential | Requires key distribution to verifiers; adds complexity; hash is sufficient for binding |
| Structured decomposition only (no phrase/hash) | Decomposition is ambiguous — two different decompositions can represent the same or different intents; hash of the canonical phrase is unambiguous |
| No intent binding in credential | Credential would authorise an agent without constraining what it can do — not accountability, just identity |
