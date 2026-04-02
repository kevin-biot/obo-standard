# Contributing to the OBO Standard

Thank you for your interest. This specification improves through implementation
experience, not through committee deliberation. The most valuable contribution
is trying to build something and reporting back what worked and what did not.

## What we need most

### 1. Implementation experience

If you implement the OBO Credential or OBO Evidence Envelope — in any language,
for any use case — please file an issue with:

- Which fields you implemented
- Any field whose semantics were ambiguous or underspecified
- What you decided to do and why
- A link to your implementation (if public)

This is the primary input to the next revision of the specification.

### 2. DNS deployment reports

The DNS Anchoring Profile (Appendix D) is deployable today with no new tooling.
Sub-profiles D.1 (operator signing key) and D.2 (governance pack digest) require
only a DNS TXT record and an Ed25519 keypair.

If you deploy any `_obo-*` record in DNS, please file an issue reporting:

- Which sub-profile you deployed
- Whether DNSSEC signing was available
- Any operational friction (TTL choices, key rotation, tooling gaps)

### 3. Jurisdiction profiles

OBO is domain-agnostic. Profiles for specific regulatory contexts are valuable:

- **Payments**: How does OBO map to PSD3 Article 65 (strong customer authentication)?
  How does the action class model map to payment initiation vs. account information?
- **Healthcare**: How does OBO map to NHS data access frameworks or HIPAA?
  How do action classes map to read vs. write vs. prescribe?
- **Legal**: How does OBO map to e-IDAS qualified electronic signatures?
- **UAE / GCC**: How does CBUAE Open Finance framework map to OBO corridor tiers?

A profile is a document that maps OBO fields to a specific regulatory context and
defines any additional required fields or constraints. File a PR against the
`profiles/` directory.

### 4. Cryptographic review

Appendix D.4b describes a gnark PLONK suffix privacy circuit for proving domain
suffix membership (e.g. `.ae`) without revealing the full domain. This construction:

- Extends the PTX commitment structure (IACR ePrint 2025/2332)
- Uses gnark PLONK with Poseidon hash
- Has NOT been independently security-reviewed

If you have experience with ZK circuit design, Groth16/PLONK systems, or the gnark
library, a review of the D.4b construction in Appendix D would be enormously
valuable. File an issue tagged `crypto-review`.

### 5. Co-authorship

If you contribute substantially to the specification — jurisdiction profiles,
implementation experience that changes field semantics, cryptographic review
that affects Appendix D — you are a co-author. File a PR adding your name and
affiliation to the authors section of the draft.

---

## How to contribute

**File an issue** for:
- Ambiguous field semantics
- Missing required fields for a use case
- Implementation experience reports
- DNS deployment reports
- Jurisdiction profile proposals
- Cryptographic review findings

**Open a pull request** for:
- Proposed specification text changes
- New examples in `examples/`
- New or revised DNS zone templates in `examples/dns-zone-templates/`
- New jurisdiction profiles in `profiles/`
- Schema corrections in `schemas/`

**Discussion:**
Use GitHub Discussions for broader questions about architecture, use cases, or
the relationship to other standards (OAuth, W3C VCs, A2A protocols).

---

## What we will not merge

- Changes that introduce a mandatory central registry or approval network.
- Changes that require a co-signature from a named commercial entity.
- Breaking changes to required field semantics without a versioned migration path.
- Proprietary extensions presented as normative requirements.

See [CHARTER.md](CHARTER.md) for the full governance model.

---

## Style guide for specification text

- Use RFC 2119 keywords (MUST, SHOULD, MAY) for normative requirements.
- Number requirements as OBO-REQ-NNN in sequence.
- Every required field must have: name, type, and one-sentence semantics.
- Examples must be valid against the JSON Schema in `schemas/`.
- DNS record examples must follow the naming convention in Appendix D.

---

## Code of conduct

Be direct. Be specific. Argue about specifications, not people. Implementation
evidence outweighs theoretical arguments. A working deployment that finds a flaw
is more valuable than a perfect argument that finds none.
