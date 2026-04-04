# ADR-003: Fail-Closed Verification

**Status:** Accepted
**Date:** 2026-04-02
**Deciders:** OBO working group
**Spec ref:** §7

---

## Context

OBO verification is a gate: an agent or service checks a presented credential
before executing an action. When verification fails — due to an invalid
signature, an expired credential, a missing field, an unresolvable key, or any
other error — the gate must make a binary choice: permit the action anyway
(fail-open) or deny it (fail-closed).

Some systems choose fail-open to preserve availability: "if we can't check,
we'll allow." This is common in networks (firewall rule misses), access control
(permission denied on check → allow), and service integrations (authentication
service down → allow with degraded mode).

---

## Decision

**OBO verification is fail-closed. Any verification error — regardless of cause
— results in a deny.**

This applies to:
- Invalid or malformed credential
- Signature verification failure
- Operator key not resolvable from DNS
- Credential expired
- Intent hash mismatch
- Replay detected
- Action class exceeded
- Missing required fields for the action class
- Any internal verification error (exception, timeout, unexpected state)

There are no error conditions under which a verifier SHOULD or MAY permit the
action while logging a warning. The only valid outcomes are allow (all checks
pass) and deny (any check fails or is inconclusive).

---

## Rationale

### The asymmetry of consequences

In agentic transactions, the consequence of a false negative (denying a
legitimate action) is inconvenience — the action must be retried with a valid
credential. The consequence of a false positive (allowing an invalid or
unverifiable credential) is an unaccountable action: something happened that
no one can prove was authorised.

For Class C/D actions (irreversible, regulated), the asymmetry is extreme. A
false positive under Class D is a regulated transaction with no audit trail.
Under PSD2, EU AI Act Art. 12, or similar regimes, this is not merely
operationally bad — it is a compliance failure.

The correct response to this asymmetry is to make false positives structurally
impossible by design, not just unlikely in practice.

### Fail-open is an attack surface

A fail-open fallback creates an incentive for attackers to cause verification
failures. If a verifier falls back to allow when DNS is unreachable, an attacker
who can disrupt DNS (e.g. via DDoS on the resolver, BGP hijack, or NXDOMAIN
injection) can bypass OBO verification entirely. The protection afforded by OBO
is only as strong as the least available component in the verification chain —
unless the failure mode is deny.

Fail-closed removes this attack vector entirely. Disrupting DNS is no longer a
path to bypassing credential verification; it is a path to a service outage,
which has a different (and much more visible) incident response.

### Clarity for implementers

A fail-closed rule is unambiguous. Implementers do not need to decide, for each
error condition, whether it warrants a deny or a degraded allow. The rule is:
verification either succeeds completely or the action is denied. This reduces
implementation surface and makes security audits simpler — there is only one
"allowed" code path.

### Error codes surface the reason

Fail-closed does not mean silent failure. Every denial MUST include a reason
code (`OBO-ERR-*`) that precisely identifies why verification failed. This
preserves debuggability and operational visibility while maintaining security.
A verifier can log, alert, and report on every denied request with full context.

### Availability is a deployment concern, not a protocol concession

If a production deployment cannot tolerate the availability impact of fail-closed
verification (e.g. DNS outages causing transaction failures), the correct
responses are:

1. Deploy DNS resolvers with high availability (multiple providers, local
   caching with short TTL, DNSSEC validation).
2. Maintain a curated registry of known counterparties as a Class C/D primary
   check (§8.6), reducing DNS dependency for the highest-value transactions.
3. Implement retry with backoff in the calling agent.

These are operational hardening measures. They do not require relaxing the
protocol's security posture.

---

## Consequences

**Positive:**
- OBO verification is not bypassable by causing system errors.
- Implementers have a single unambiguous rule.
- Compliance posture is consistent: no category of verification failure silently
  produces an unaccountable action.

**Negative / watch points:**
- A DNS outage affecting `_obo-key.<operator_id>` resolution will cause
  legitimate transactions to be denied until DNS recovers. This is the correct
  behaviour — and the operational signal that DNS infrastructure needs
  attention.
- Verifiers that log and alert on `OBO-ERR-006` (key not found) will surface
  DNS issues that might otherwise be invisible.
- Short-lived infrastructure hiccups (transient DNS timeouts) may produce
  spurious denials. Retry logic in the calling agent is the recommended
  mitigation, not relaxing the verifier.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Fail-open on DNS unavailability | Creates an attack vector; breaks accountability |
| Fail-open on expired credential (grace period) | Undefined grace windows are exploitable; operators must issue fresh credentials |
| Configurable fail mode (operator chooses) | Operators under pressure will choose fail-open; protocol security cannot be per-deployment configurable |
| Warn-and-allow for non-critical errors | "Non-critical" is not definable in a way that cannot be gamed; single rule is safer |
