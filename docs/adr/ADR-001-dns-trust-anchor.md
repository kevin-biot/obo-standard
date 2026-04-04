# ADR-001: DNS as the Trust Anchor for Operator Public Keys

**Status:** Accepted
**Date:** 2026-04-02
**Deciders:** OBO working group
**Spec ref:** §8.6, Appendix E

---

## Context

OBO verifiers need to resolve the public key of an issuing operator in order to
verify `credential_sig` and `envelope_sig`. This requires a trust anchor: a
mechanism that binds an operator identity (e.g. `lane2.ai`) to a cryptographic
key in a way that is authoritative, independently verifiable, and resistant to
impersonation.

Three options were considered:

1. **A centralised OBO registry** — a service run by the OBO working group (or
   a designated trust authority) that maps operator IDs to public keys.
2. **DNS TXT records** — each operator publishes its own public key under a
   well-known subdomain of its operator domain.
3. **W3C Decentralised Identifiers (DIDs)** — operator identity expressed as a
   DID, key resolution via the DID method (did:web, did:key, did:ebsi, etc.).

---

## Decision

**Use DNS TXT records as the primary trust anchor.**

```
_obo-key.<operator_id>  IN TXT  "v=obo1 ed25519=<base64url pubkey>"
```

The `operator_id` MUST be a registered domain name the operator controls. This
ensures that the operator's ability to publish a key is gated by their control
of the domain — the same proof used to issue TLS certificates via DNS-01
challenge.

DIDs are supported as an alternative profile (Appendix F) but are not the
primary mechanism.

A centralised OBO registry is explicitly rejected as a primary mechanism (see
below), but a curated registry of high-value known counterparties is RECOMMENDED
as a supplementary check for Class C/D transactions (§8.6).

---

## Rationale

### Why DNS over a centralised registry

**No single point of failure or control.** A centralised registry creates an
operational dependency — if it is unavailable, all OBO verification fails. It
also creates a governance problem: who controls the registry, how are entries
added or removed, and what recourse exists if an entry is incorrect?

DNS has no such single point. Each operator controls its own records. Operators
in different jurisdictions, industries, and trust domains can participate without
seeking permission from a central authority.

**Operator control over key rotation.** With a centralised registry, an
operator must request a key update through an external process. With DNS, the
operator updates their own zone immediately and the change propagates within the
record's TTL. This makes timely key rotation — critical for incident response —
entirely under the operator's control.

**Existing infrastructure and tooling.** Every operator with a domain already
has DNS. No additional PKI enrollment, no new credential type, no new
infrastructure. Verifiers already resolve DNS for every HTTPS connection; adding
a TXT lookup is a marginal operational addition.

**Established precedent.** DNS is already used as a trust anchor for: DKIM
(email sender authentication), DMARC (email policy publication), ACME DNS-01
challenge (TLS certificate issuance), MTA-STS (mail transport security). OBO
follows the same pattern in a new domain.

### Why not DIDs as the primary mechanism

DIDs are correct in principle and OBO supports them (Appendix F). However, DID
resolution is not universally implemented, method fragmentation introduces
interoperability risk, and `did:web` reduces to DNS-based trust anyway. For the
majority of agentic transaction operators — enterprises and SaaS platforms with
existing domain infrastructure — DNS is simpler and lower latency.

DIDs remain the right choice for operators who already use DID-based identity
infrastructure or for scenarios where the operator does not control a DNS zone
(e.g., individual agents with `did:key`).

### TTL and caching for Class C/D

Short TTL (60–300 s) is RECOMMENDED for operator keys. The risk of stale cached
keys is asymmetric: if a key has been rotated due to compromise, a verifier
using a stale cached copy will accept signatures from the compromised key for
the duration of the TTL. For Class C/D (irreversible, regulated) transactions,
this window must be minimised.

§8.6 goes further: for high-value known counterparties, a curated registry
(maintained by the verifier or a trusted third party) MUST be the primary
check. DNS is a trip-wire — it detects unexpected operators and signals key
changes — but is not sufficient alone for Class C/D.

---

## Consequences

**Positive:**
- No central OBO infrastructure required for basic operation.
- Key rotation is entirely under the operator's control.
- Verifier implementation is a single DNS TXT lookup, resolvable with any
  standard DNS client.
- Compatible with DNSSEC for additional integrity (where zone-signed).

**Negative / watch points:**
- DNS cache poisoning is a theoretical attack vector. Mitigated by short TTL,
  DNSSEC where available, and pinned trusted resolvers.
- Operators without domain control (e.g. individual developers) must use the DID
  profile or another out-of-band key distribution mechanism.
- A verifier that aggressively caches DNS responses may accept stale keys after
  rotation. Implementations MUST respect TTL and re-resolve per transaction for
  Class C/D.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Centralised OBO registry (primary) | Single point of failure; governance overhead; no operator autonomy |
| X.509 PKI | Certificate issuance overhead; CA dependency; not designed for per-transaction key resolution |
| Static configuration / allowlist only | Does not scale; out-of-band key distribution is operationally fragile |
