# ADR-008: Merkle Append-Only Log over Blockchain / Distributed Ledger

**Status:** Accepted
**Date:** 2026-04-04
**Deciders:** OBO working group
**Spec ref:** §4.3, §4.4, Appendix E

---

## Context

OBO requires a tamper-evident, independently verifiable record of each
transaction's evidence envelope. A technology must be chosen for the
Evidence Anchor — the service that accepts Evidence Envelopes and produces
auditable commitments.

Two broad families were evaluated:

**Option A — Blockchain / Distributed Ledger Technology (DLT):** Submit
evidence to a blockchain (public or permissioned). The chain's consensus
mechanism provides tamper-evidence and independent verifiability.

**Option B — Merkle Append-Only Log:** Submit evidence as a set of
`tag:value` leaves; the Evidence Anchor hashes them into a Merkle tree,
produces a signed checkpoint, and periodically anchors epoch roots in DNS.
Independent verifiability is achieved via inclusion proofs, not consensus.

---

## Decision

**OBO uses a Merkle append-only log. Blockchain / DLT is explicitly rejected
for OBO's core evidence anchoring use case.**

The decision is modelled directly on Certificate Transparency (RFC 9162),
which has operated this architecture at global scale since 2013 without a
distributed ledger of any kind.

---

## Rationale

### 1. Certificate Transparency proved this model a decade ago

Certificate Transparency (CT) solves an identical problem in the TLS
ecosystem: how do you produce a tamper-evident, publicly verifiable record
that a certificate was issued, in a form that any party can audit, without
requiring a distributed consensus network?

The answer CT chose in 2013 — and which has since logged billions of
certificates across dozens of independent operators — is a Merkle
append-only log with signed tree heads. RFC 6962 (2013), updated by
RFC 9162 (2021). No blockchain. No consensus protocol. Merkle inclusion
proofs, signed checkpoints, and DNS/CT-log-list anchoring.

OBO's Evidence Anchor is CT applied to agentic transactions. The
architecture is not novel — it is CT with a different leaf schema.

Google (Argon, Xenon, Solera), Cloudflare (Nimbus), Let's Encrypt (Oak),
DigiCert, Sectigo, and others all operate CT logs today. These operators
have a directly applicable existing infrastructure base for operating
OBO Evidence Anchors. They do not need to build anything new — only to
add an OBO-compatible submission endpoint alongside their existing log
operations.

### 2. Blockchain solves the wrong problem

Blockchain provides Byzantine fault tolerance: the ability to reach consensus
on a shared state among parties where any participant might be adversarial.
This is the correct solution when you have no trusted operator and need the
system to function even if a majority of participants collude.

OBO's trust model is different. The operator has already signed the OBO
Credential. The operator is already the accountable entity for the
transaction. The Evidence Anchor's job is to produce a tamper-evident record
that the operator cannot later alter — not to distribute trust across
untrusted participants.

You do not need Byzantine fault tolerance to prevent an operator from
retroactively modifying a signed log entry. You need append-only semantics
and independent verifiability of the log structure. A Merkle log provides
both. Blockchain provides both plus Byzantine fault tolerance, which is
unnecessary overhead in this trust model.

Blockchain for evidence anchoring is the equivalent of using a distributed
consensus network to prevent someone from altering a signed PDF — technically
it prevents tampering, but so does a much simpler approach, and the added
complexity serves no purpose given the trust model.

### 3. Blockchain cannot meet OBO's timing requirement

The OBO Evidence Envelope MUST be submitted to the Evidence Anchor before the
transaction is considered complete (OBO-REQ-015). This is a protocol-level
requirement, not a preference — the evidence must be minted *before* the
action proceeds, ensuring the commitment exists regardless of what happens
after.

| Platform | Time-to-finality | Suitable for pre-action evidence? |
|----------|-----------------|-----------------------------------|
| Ethereum (PoS) | ~12 seconds | No |
| Bitcoin | ~10 minutes | No |
| Solana | ~0.4 seconds | Borderline; operator dependency |
| Hyperledger Fabric | 1–5 seconds (configured) | Borderline |
| Merkle log (OBO) | <100 ms | Yes |

Pre-action evidence commitment on a public blockchain is not feasible at
production transaction volumes. Permissioned blockchains can be tuned for
lower latency but then replicate the trust model of a private Merkle log
with significantly more operational complexity.

### 4. Public blockchains violate privacy requirements

Per-transaction evidence records submitted to a public blockchain create
a permanent, publicly queryable metadata trail: which operators are
processing which volumes of transactions, at what times, for which
domains. This is not acceptable for most enterprise and regulated deployments.

A private Merkle log with operator-controlled access to individual records,
and periodic epoch roots published in DNS, provides tamper-evidence without
public metadata exposure. Individual records are not visible from the epoch
root — only the log structure is.

