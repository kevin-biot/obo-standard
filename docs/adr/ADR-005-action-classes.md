# ADR-005: Graduated Action Classes (A/B/C/D) Not Binary Allow/Deny

**Status:** Accepted
**Date:** 2026-04-02
**Deciders:** OBO working group
**Spec ref:** §3.1, §6, §9.3

---

## Context

OBO credentials authorise an agent to perform an action on behalf of a
principal. A decision was required on how to express the *scope* of that
authorisation — specifically, what category of action is being permitted.

The simplest approach is binary: a credential either permits or does not permit
the action. The alternative is a graduated scale that encodes the nature of the
action and the corresponding verification requirements.

---

## Decision

**OBO defines four action classes: A (read-only), B (write/reversible),
C (write/irreversible), D (regulated/high-value). Each class implies a
verification floor: C and D require a delegation chain artifact (§3.3) and an
intent artifact (§3.4). D additionally requires authorisation evidence
(biometric and/or KYC).**

The action class is set in the credential by the issuing operator. Verifiers
MUST reject any request where the action to be performed exceeds the class
bound of the presented credential.

---

## Rationale

### Binary allow/deny does not capture the risk gradient

An agent searching for flights (read-only, no side effects) and an agent
initiating a £50,000 wire transfer (irreversible, regulated) both need an OBO
credential. If the credential says only "allowed" or "not allowed", the
verifier has no basis for applying proportionate verification — it cannot know
that the wire transfer requires full delegation chain and biometric proof while
the flight search does not.

The risk to the principal and the accountability requirement to a regulator are
not the same for these two cases. The protocol must encode this difference
explicitly.

### Classes map to verifiable accountability requirements

The four classes are not aesthetic — each maps to a specific set of artifacts
that MUST be present and verifiable:

| Class | Description | Required artifacts | Spec obligation |
|-------|-------------|-------------------|----------------|
| A | Read-only, informational | Credential only | OBO-REQ-001 |
| B | Write, reversible (can be undone) | Credential only | OBO-REQ-002 |
| C | Write, irreversible | Credential + Delegation Chain + Intent Artifact | OBO-REQ-004/005/006 |
| D | Regulated / high-value | All Class C + authorisation evidence (biometric/KYC) | OBO-REQ-007 |

This is not a policy choice left to operators — it is a normative requirement.
An operator cannot issue a Class D credential without the delegation chain and
intent artifacts being present and verifiable. A verifier cannot accept a Class
D credential without checking them.

### "Irreversible" and "regulated" are the accountability boundaries

The key distinctions are:
- **A/B:** The action can be retried, reversed, or has no lasting effect.
  Accountability is desirable but not legally mandated for most cases.
- **C:** The action cannot be undone (a sent message, a deleted file, a booked
  flight, a committed code push). Accountability is essential because there is
  no remediation path — only compensation after the fact.
- **D:** Class C plus the action is subject to a regulatory regime (financial,
  medical, legal). Accountability must be independently verifiable in a form
  acceptable to a regulator or court. This requires not just cryptographic
  proof of authorisation but evidence of identity verification and explicit
  human approval.

### Scope MUST NOT widen at any delegation hop

This is a direct consequence of the class system. If a principal authorises an
agent at Class B, a downstream agent cannot re-interpret that delegation as
Class C authority. The class bound is set at issuance and enforced at every
hop in the delegation chain. See §3.3.

This prevents a common pattern in delegation systems where authority
inadvertently expands through layers of re-delegation. OBO makes scope
non-monotonically-widening by protocol.

### Four classes, not more

Four was chosen as the minimum set that captures the meaningful risk gradient
for agentic transactions without creating fine-grained classes that implementers
will misapply. The boundary between A and B (read vs write) and between C and D
(irreversible vs regulated) are the two clinically important distinctions.

Additional fine-grained classes within each tier are achievable via the
`corridor` predicate system (Appendix E) or profile-specific policy, without
adding new protocol classes.

---

## Consequences

**Positive:**
- Verifiers can apply proportionate verification without out-of-band policy
  lookup.
- Compliance requirements (PSD2 SCA, EU AI Act Art. 12) map directly to
  Class D requirements.
- The class is visible in the credential — auditors can see what was authorised.

**Negative / watch points:**
- Operators must correctly classify actions. Over-classifying (calling everything
  Class A) breaks accountability; under-classifying (calling a wire transfer
  Class A) is a compliance failure. The spec provides examples but cannot
  enumerate every possible action.
- Class C/D verification is more expensive — it requires retrieving and verifying
  the delegation chain and intent artifact documents in addition to the
  credential. This is intentional: the cost reflects the accountability
  requirement.
- New action types that don't fit A/B/C/D cleanly require judgment calls by
  operators. The spec guidance is: when in doubt, classify higher.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Binary allow/deny | Cannot encode risk gradient; verifier has no basis for proportionate verification |
| Free-text scope strings (OAuth-style) | No normative mapping to verification requirements; operationally inconsistent |
| Numeric risk score | Continuous values create threshold negotiation and boundary gaming |
| Policy-server lookup per action | External dependency; latency; verifier cannot fail-closed without policy server |
