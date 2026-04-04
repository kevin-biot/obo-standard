# OBO Use Cases

This document shows OBO applied to concrete, real-world scenarios available
today. Each case describes who the parties are, what action class applies, what
goes in the credential, and what the evidence proves — and contrasts the
before-OBO and after-OBO situations.

The scenarios are organised by action class to show how the accountability
requirement scales with the risk of the action.

---

## The core assumption: no Authorization Server between the agents

**OBO is designed for the case where there is no pre-existing Authorization
Server (AS) in the interaction path between agents.**

If an AS is present — an OAuth 2.0 authorisation server, an OpenID Connect
provider, an enterprise identity broker — then standard OAuth / OIDC flows
already handle token issuance and scope enforcement between the parties. Use
them. OBO does not replace OAuth. In an environment where the agents are
already enrolled in a shared AS, the right tool is OAuth Token Exchange
(RFC 8693) or a similar delegated token flow.

**OBO fills the gap when no shared AS exists.** This is the common case for:

- **Cross-organisation agent interactions** — TravelAgent (lane2.ai) calling
  FlightSearchAgent (another operator). There is no shared OAuth AS between
  them; neither has pre-registered with the other's identity infrastructure.
- **Ad-hoc agent-to-agent calls** — a newly deployed agent calling a service
  it has never contacted before, with no prior enrollment.
- **Consumer agents calling commercial APIs** — a personal assistant calling a
  booking or data service without an enterprise identity broker in the path.
- **Multi-hop delegation chains** — authority passed across three or more
  operators, each potentially in a different trust domain, with no single AS
  that spans all of them.

In these situations, the only trust anchor available at interaction time is what
is publicly verifiable — which is exactly what DNS-anchored operator keys
provide.

### When OBO and OAuth coexist

OBO and OAuth are composable. A common pattern in enterprise deployments:

```
Human principal
    │
    │  authenticates via OIDC / enterprise IdP (OAuth AS present)
    ▼
Operator agent  ──── OAuth access token ────►  Internal enterprise APIs
    │
    │  no shared AS with external service
    ▼
OBO credential  ─────────────────────────────►  External agent / service
```

The internal leg uses OAuth because both parties share an AS. The external leg
uses OBO because they do not. The OBO credential carries the operator's
Ed25519-signed proof of authority; the receiving external agent verifies it via
DNS without needing to enroll with the operator's IdP.

This is also the pattern described in §8 of the spec ("Relationship to Existing
Standards"): OBO adds the accountability layer that OAuth was not designed to
provide, specifically for agentic interactions where pre-shared trust
infrastructure does not exist between the parties.

---

## Class A — Read-only, informational

*The agent reads data. No side effects. Accountability is about transparency,
not liability.*

---

### A1. Personal assistant reads your calendar to check availability

**Parties:** User (principal) → Personal assistant agent (operator) → Calendar
service (verifier)

**Scenario:** Alice asks her AI assistant to find a meeting slot next week.
The assistant queries her work calendar service, which holds sensitive scheduling
data including external party names and meeting topics.

**Before OBO:** The calendar service has no way to distinguish Alice's assistant
from any other API client using Alice's OAuth token. If the token is misused,
the audit trail shows "Alice's token" — not which agent used it, for what
purpose, or whether Alice explicitly asked it to.

**After OBO:**

```json
{
  "credential_id": "urn:obo:cred:…",
  "operator_id":   "assistant.example.com",
  "principal_id":  "did:key:z6Mk…",
  "action_class":  "A",
  "intent_hash":   "SHA-256('Find a free 1-hour slot next week for a 30-minute call')",
  "not_after":     "2026-04-04T12:05:00Z"
}
```

The calendar service verifies the credential and knows: Alice's assistant (not
Alice directly) made this query, on Alice's explicit instruction, for the stated
purpose, within a 5-minute window. The evidence envelope records the outcome.
If the query returns data it should not, the audit trail is unambiguous.

**Value:** Transparency and delegation traceability, even for low-risk reads.
No additional friction for the user.

---

### A2. Market data agent queries pricing feed