### 5. Transaction fees are incompatible with per-transaction evidence

OBO requires one Evidence Anchor submission per transaction. At meaningful
production volumes (thousands of agent transactions per hour), gas fees on
public blockchains are prohibitive and non-deterministic. Merkle log
submissions have fixed, predictable cost.

### 6. DNS epoch anchoring provides decentralised finality without consensus

OBO's Merkle log does not require a blockchain for decentralised finality.
Evidence Anchor operators publish epoch roots to DNS TXT records:

```
_anchor-epoch-<N>.<anchor_domain> IN TXT "v=anchor1 root=<root> size=<n>"
```

DNS is globally distributed, independently queryable, and — like the CT log
list — can be cross-checked across multiple independent observers. An auditor
can independently verify that an epoch root exists in DNS and matches the
Merkle commitment in an Evidence Anchor receipt without trusting any single
party.

This is decentralised finality through DNS, not consensus. It is the same
mechanism CT uses when publishing signed tree heads that are included in
Chrome's CT policy enforcement list.

---

## The reference implementation and the production path

OBO provides a reference Evidence Anchor server (`anchor_stub/`) that
implements the full Evidence Anchor API. This server is deliberately minimal —
it proves the protocol works and is suitable for development, testing, and
low-volume deployments.

The production path for Evidence Anchor operators is not to run the reference
server at scale. The production path is:

1. **CT log operators** (Google, Cloudflare, Let's Encrypt, DigiCert) extend
   their existing Trillian-backed log infrastructure to accept OBO leaf
   submissions at a new endpoint (`POST /v1/evidence/mint`).

2. **Enterprise log operators** with existing append-only audit infrastructure
   (HSM-backed, SOC 2-certified) add an OBO-compatible submission and proof
   API.

3. **Independent trust operators** — analogous to CT log operators — emerge
   as neutral third parties that provide Evidence Anchor services for OBO
   deployments where operator self-anchoring would be a conflict of interest.

Google's Trillian (open-sourced 2016, Apache 2.0) is the reference
implementation of a production Merkle log at scale. It powers Google's CT
log operations and is designed as a general-purpose log backend. An
organisation running Trillian today can add OBO Evidence Anchor support
with a new submission handler and the OBO leaf schema — no infrastructure
investment beyond the development of that endpoint.

The reference server demonstrates the protocol. Trillian and its equivalents
are the production infrastructure.

---

## Independence requirement

Evidence Anchor operators SHOULD be independent of OBO credential operators
for Class C and D transactions. This mirrors the CT requirement that log
operators are independent of Certificate Authorities — a CA cannot be the
sole log for its own certificates, because the purpose of the log is to
detect CA misbehaviour.

For OBO: an operator that both issues credentials and exclusively anchors its
own evidence provides weaker accountability guarantees than an operator that
submits to an independent Evidence Anchor. Independent anchoring is not
mandated in the base spec (operators may run their own anchors for Class A/B),
but is RECOMMENDED for Class C/D and will be normative in future profile
specifications for regulated use cases.

---

## Consequences

**Positive:**
- No new infrastructure investment required for production operators — CT
  log operators already have the stack
- Sub-100ms evidence minting enables pre-action commitment
- Privacy by default — only epoch roots are public; individual records are not
- DNS epoch anchoring provides decentralised finality without consensus
- Operationally simple: no wallets, no gas, no consensus participation
- Directly analogous to a proven global-scale system (CT logs, 10+ years)

**Negative / watch points:**
- "Blockchain" is a more recognisable term in some audiences. The equivalence
  to CT logs (which are universally trusted) is the correct framing for
  technical audiences; "tamper-evident evidence log" is the correct framing
  for non-technical audiences.
- An Evidence Anchor operator that controls both the log and the epoch root
  DNS record could theoretically fork a private log. Independence of log
  operator and DNS domain control is a deployment best practice, not yet
  enforced by the spec.
- CT log operators are accustomed to logging certificates (pre-issuance
  events) not transaction outcomes (post-action events). The OBO schema is
  operationally similar but the commercial model for Evidence Anchor services
  does not yet exist. We assert it will emerge as regulatory requirements
  make accountable evidence mandatory — see `docs/EVIDENCE-INFRASTRUCTURE.md`.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Public blockchain (Ethereum, Solana) | Finality latency; transaction fees; public metadata exposure; Byzantine overhead not needed |
| Permissioned blockchain (Hyperledger Fabric) | Complex distributed system that replicates the trust model of a simpler Merkle log |
| IPFS content-addressed storage | Content addressing proves integrity but not ordering; no append-only semantics; no signed checkpoints |
| Traditional database with audit log | No independently verifiable tamper-evidence; requires trusting the database operator |
| W3C Verifiable Credentials Registry | Designed for credential issuance, not post-transaction evidence; no Merkle commitment model |
