# FAQ

Short answers to the questions that come up most. If you have time for more
detail, the linked ADRs and spec sections go deeper.

---

## "But doesn't X already do this?"

---

### RFC 8693 — OAuth 2.0 Token Exchange already covers on-behalf-of delegation

RFC 8693 is exactly right when there is a shared Authorization Server both
parties already trust. §2.1 requires the client to exchange a token at an AS
and receive a new one with delegation claims. The problem: Ryanair doesn't trust
lane2.ai's AS, and lane2.ai has no account at Ryanair's AS. For N operators you
need N×(N-1)/2 bilateral AS trust relationships, or a central AS — OBO avoids
both. The DNS-anchored credential is verifiable by any counterparty with no
prior enrollment and no shared infrastructure.

Additionally: RFC 8693 is about token issuance, not post-transaction evidence.
There is no equivalent to the evidence envelope, `intent_hash` scope-fencing,
or Merkle anchoring. The question "show me the scope at signing time, offline,
without calling anyone" is not answered by 8693.

**Use RFC 8693** inside a trust domain where both parties share an AS.
**Use OBO** when they don't.

See also: [The core assumption in USE-CASES.md](USE-CASES.md#the-core-assumption-no-authorization-server-between-the-agents)

---

### OAuth 2.0 handles delegation and scope

OAuth handles delegation well within a trust domain. The `scope` parameter
fences what a token can do. But OAuth scope is a string negotiated at token
issuance — it is not a cryptographic commitment to a specific human-approved
intent phrase, and it does not survive crossing an organisational boundary
without a shared AS. An OAuth access token for `scope=flights:book` does not
tell the receiving service which flight, at what price, approved by whom, at
what time. `intent_hash = SHA-256("Book cheapest economy LHR→JFK 15 April")`
does. The evidence envelope records what actually happened. OAuth produces
neither.

---

### WIMSE / SPIFFE gives every workload a strong identity

Yes, and that solves the within-org problem cleanly. SPIFFE SVIDs are
cryptographically strong workload identities that work well inside an
organisation's infrastructure. The gap: a SPIFFE certificate issued by
company A's SPIRE server has no verifier at company B. There is no cross-org
SPIFFE trust federation in the general case. OBO carries the operator's
identity *across* the trust domain boundary using DNS as the common ground —
any counterparty can resolve `_obo-key.<operator_id>` without enrolling with
the operator's identity infrastructure.

WIMSE and OBO are complementary: WIMSE for intra-org workload identity, OBO
for the cross-org accountability layer.

---

### W3C Verifiable Credentials are designed for exactly this

W3C VCs are portable, cryptographically signed identity and attribute claims —
well-suited for carrying "Alice is KYC-verified at enhanced level." OBO uses
compatible primitives (Ed25519, DIDs in Appendix F) and the Intent Artifact
(§3.4) can reference VC-backed `kyc_ref` evidence. The gap: VCs carry
*claims about identity*, not a scope-fenced authorisation for a specific action
plus post-transaction evidence. A VC does not contain `intent_hash`. A VC is
not committed into a Merkle root alongside the transaction outcome. OBO and
W3C VCs compose — they solve adjacent problems.

---

### A2A (Agent-to-Agent protocol) handles inter-agent communication

A2A defines how agents discover each other (Agent Cards), exchange tasks, and
stream results. It is a transport and task protocol. It does not define what
evidence an agent must present to be trusted, how the receiving agent verifies
the presenting agent's authority, or how the transaction is recorded for audit.
OBO plugs into A2A at the `extensions` field of `TaskSendParams` — A2A carries
the task, OBO carries the accountability. See
`examples/integrations/a2a/` for the reference implementation.

---

### mTLS / client certificates prove the agent's identity

A certificate proves the agent signed. It does not prove what the agent was
permitted to sign. When the dispute arises and the judge asks "show me the scope
of the delegation" — a certificate is silent. OBO adds the scope fence:
`intent_hash` commits to the exact authorised phrase, `action_class` sets the
ceiling, `principal_sig` records the human's explicit approval. The certificate
(or DNS-anchored key) is still there answering "who is this?" — OBO answers
"what were they allowed to do?"

See [The Scope Problem](THE-SCOPE-PROBLEM.md) for the full argument.

---

### Just use audit logs — every system already logs everything

Logs are mutable. A log entry saying "agent booked first class flight" can be
edited, deleted, or never written. Even immutable logs (append-only, tamper-
evident) are typically controlled by one party — the operator — which means the
operator can omit entries or the log can be lost in an incident. OBO evidence is
different: the `envelope_sig` is produced by the acting operator *and* committed
into a SAPP Merkle root *and* (in production) anchored by a second independent
party (the SAPP operator's EdDSA JWS over the checkpoint). No single party can
alter or suppress the record after the fact. Logs tell you what happened.
OBO evidence proves it.

---

## "Why not just..."

---

### Why not a central OBO registry for operator keys?

A central registry is a single point of failure, a governance bottleneck, and
an enrollment prerequisite that excludes operators who haven't registered. DNS
gives every operator that controls a domain an immediate, self-sovereign way to
publish their key. No permission required. No registry to be unavailable at the
wrong moment. Key rotation is under the operator's control, propagates in
seconds, and requires no third-party coordination.

See [ADR-001](adr/ADR-001-dns-trust-anchor.md) for the full rationale.

---

### Why not require human approval for every agent action?

OBO is the accountability layer, not the gating layer. For Class A and B
actions (read-only, reversible), requiring synchronous human approval defeats
the purpose of an agent. The value of OBO for Class A/B is the audit trail —
the record that a human *did* delegate, and the agent *did* stay within scope —
without requiring the human to approve every individual action in real time.
For Class C/D (irreversible, regulated), OBO does require explicit human
approval via `principal_sig` in the Intent Artifact. The action class determines
the approval requirement. Not every action needs synchronous HITL; every action
needs an accountable record.

---

### Why not just encrypt the agent's communications?

Encryption protects content in transit. It does not prove scope, it does not
prove a human approved the action, and it does not produce a post-transaction
record verifiable by a third party. An encrypted channel between TravelAgent
and Ryanair tells an auditor nothing about whether the booking was authorised.
OBO operates at the application layer above transport security — it assumes
TLS is present and adds the accountability layer that TLS was not designed
to provide.

---

### Why Ed25519 and not RSA / ECDSA?

Short answer: smaller keys, no padding oracle risk, deterministic signatures,
and no algorithm negotiation that can be gamed. A 43-character base64url string
in a DNS TXT record is the entire public key. No padding oracle attack exists
for Ed25519. The same message and key always produce the same signature —
removing the class of attacks from weak randomness that has broken ECDSA
deployments in practice.

See [ADR-002](adr/ADR-002-ed25519-only.md) for the full rationale.

---

## "What about..."

---

### What if DNS is compromised?

DNS cache poisoning is a real attack vector and OBO acknowledges it. Mitigations:
short TTL (60–300 s for operator keys), DNSSEC where the zone is signed, and
for Class C/D — the most valuable transactions — §8.6 requires verifiers to
maintain a curated registry of known counterparties and use DNS as a trip-wire
rather than the sole check. A compromised DNS response causes a transaction
denial (fail-closed), not a false allow — unless the attacker can also forge
an Ed25519 signature with the substituted key, which requires breaking the
key, not just the DNS record.

---

### Is this GDPR / privacy compliant?

The credential carries `intent_hash = SHA-256(intent_phrase)`, not the phrase
itself. A hash reveals nothing about the content of the intent to parties
that handle the credential. The full phrase travels only in the Intent Artifact
(§3.4), which is disclosed only to parties that require it for Class C/D
verification. Identifiers use DIDs or operator domains rather than personal
data. §10 of the spec covers minimum disclosure, identifier construction, intent
phrase minimisation, and the E.4b suffix privacy circuit for DNS-published
corridor predicates.

See [ADR-006](adr/ADR-006-intent-hash.md) for the intent hash privacy rationale.

---

### What if the operator's private key is stolen?

Rotate immediately: generate a new key pair, update the DNS TXT record, wait
one TTL for propagation. New credentials issued after the rotation are valid;
any credential signed with the compromised key will fail verification once the
DNS record no longer contains that key. There is no revocation mechanism in the
current spec (v0.3.x) — rotation via DNS is the primary mitigation. For Class
C/D operators, HSM storage (FIPS 140-2 Level 3) and short credential TTLs
(minutes) limit the blast radius of a key compromise.

---

### Does OBO replace OAuth, WIMSE, W3C VCs, or A2A?

No. OBO adds the cross-org accountability layer that none of them were designed
to provide. The composition table from §8 of the spec:

| Standard | What it provides | Where OBO adds |
|----------|-----------------|----------------|
| OAuth 2.0 / RFC 8693 | Token delegation within a shared AS | Cross-org, no-shared-AS case |
| WIMSE / SPIFFE | Strong workload identity intra-org | Cross-org boundary crossing |
| W3C Verifiable Credentials | Portable identity and attribute claims | Scope-fenced action authorisation + evidence |
| A2A | Agent discovery, task transport | Pre-transaction trust + post-transaction evidence |
| HTTP Message Signatures RFC 9421 | Request integrity | Intent binding, delegation proof, outcome record |

Use the right tool for each layer. OBO is one layer — the accountability layer
for cross-org agentic transactions. It is designed to compose with all of the
above, not to replace any of them.
