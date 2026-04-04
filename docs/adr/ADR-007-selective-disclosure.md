# ADR-007: Selective Disclosure Alignment — PID Attributes Never Enter the Merkle Tree

**Status:** Accepted
**Date:** 2026-04-04
**Deciders:** OBO working group
**Spec ref:** §3.4, §10.1, §10.3

---

## Context

OBO's Intent Artifact (§3.4) captures the human authorisation act, including
identity verification evidence. For regulated transactions (Class C/D), this
evidence includes KYC checks, biometric verification, and — with EUDI Wallet
adoption — Selective Disclosure credentials (SD-JWT, ISO 18013-5 mdoc) issued
by national identity authorities.

A decision was required on what identity material is permitted as Merkle leaves
in the Evidence Anchor submission:

**Option A:** Include disclosed PID attributes (name, date of birth, nationality,
national identifier) as named Merkle leaves. Maximises audit completeness.

**Option B:** Include only a hash reference to the EUDI presentation. PID
attributes stay with the operator under applicable law. The Merkle tree proves
the process; the substance is held separately.

---

## Decision

**PID attributes MUST NOT appear as Merkle leaves. The `kyc_ref` leaf MUST be
a SHA-256 hash of the EUDI presentation bytes (or equivalent KYC record). No
field in the Evidence Anchor submission SHALL contain raw identity attributes
(name, national identifier, date of birth, address, or equivalent). The audit
trail proves that identity verification occurred and which presentation was
used; the substance of that verification is retained by the operator under GDPR
and applicable law.**

The normative `kyc_ref` format when referencing an EUDI presentation is:

```
kyc_ref:sha256:<lowercase hex of SHA-256(presentation_bytes)>
```

The optional `eudi_pid_issuer` leaf records the issuing national authority
without disclosing any PID attributes:

```
eudi_pid_issuer:ants.gouv.fr
```

---

## Rationale

### Selective Disclosure is a design constraint, not a feature

EUDI Wallet PID credentials use Selective Disclosure JWT (SD-JWT, RFC 9420
draft) and ISO 18013-5 mdoc precisely so that holders can reveal only the
minimum attributes required for a transaction. A travel booking may need name
and nationality; a medical appointment may need name and date of birth; a
financial transaction may need name and national identifier.

If OBO baked these disclosed attributes into the Merkle tree, it would:

1. Nullify the selective disclosure guarantee — the attribute would be
   permanently committed to a public log regardless of what the holder chose
   to disclose at that moment
2. Violate GDPR Article 5(1)(e) (storage limitation) — personal data would
   be retained in an append-only structure beyond its necessary purpose
3. Violate GDPR Article 25 (data protection by design) — the architecture
   would embed excessive data collection into the protocol
4. Create a cross-transaction correlation attack surface — an auditor with
   access to multiple Merkle roots could link transactions by matching PID
   attributes, even across pseudonymous agents

The correct architecture is that the Merkle tree proves *process*; the
*substance* stays with the operator.

### What `kyc_ref` actually commits to

`kyc_ref:sha256:<hex>` commits to the exact bytes of the EUDI SD-JWT or mdoc
presentation that the operator verified. This provides:

- **Binding:** The operator cannot swap out which verification was used after
  the fact — the hash pins the exact presentation
- **Non-disclosure:** The hash reveals nothing about which attributes were
  disclosed or what their values were
- **Reconstructibility:** With operator cooperation, the original presentation
  can be retrieved and the hash recomputed to prove the Merkle leaf is correct
- **Cross-reference:** An auditor or regulator can obtain the presentation from
  the operator and verify it matches the committed hash

This is the same design pattern as `intent_hash` (ADR-006): commit to the
hash; hold the substance. Consistency across OBO is intentional.

### GDPR Article 6 and operator custody

The operator holds the original EUDI presentation under GDPR Article 6
(lawful basis for processing — contract performance or legal obligation for
Class D transactions). The operator is the data controller for this material.
The Evidence Anchor operator sees only the hash leaf — it is not a data
controller for PID attributes.

This clean separation of custody means:
- Operators comply with GDPR independently for the PID data they hold
- Evidence Anchor operators are not dragged into PID compliance obligations
- Cross-border audit (EU AI Act Article 12) can proceed via the Merkle root
  without requiring PID data to cross organisational boundaries

### Minimum disclosure principle (§10.1)

OBO's existing minimum disclosure principle (§10.1) establishes that evidence
envelopes SHOULD contain the minimum data necessary for their accountability
purpose. The accountability purpose of the Merkle tree is to prove *that*
identity was verified — not *what* was disclosed. Therefore the hash is not
only permissible but correct.

---

## Consequences

**Positive:**
- OBO is structurally compatible with EUDI Wallet selective disclosure (SD-JWT,
  mdoc) and any future selective disclosure credential format
- GDPR compliance is achievable without architectural changes
- Evidence Anchor operators are not PID data controllers
- Cross-border audit via Merkle root does not require PID data sharing
- Aligns with §10.1 minimum disclosure principle already in the spec

**Negative / watch points:**
- A verifier cannot confirm *which* PID attributes were disclosed from the
  Merkle tree alone. They see that KYC occurred and which presentation was
  used; for the attributes, they must engage the operator directly.
- `kyc_ref` must be a hash of the *exact* presentation bytes. Operators must
  store the presentation bytes with sufficient precision to recompute the hash.
  Re-normalised or re-encoded presentations will produce a different hash and
  break the commitment.
- `sha256:<hex>` format is normative. Opaque provider-assigned KYC reference
  strings (e.g. `jumio-kyc-abc123`) are no longer sufficient for EUDI
  presentations — they do not provide verifiable binding to the presentation
  content.

---

## Migration note

Prior versions of §3.4 examples used opaque `kyc_ref` values
(e.g. `"jumio-kyc-abc123"`). Opaque references remain valid for non-EUDI KYC
providers where a hash-of-presentation is not available. For EUDI presentations
and any credential format supporting selective disclosure, `sha256:<hex>` MUST
be used.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Include disclosed attributes as Merkle leaves | Nullifies selective disclosure; GDPR Article 5(1)(e) violation; correlation attack surface |
| Include encrypted attributes | Encryption is not anonymisation under GDPR; key management adds complexity without resolving the data minimisation issue |
| Zero-knowledge proof of attribute disclosure | Valid future direction; not yet standardised for EUDI PID at the protocol level; premature to mandate |
| Opaque `kyc_ref` only | No verifiable binding between the leaf and the actual presentation; insufficient for Class D audit |
