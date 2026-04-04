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

### OpenID4VP — just use OpenID for Verifiable Presentations and pass the keys

OpenID4VP is a more sophisticated observation than plain OAuth — and it gets
closer. OpenID4VP defines how a holder presents W3C Verifiable Credentials to a
verifier via a signed Verifiable Presentation (VP), with key-binding proving the
presenter holds the key. OBO's DID profile (Appendix F) is compatible with this
ecosystem and the delegation chain and intent artifacts (§3.3, §3.4) could be
expressed as VCs. The VC/VP layer composes with OBO. But three gaps remain:

**1. The flow is backwards for machine-to-machine APIs.**
OpenID4VP assumes the verifier initiates — it sends a presentation request, the
holder's wallet responds. In OBO's scenario the calling agent initiates the
request (a flight search API call, a payment, a booking). There is no
presentation request. The credential travels with the task as proof of authority.
Requiring Ryanair's API to issue a VP challenge before every inbound agent call
— at scale, in milliseconds — does not fit the machine-to-machine interaction
pattern.

**2. A VP carries identity claims. It does not carry a scope fence.**
A Verifiable Presentation proves: *this holder has these attributes* ("KYC
verified", "operator registered"). It does not carry
`intent_hash = SHA-256("Book cheapest economy LHR→JFK 15 April")` — a
cryptographic commitment to the exact scope a specific human approved at a
specific time. The scope fence is the piece that answers the judge's question.
VP credential claims are not it.

**3. OpenID4VP ends at presentation. OBO continues to evidence.**
There is no equivalent in OpenID4VP to the OBO Evidence Envelope, the SAPP
Merkle anchoring, or the post-transaction checkpoint. The VP proves claims were
valid when presented. It does not produce a cryptographically anchored record
of what the agent did with them — verifiable offline, by a third party, six
months later in a dispute.

**The pattern:** OpenID4VP is the right answer for the credential presentation
layer. OBO is three layers simultaneously — presentation, scope-fencing, and
post-transaction evidence. OpenID4VP covers the first. None of the existing VC
standards cover the second or third.

**Use OpenID4VP** where you have a wallet model, a verifier-initiated
presentation flow, and VC-based identity infrastructure.
**Compose it with OBO** when you also need scope-fenced authorisation and
post-transaction evidence that survives a cross-jurisdictional dispute.

---

### DIDComm — use DID-based agent messaging, it handles cross-org agent communication

DIDComm is a serious protocol and closer than most. It defines encrypted,
signed messaging between DID-based agents, supports credential exchange via
WACI-PEx, and does not require a shared AS — key discovery happens via DID
Documents, which is philosophically similar to OBO's DNS-anchored key. The
gaps are infrastructure, scope, and evidence:

**1. Both parties must be DID-based.**
DIDComm requires sender and receiver to have DIDs and the infrastructure to
resolve them (a Verifiable Data Registry). Ryanair, Booking.com, and Hertz have
HTTPS APIs. They do not have DIDs, DID Documents, or DIDComm endpoints, and
will not in the near term. OBO requires only that the operator controls a domain
and can publish a DNS TXT record — infrastructure every operator already has.
An accountability standard that requires the entire travel, payments, and
healthcare industry to re-platform onto SSI infrastructure before the first
transaction can be verified is not a practical standard today.

**2. Still no scope fence.**
A DIDComm message can carry a Verifiable Presentation (see OpenID4VP entry
above), but the same gap applies: VPs carry identity and attribute claims, not
`intent_hash = SHA-256("Book cheapest economy LHR→JFK 15 April")`. DIDComm
defines the envelope; it does not define a cryptographic commitment to the
specific human-approved scope of a specific action.

**3. Still no post-transaction evidence.**
DIDComm is a messaging protocol. It does not define post-transaction evidence
records, Merkle anchoring, SAPP submission, or anything equivalent to the OBO
Evidence Envelope. The message proves a credential was presented. It does not
produce an independently verifiable record of what the agent did afterward.

**4. Synchronous API calls and mediators.**
DIDComm's async delivery model uses mediators for message routing — well-suited
for wallet-to-wallet credential exchange, less suited for synchronous API calls
where a response is expected in milliseconds. OBO attaches a credential to an
HTTPS request in a header or extension field; no routing infrastructure required.

**Use DIDComm** in SSI ecosystems where both parties are DID-based and
credential exchange is the primary interaction model.
**Compose it with OBO** when you also need to cross into non-DID infrastructure
and require post-transaction evidence.

---

### IETF GNAP (RFC 9635) — it's the modern successor to OAuth, it covers this

GNAP (Grant Negotiation and Authorization Protocol) is the most sophisticated
objection in the OAuth family. It is genuinely more expressive than OAuth 2.0:
key-based client authentication (no client_id/secret), structured access
requests, multi-step interactive grants, continuation tokens, and subject
information. It was designed explicitly to handle complex delegation scenarios
that OAuth 2.0 handles awkwardly. The same two fundamental gaps remain:

**1. GNAP still requires an Authorization Server.**
GNAP's interaction model is: client → AS (grant request) → AS decision →
access token → resource server. The AS is still the trust anchor. For the
cross-org case — TravelAgent calling Ryanair's API — the question is still
"whose AS?" Ryanair does not run a GNAP AS that TravelAgent can negotiate with.
lane2.ai's GNAP AS has no standing at Ryanair. GNAP makes the grant negotiation
richer; it does not eliminate the shared-AS prerequisite.

**2. Still no intent hash, still no post-transaction evidence.**
GNAP's `access` array carries structured authorisation details about what a
token is for — more expressive than OAuth `scope` strings, but still a
description of access rights, not a SHA-256 commitment to a specific
human-approved phrase. `principal_sig` — Alice's Ed25519 signature over
"Book cheapest economy LHR→JFK 15 April" at 11:54:58 — has no equivalent in
GNAP. And like all token-issuance protocols, GNAP ends when the token is issued.
There is no post-transaction evidence envelope, no Merkle anchoring, no record
for the judge.

**A note on OAuth RAR (RFC 9396 — Rich Authorization Requests):**
RAR adds a structured `authorization_details` parameter to OAuth/OIDC — the
closest thing to `intent_hash` in the OAuth ecosystem. It can carry fine-grained
authorisation details: type, actions, locations, identifiers. Still needs an AS.
Still carries the full structure (not a hash commitment to a canonical phrase).
Still no post-transaction evidence. RAR narrows the gap on scope expressiveness;
it does not close the AS dependency or the evidence gap.

**Use GNAP** for complex interactive grant flows within or across trust domains
that have compatible AS infrastructure.
**Use OBO** when no shared AS exists and post-transaction evidence is required.

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

---

## How technically sophisticated people arrive here

If you are reading this FAQ because someone sent you a link, you have probably
already had — or are about to have — a version of the following conversation.
Recognising where you are in it saves time.

Every technically sophisticated person who engages seriously with OBO goes
through the same arc. The steps are predictable because they follow the natural
order of existing expertise. Each step is correct on its own terms. The final
step is where OBO lives.

---

### Step 1 — "OAuth handles delegation"

**The instinct:** OAuth is the standard for delegated authorisation. If an agent
is acting on behalf of a user, use OAuth. `scope=flights:book` is the fence.

**Where it stops:** OAuth scope is negotiated at token issuance between parties
that share an Authorization Server. The AS is the trust anchor. Cross-org —
Ryanair, Booking.com, Ticketmaster, Hertz — there is no shared AS.
`scope=flights:book` does not encode *which* flight, *at what price*, *approved
by whom*, *at what time*. And OAuth produces no post-transaction evidence record.

---

### Step 2 — "RFC 8693 covers on-behalf-of specifically"

**The instinct:** RFC 8693 is the OAuth extension for on-behalf-of token
exchange. It even has `act` claims for delegation chains. This is exactly the
use case.

**Where it stops:** RFC 8693 §2.1 requires the client to exchange a token at
an AS. The AS issues the new delegated token. Whose AS? For N cross-org
operators, N×(N-1)/2 bilateral AS trust relationships are required, or a central
AS. Neither exists. RFC 8693 is the right answer inside a trust domain. The
cross-org case is the gap.

---

### Step 3 — "OpenID4VP — pass the keys and the verifiable presentation"

**The instinct:** OpenID4VP + W3C VCs solves cross-org key distribution without
a shared AS. The verifier knows the root authority (the VC issuer). The agent
presents a signed credential. The verifier validates the user's signature on the
mandate.

**Where it stops:** Three gaps remain. The flow is backwards for M2M APIs —
OpenID4VP requires the verifier to initiate a presentation request; at API scale
in milliseconds this doesn't fit. A VP carries identity and attribute claims,
not `intent_hash` — a cryptographic commitment to the exact scope the human
approved at the exact time. And OpenID4VP ends at presentation — no
post-transaction evidence envelope, no Merkle anchoring, no record for the
dispute six months later.

---

### Step 4 — "There is no single answer — compose technologies: W3C VC + OpenID4VP"

**The instinct:** You're right that no single existing standard covers it.
Combine them. W3C VC for portable identity. OpenID4VP for cross-org presentation.
Something else for the evidence trail.

**This is the arrival point.** This instinct is exactly correct.

OBO is that composition — specified, implemented, and running. The parts:

| What is needed | What OBO uses |
|---------------|--------------|
| Cross-org operator identity without shared AS | DNS-anchored Ed25519 key (`_obo-key.<domain>`) |
| Scope fence: what the human approved | `intent_hash = SHA-256(exact phrase)` in credential |
| Human approval proof (Class C/D) | `principal_sig` in Intent Artifact (§3.4) |
| Post-transaction evidence | Evidence Envelope, signed, Merkle-anchored in SAPP |
| Composability with W3C VCs / DIDs | DID Profile (Appendix F), `kyc_ref` in Intent Artifact |

The "root authority that verifies the agent" in Step 3 is
`_obo-key.lane2.ai IN TXT "v=obo1 ed25519=…"`. Any counterparty resolves it in
one DNS lookup. No issuer registry. No enrollment. No shared infrastructure.

The DNS key is live. The reference implementation runs. The evidence captures
are in the repo.

---

### Why the journey takes four steps

The existing standards were designed for **systems calling systems** within
established trust relationships — where the AS is known in advance, the scope
is negotiated at enrollment, and the parties have a prior relationship.

OBO is designed for **agents acting for humans at runtime** — where the
counterparty is unknown in advance, the scope is what a specific human approved
minutes ago, and the accountability record must survive a dispute months later
in a different jurisdiction.

That is not an incremental extension of the existing model. It is a different
layer. Experts who have built the existing layer well — and they have built it
well — need four steps to see that the layer doesn't exist yet, not that they
built the wrong thing.

Every step of the journey is valid expertise applied to the wrong problem
boundary. Step 4 is where the boundary becomes visible.