**Parties:** Trading firm (operator) → Price discovery agent → Market data
service (verifier)

**Scenario:** An automated agent queries a real-time pricing feed to inform
a trading strategy. The feed provider charges per-query and monitors for
excessive or suspicious access patterns.

**Before OBO:** The provider sees API key + volume. If the trading firm is
compromised and a rogue agent runs excessive queries, the audit trail shows
only the API key.

**After OBO:** Each query carries a credential with `intent_hash` bound to the
specific query context. Unusual volume or off-strategy queries are attributable
to a specific agent and intent — not just an API key. The feed provider can
enforce intent-class limits and flag deviations.

---

## Class B — Write, reversible

*The agent changes state, but the change can be undone. Accountability is about
who authorised the write — important but not legally critical.*

---

### B1. Concierge agent books a restaurant reservation

**Parties:** User (principal) → Concierge agent (operator) → Restaurant booking
service (verifier)

**Scenario:** Bob asks his concierge agent to book a table for four at a
specific restaurant next Saturday. The booking can be cancelled; no payment is
taken at reservation time.

**Before OBO:** If the agent books the wrong restaurant, the wrong date, or
makes a booking Bob didn't ask for, there is no cryptographic record of what
Bob actually requested.

**After OBO:**

```json
{
  "action_class": "B",
  "intent_hash":  "SHA-256('Book a table for 4 at Osteria Mozza on Saturday 11 April at 7pm')"
}
```

The booking service verifies the credential. The evidence envelope records:
`obo_intent_hash`, `obo_outcome: allow`, the task reference. If there is a
dispute ("I didn't ask for that restaurant"), the intent hash is the
cryptographic record of what Bob approved.

**Value:** Disputes resolved with evidence, not recollection. The agent is
accountable for executing exactly the stated intent.

---

### B2. DevOps agent merges a pull request

**Parties:** Developer (principal) → CI/CD agent (operator) → Version control
service (verifier)

**Scenario:** A developer approves an AI agent to merge a PR after checks pass.
The merge is reversible (revert commit), so Class B applies.

**Before OBO:** The merge appears as the developer's action in git history —
even though an agent did it. If the wrong PR is merged, there is no record of
whether the developer explicitly authorised this specific PR.

**After OBO:**

```json
{
  "action_class": "B",
  "intent_hash":  "SHA-256('Merge PR #4821 (add-payment-gateway) after all CI checks pass')"
}
```

The VCS verifier checks the credential, verifies the intent hash matches the
specific PR, and only permits the merge for that exact PR. A rogue agent cannot
use the same credential to merge a different PR. The audit trail shows the
developer's explicit per-PR authorisation, not just their token.

---

## Class C — Write, irreversible

*The action cannot be undone. Accountability is essential — and for some
industries, legally required.*

---

### C1. Travel agent books a non-refundable flight *(reference implementation)*

**Parties:** Alice (principal) → TravelAgent (operator, `lane2.ai`) →
FlightSearchAgent (verifier)

**Scenario:** Alice asks TravelAgent to book the cheapest economy flight from
LHR to JFK on 15 April. The ticket is non-refundable. Once booked, the seat is
gone.

**This is the scenario demonstrated in `examples/integrations/a2a/`.** The
full evidence chain is in `examples/integrations/a2a/captures/`.

**Before OBO:** FlightSearchAgent receives a task from TravelAgent via A2A. It
has no way to verify that Alice approved this specific booking, or that
TravelAgent is authorised to book on Alice's behalf, or that TravelAgent's
identity is what it claims.

**After OBO:**

```json
{
  "action_class": "C",
  "intent_hash":  "SHA-256('Book cheapest economy flight LHR→JFK 15 April')",
  "credential_sig": "Ed25519(canonical fields, lane2.ai private key)"
}
```

FlightSearchAgent:
1. Resolves `_obo-key.lane2.ai` from DNS → Ed25519 public key
2. Verifies `credential_sig`
3. Verifies `intent_hash` matches the presented intent phrase
4. Checks action class C is permitted for booking endpoint
5. Executes the booking
6. Receives evidence bundle from SAPP (`checkpoint_index: 0`, `merkle_root: …`)

The Merkle root commits to all 14 evidence leaves. The booking is
cryptographically attributed to Alice's explicit instruction and TravelAgent's
verified identity.

**With full Class C evidence (§3.3 + §3.4, future `--rich` mode):**
The delegation chain proves TravelAgent was authorised by the operator to act
for Alice. The Intent Artifact carries Alice's `principal_sig` over the exact
phrase and her authorisation timestamp. A travel insurer handling a dispute can
verify both.

---

### C2. Healthcare agent books a non-cancellable specialist appointment

**Parties:** Patient (principal) → Health assistant agent (operator) →
Hospital booking system (verifier)

**Scenario:** A patient's health assistant books a specialist appointment that
carries a cancellation fee. The appointment slot is taken; partial refund only.

**Before OBO:** The booking system knows the patient's account was used. It
cannot verify whether the patient explicitly approved this specific appointment
or whether an agent acted autonomously.

**After OBO:**

```json
{
  "action_class": "C",
  "intent_hash":  "SHA-256('Book appointment with Dr Reyes oncology 22 April 14:00')",
  "principal_id": "did:key:z6Mk…"
}
```

The Intent Artifact (§3.4) carries:
- `phrase`: the exact appointment request as the patient approved it
- `principal_sig`: the patient's Ed25519 signature over the phrase
- `intent_authorised_at`: timestamp of patient approval

If the patient later claims they didn't book this appointment, the `principal_sig`
in the Intent Artifact is the proof. The hospital has an accountable record that
satisfies their data governance requirements.

---

## Class D — Regulated, high-value

*The action is subject to a regulatory regime. Full accountability chain required:
delegation proof, explicit human approval, identity verification.*

---

### D1. Payment agent initiates a wire transfer (PSD2 / Open Banking)

**Parties:** Account holder (principal) → Payment orchestration agent (operator)
→ Bank API (verifier)

**Scenario:** An enterprise payment agent initiates a £47,250 wire transfer to
a supplier. Under PSD2 Article 74, the bank must verify Strong Customer
Authentication and maintain an audit trail of the authorisation.

**Before OBO:** The bank verifies the OAuth token and SCA (via FIDO2 or OTP).
The audit trail shows a payment was authorised at a specific time. But if the
payment was initiated by an AI agent — not the account holder directly — the
bank's audit trail has no record of which agent, under what authorisation, with
what intent phrase, or whether the account holder explicitly approved this
specific transfer.

**After OBO (Class D):**

```
Credential:
  action_class: D
  intent_hash:  SHA-256("Transfer £47,250 to GB29NWBK60161331926819, ref INV-20482")
  principal_id: did:key:z6Mk…  (account holder DID)

Delegation Chain Artifact (§3.3):
  Acme Corp → payment agent, scope: transfers ≤ £50,000 economy class

Intent Artifact (§3.4):
  phrase:                   "Transfer £47,250 to GB29NWBK60161331926819, ref INV-20482"
  principal_sig:            Ed25519(CFO's key, phrase)
  intent_authorised_at:     2026-04-04T11:54:58Z
  authorisation_method:     explicit_approval
  kyc_level:                enhanced
  kyc_ref:                  jumio-kyc-abc123
  biometric_method:         face_id
  biometric_score:          0.987
```

The bank receives:
- Cryptographic proof the CFO signed this specific transfer
- Proof the agent's delegation scope covers this amount
- KYC and biometric evidence acceptable under PSD2 Art. 74
- A SAPP merkle_root committing the full 30-leaf evidence set

One hash. Everything in it. Nothing can be presented or withheld independently.

**Regulatory value:** Satisfies PSD2 Art. 74 SCA requirements, EU AI Act
Art. 12 transparency obligations, and is legally producible in a payment
dispute without additional reconstruction.

---

### D2. Legal agent executes a contract clause

**Parties:** In-house counsel (principal) → Legal AI agent (operator) →
Contract management system (verifier)

**Scenario:** A legal AI agent is authorised to execute a specific contract
amendment on behalf of in-house counsel. Contract execution is irreversible and
has legal effect.

**After OBO (Class D):**

The Intent Artifact carries:
- The exact clause text as counsel approved it (`phrase`)
- Counsel's `principal_sig` — their Ed25519 signature is the digital equivalent
  of their signature on the document
- The timestamp of approval and the identity verification method

The delegation chain proves the agent was authorised to act within the defined
scope (this contract, this clause). The evidence envelope records the outcome.

A court receiving a dispute about whether this amendment was authorised has a
complete, cryptographically verifiable chain: identity → delegation → explicit
approval → execution record. No reconstruction required.

---

### D3. Infrastructure agent terminates a production database

**Parties:** SRE team lead (principal) → Infrastructure agent (operator) →
Cloud control plane (verifier)

**Scenario:** During an incident, an infrastructure agent is authorised to
terminate a compromised production database. The action is irreversible (data
loss), has regulatory implications (GDPR breach notification may be triggered),
and requires explicit human approval under the organisation's change management
policy.

**Before OBO:** The cloud control plane logs show the agent's API key initiated
the termination. If the action was unauthorised or exceeded scope, there is no
cryptographic record of who approved what.

**After OBO (Class D):**

```json
{
  "action_class": "D",
  "intent_hash":  "SHA-256('Terminate RDS instance prod-db-3 in eu-west-1, incident INC-4821')",
  "principal_id": "did:key:z6Mk…"
}
```

The Intent Artifact carries the SRE team lead's `principal_sig` over the exact
instance identifier and incident reference. No agent can substitute a different
database — the `intent_hash` binds the credential to this specific termination.

Post-incident, the compliance team has a SAPP-anchored evidence record that
proves: who approved it, what was approved, when, under what delegation scope,
and what happened. The regulatory breach notification includes the cryptographic
evidence reference.

---

## The two-agent first contact problem

All nine scenarios above share a common challenge: **two agents that have never
interacted before must establish trust quickly, with no pre-shared secrets and
no shared Authorization Server.**

Before OBO, the only options without a shared AS were:
- Pre-register every agent pair out-of-band (doesn't scale)
- Use a centralised directory (single point of failure, governance overhead)
- Trust on assertion (no accountability)
- Require every external service to enroll with the calling agent's AS
  (operationally impossible at scale across organisations)

After OBO, the pattern is the same in every case:
1. Receiving agent fetches calling agent's Agent Card → discovers OBO requirement
2. Calling agent presents an OBO credential signed by its operator
3. Receiving agent resolves the operator's public key from DNS
4. Verification is purely cryptographic — no phone calls, no pre-registration,
   no shared identity infrastructure

This is what "zero infrastructure" means in the OBO framing: neither party needs
to have met before, and neither party needs to share an AS or trust a
third-party directory. The operator's domain control (proven by DNS TXT record
publication) is the only prerequisite.

**If a shared AS does exist between the parties, use it.** OBO is not a
replacement for OAuth in environments where OAuth already works. OBO is the
answer to "what do we do when it doesn't."

---

## Summary table

| # | Scenario | Class | Key accountability question answered |
|---|----------|-------|--------------------------------------|
| A1 | Calendar availability check | A | Which agent read this data, for what purpose? |
| A2 | Market data query | A | Was this query within the agent's authorised scope? |
| B1 | Restaurant reservation | B | Did the user approve this specific booking? |
| B2 | PR merge | B | Did the developer authorise this specific PR? |
| C1 | Non-refundable flight | C | Operator identity + intent binding (live demo ✅) |
| C2 | Hospital appointment | C | Did the patient sign off on this specific slot? |
| D1 | Wire transfer | D | Full PSD2-compliant audit chain including SCA evidence |
| D2 | Contract execution | D | Legally producible authorisation + identity proof |
| D3 | Production DB termination | D | Who approved what, exactly, for post-incident compliance |

The action class determines the verification requirement. The verification
requirement determines the evidence artifacts needed. The evidence artifacts
are all committed into one `merkle_root`. One hash, auditable by anyone.
