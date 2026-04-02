# OBO — On Behalf Of: Minimum Evidence Standard for Agentic Transactions

**draft-lane2-obo-agentic-evidence-envelope-00**
Status: Working Draft · Seeking contributors and implementation experience

---

## The problem

A person asks their agent to plan a trip: book a flight, reserve a hotel,
get concert tickets, arrange a car, initiate the payment. Five organisations.
Possibly three countries. None of them have ever met this agent before.
No shared infrastructure. No common authorisation server. No prior relationship.

Each of those five organisations needs to answer the same four questions
before they act on the agent's instruction:

1. **Who are you, and who sent you?**
2. **What are you authorised to do?**
3. **What did you actually do?**
4. **Can I prove all of this to a regulator after the fact, without calling anyone?**

OBO emerged from a working implementation, not a specification exercise.
The fields exist because a real agentic pipeline required them when
crossing organisational boundaries with no shared infrastructure. The
gaps it fills are the gaps that appeared under load, not in a committee
room.

**The single-organisation case is already solved.** When one company controls
everything — its own AS, its own agents, its own APIs — OAuth, WIMSE, and
SPIFFE work well. That is not the growth area.

**The growth area is cross-organisation, cross-border, no shared AS.** A
travel agent booking on Ryanair, Booking.com, Ticketmaster, and Hertz has
no common authorisation server with any of them. A healthcare agent crossing
NHS and a private clinic crosses jurisdictions. A payment agent initiating a
SEPA transfer and settling in a different currency crosses regulatory regimes.

**Correspondent banking is the oldest version of this problem.** HSBC London
sends a SWIFT pacs.008 to Deutsche Bank Frankfurt, which forwards to JPMorgan
New York, which settles at Emirates NBD Dubai. Four jurisdictions. Four legal
entities. No shared authorisation server. No prior relationship between the
originating corporate and the receiving bank. SWIFT solved the message format.
It did not solve the evidence problem: who authorised the instruction, under
what governance, to what scope, and can any party in the chain prove it offline
without calling the originator? That is precisely what OBO Evidence Envelopes
address — and why SWIFT member institutions have been invited to contribute to
the [ISO 20022 profile](profiles/payments-swift-iso20022.md).

In every one of those cases, existing standards fail at question 4:

- **OAuth** answers 1 and 2 — but requires a live authorisation server both
  parties trust. When there is no shared AS, there is no verification.
- **WIMSE / SPIFFE** provide strong workload identity within a trust domain —
  but a trust domain boundary is exactly what cross-org agentic commerce crosses.
- **W3C Verifiable Credentials** answer 1 — but cover identity claims, not
  per-transaction evidence of what happened and what scope was exercised.
- **A2A agent protocols** enumerate tool surfaces — but do not prove bounded
  execution or produce tamper-evident post-transaction records.

---

## The solution

OBO answers all four questions with two artefacts:

```
OBO Credential        — carried by the agent before the transaction
                        answers: who, authorised for what, under whose governance

OBO Evidence Envelope — sealed by the agent after the transaction
                        answers: what happened, within what scope, tamper-evident
```

Both artefacts are verifiable **offline, without contacting any central
service**, by anyone who can resolve DNS — including organisations that
have never met the agent, share no infrastructure with its operator,
and are in a different jurisdiction.

> **DNS as the universal trust anchor.** Every organisation on the
> internet can resolve DNS. No shared AS required. No pre-registration.
> No approved network. Operator signing keys, governance pack digests,
> corridor admission predicates, and nullifier epoch roots are published
> as DNS TXT records — the same infrastructure pattern DKIM has used for
> email trust for twenty years.
>
> ```
> operator key  →  _obo-key._domainkey.<operator>
> governance    →  _obo-gov.<version>.<operator>
> corridor gate →  _obo-crq.<corridor-id>.<corridor>
> nullifier     →  _obo-null.<epoch>.<corridor>
> ```
>
> Ryanair does not need a trust relationship with your agent's operator.
> It needs DNS. That is already solved.

---

## The two artefacts

### OBO Credential (pre-transaction)

Minimum required fields:

| Field | What it answers |
|---|---|
| `principal_id` | Who delegated authority to the agent |
| `agent_id` | Which agent is acting |
| `operator_id` | Who operates the agent (may differ from principal) |
| `binding_proof_ref` | Proof of the principal→agent delegation |
| `intent_namespace` | The governed scope the agent may act within |
| `action_classes` | Severity ceiling: A (read) through D (irreversible) |
| `governance_framework_ref` | Machine-readable policy and ontology pack |
| `issued_at` / `expires_at` | Time bounds |
| `issuer_id` | Who signed this credential |
| `credential_digest` | Tamper detection |

### OBO Evidence Envelope (post-transaction)

Minimum required fields:

| Field | What it answers |
|---|---|
| `evidence_id` | Unique identifier for this evidence record |
| `obo_credential_ref` | Which credential authorised this transaction |
| `principal_id` / `agent_id` | Repeated for standalone verifiability |
| `intent_hash` | SHA-256 of the normalised intent — binds evidence to intent |
| `intent_class` | Governed intent category |
| `action_class` | Actual severity class executed |
| `outcome` | allow / deny / escalate / error |
| `policy_snapshot_ref` | Policy under which the action was evaluated |
| `sealed_at` | When the envelope was sealed |
| `evidence_digest` | Tamper-evident digest of the envelope |

Full field definitions, optional fields, and profiles are in the
[specification](draft-obo-agentic-evidence-envelope-00.md).

---

## DNS anchoring — how verification works

OBO Credentials are verified against signing keys published in DNS:

```
_obo-key._domainkey.<operator-domain>   TXT
  "v=obo1; k=ed25519; p=<base64url-public-key>"
```

No authorisation server contact required at verification time.
No CA. No registry. DNS only. This is precisely the DKIM pattern —
proven at internet scale for twenty years.

See [Appendix D](draft-obo-agentic-evidence-envelope-00.md#appendix-d-dns-anchoring-profile)
for the full DNS Anchoring Profile: key publication, governance pack
digest anchoring, nullifier epoch roots, and agent domain control proofs.

---

## Corridor admission predicates

Governed corridors (routing layers between agents) publish their admission
requirements in DNS:

```
_obo-crq.<corridor-id>.<corridor-domain>   TXT
  "v=obo1-crq; tier=regulated; ns=urn:obo:ns:payments;
   rtgf-required=true; rtgf-issuer=rtgf.regulator.example"
```

An agent resolves this record before attempting corridor admission. It knows
exactly what proofs to assemble. No probing. No opaque rejections. Machine-readable,
jurisdiction-aware, proof-based membership — no approved network required.

---

## Action classes

| Class | Severity | Examples |
|---|---|---|
| A | Read-only | Balance enquiry, availability check |
| B | Reversible write | Reservation, draft order |
| C | Irreversible write | Confirmed booking, data submission |
| D | Systemic | Payment initiation, consent grant, legal instruction |

The agent declares its maximum class in the credential. Each transaction
records the actual class in the evidence envelope. Verifiers reject
envelopes where the actual class exceeds the declared ceiling.

---

## Profiles

Base envelope profile types:

- **Regulated lane** — adds `why_ref` rationale chain for EU AI Act / PSD3 compliance
- **Local / offline** — credential verifiable without network access
- **Corridor-bound** — corridor co-signs the evidence envelope
- **Multi-step** — each step has its own envelope; steps chain via `prior_evidence_ref`
- **DNS anchoring** — operator key, governance pack, nullifier root, domain control proof

Named jurisdiction and scheme profiles (with conformant JSON examples):

| Profile | Scenario | Examples |
|---|---|---|
| [payments-mastercard-vi](profiles/payments-mastercard-vi.md) | Mastercard Verifiable Intent, SEPA credit transfer, PSD3 | [payment-lifecycle/](examples/envelopes/payment-lifecycle/) |
| [payments-swift-iso20022](profiles/payments-swift-iso20022.md) | SWIFT pacs.008, four-bank correspondent chain, UETR threading | [swift-correspondent/](examples/envelopes/swift-correspondent/) |

Contributions invited: NHS, UAE CBUAE, US ACH, cross-border RTGS.
See [profiles/README.md](profiles/README.md).

---

## How it works today — and where OBO fits

This is how the open internet already works. No changes required
downstream.

### The existing model — anonymous user, travel site, Amadeus

A user visits a travel site anonymously. They refuse to register.
The travel site finds flights and hotels and completes the booking:

```
User (anon)  ──→  travel site  ──→  Amadeus API       (site's own creds)
                               ──→  hotel booking API  (site's own creds)
                               ──→  payment PSP        (site's own creds)
```

The user is anonymous to Amadeus, the hotel, and the PSP. The travel
site is the accountable entity — it holds the relationships, the
contracts, and the credentials. This model works. It has worked for
twenty-five years. OBO does not change it.

### Add an agent — one new layer, nothing downstream changes

The user asks their agent to plan the same trip:

```
User (anon)
     │
     │  delegates to agent
     ▼
Agent carries OBO Credential
  — who sent me (operator_id)
  — what I'm allowed to do (action_classes A+B)
  — under whose governance (governance_framework_ref → PACT pack)
  — expires in 1 hour
     │
     │  approaches travel site
     ▼
Travel site verifies OBO Credential via DNS
  — no registration required
  — no prior relationship required
  — no shared AS required
  — DNS lookup: _obo-key._domainkey.<operator>  →  Ed25519 public key
  — credential valid: proceed
     │
     ├──→  Amadeus API       (site's own creds — UNCHANGED)
     ├──→  hotel booking API (site's own creds — UNCHANGED)
     └──→  payment PSP       (site's own creds — UNCHANGED)
                │
                ▼
     OBO Evidence Envelope sealed
       — what the agent did, within what scope
       — tamper-evident, offline-verifiable
       — accountability traces to operator (legal entity)
```

**The travel site → Amadeus leg has no OBO in it and needs none.**
The OBO layer sits entirely at the first contact boundary — between
the agent and the travel site. Everything behind it is unchanged.

This is the "no shared infrastructure" claim made concrete: Amadeus
does not need to know OBO exists. The hotel API does not need to know
OBO exists. The PSP does not need to know OBO exists. The travel site
resolves one DNS record and gets the answer to all four questions.

### What changes at payment finalisation

When the PSP processes the payment, the OBO Evidence Envelope is
already sealed. The accountability chain is:

```
PSP payment  ←  travel site (accountable, legal entity)
                     ←  OBO Credential (operator issued, DNS-verifiable)
                              ←  principal_id (the delegating human)
                                       ←  why_ref (RTGF rationale token)
```

If a dispute opens, the travel site produces the sealed evidence
envelope. The operator (a legal entity) is accountable — not the
agent, which has no legal standing. This is how payment networks
have always worked. OBO extends it to agents without breaking it.

---

## Legal accountability — agents are instruments, not persons

This is not a theoretical concern. It is a liability problem that will
be resolved by courts unless standards get ahead of it.

**The emerging dangerous pattern:**

Several current agentic payment approaches — including Mastercard
Verifiable Intent (VI) at its L3 autonomous mode — give agents their
own private signing keys. The agent signs transactions independently.
The payment network receives a cryptographic signature.

When a dispute opens, the question becomes: who signed?

*"An AI agent signed it."*

That is not a legal answer. Agents are not legal persons. An agent
cannot be summoned. An agent cannot testify. An agent cannot be held
liable. The private key exists. The signature exists. The signer —
as a legally accountable entity — does not exist.

This creates a **liability black hole at payment finalisation** —
the precise moment when legal accountability must crystallise. Courts
will eventually resolve this. The resolution will not be clean, and
it will not be quick. The users who transacted in the meantime carry
the risk.

This is not a criticism of Mastercard VI as a technical system.
The VI delegation chain (L1 → L2 → L3) is serious, well-designed
work. The liability gap is a consequence of L3 autonomous signing
without a clear legal-entity accountability anchor — a gap that
affects any approach that treats the agent as a signing principal
rather than an instrument of a signing principal.

**OBO's design is explicit about this:**

The agent is never the accountable party. The agent carries
credentials issued by an operator who is a legal entity.

```
operator_id   — the legal entity accountable for this agent's actions
principal_id  — the human who delegated authority
why_ref       — traces to the human-approved rationale (RTGF token)
```

The OBO Evidence Envelope records what the agent did. The
accountability chain traces to the **operator** — a company, a
regulated PSP, a legal person who can go to court, produce the sealed
evidence record, and demonstrate: *"here is what our agent was
authorised to do, here is what it did, here is the governance pack
that defined the boundary, here is the human rationale that authorised
it."*

**The operator is the legal person. The agent is the instrument.**

This is how payment networks have always worked. Visa and Mastercard
hold merchants, acquirers, and issuers accountable — not the card
terminal, not the POS software. OBO extends that proven accountability
model to agents. L3 autonomous signing without a legal-entity anchor
breaks it.

---

## How OBO fits with other work

Several serious efforts are tackling agentic trust. They are doing
valuable work. They share a foundational assumption that OBO does not:
**a live authorization server or identity infrastructure is available
and trusted by all parties.**

That assumption holds when one organisation controls the AS — internal
enterprise automation, single-platform agent deployments, API-to-API
within a trust domain. Those cases are well served by OAuth, WIMSE,
SPIFFE, and the frameworks below.

It breaks for the growth area: **cross-organisation, cross-border,
no shared AS.** An agent booking a flight, hotel, concert, and car
across four organisations in two countries has no common AS with any
of them. A healthcare agent crossing NHS and a private clinic crosses
jurisdictions. A payment agent in a regulated corridor needs
authorization scope pre-committed and auditable back to a human
decision — not negotiated at runtime by the agent itself.

OBO is built for those cases. DNS is the only shared infrastructure
assumed. The comparison is honest about where the lines are.

### The shared mental model in existing work

| Standard / protocol | Implementation state | Mental model | What it solves well | What it leaves open |
|---|---|---|---|---|
| [AAuth](https://github.com/dickhardt/AAuth) — Dick Hardt, IETF draft | Early draft. Requirements text. No reference implementation. | Agent as dynamic OAuth client. Async HTTP negotiation at the door. `purpose` parameter. | First-contact authorization without pre-registration. Open-web agent interactions. | Scope determined at runtime — negotiable, not pre-committed. No sealed post-transaction evidence. AS required. |
| [draft-klrc-aiagent-auth](https://github.com/PieterKas/agent2agent-auth-framework) — IETF draft | Early draft. Abstract layer model and requirements text. No wire format specified. No reference implementation. | Agent as workload. WIMSE + SPIFFE + OAuth unified stack. AIMS layered model. | Unified agent identity, credential lifecycle, cross-domain token chaining. Audit logs required. | Audit log **format explicitly out of scope**. Wire format unspecified. Policy format out of scope. Compliance/jurisdiction out of scope. AS required. |
| OAuth 2.0 / RFC 8693 Token Exchange | Mature RFC. Widely deployed. Multiple production implementations. | API client getting a scoped token from a live AS. | Delegated access, scopes, token exchange. Mature, widely deployed. | Live AS required. No per-transaction sealed evidence. Scope negotiated not pre-committed. |
| W3C Verifiable Credentials | W3C Recommendation. Multiple implementations. | Portable identity claims, DID-anchored. | Cryptographic credential presentation. Offline-capable identity. | No bounded-execution evidence. No per-transaction sealed record. |
| A2A agent protocols | Evolving. Protocol-level spec, no evidence standard. | Agent as tool-calling API client. Capability discovery at runtime. | Enumerating what an agent can call. Tool surface negotiation. | Runtime negotiation — agent discovers and expands scope as it goes. No proof of bounded execution. |
| **OBO** — this standard | Working draft. Running Go reference implementation exercised end-to-end. JSON examples and DNS zone templates in this repository. | Pre-committed credential + sealed post-transaction evidence. DNS as universal trust anchor. | Cross-org, cross-border, no shared AS. Offline-verifiable by any party. Tamper-evident audit record specified and portable. | Early draft. Single reference implementation. Seeking independent implementations for IETF submission. |

The pattern for the first four: **OAuth and API-centric thinking extended to agents.**
Valuable. Necessary. Not sufficient for the hardest cases. OBO is in the table
because the comparison should be honest — including about where OBO itself sits.

### What OBO does differently

OBO starts from a different assumption: **there is no shared
infrastructure except DNS.**

| | OAuth/API-centric approaches | OBO |
|---|---|---|
| Trust root | Live authorization server | DNS TXT record — universally resolvable, no AS |
| Agent scope | Negotiated at runtime | Pre-committed at credential issuance, sealed in DNS |
| Evidence format | Audit logs — format undefined or implementation-specific | OBO Evidence Envelope — specified, portable, offline-verifiable by any party |
| Offline verification | No | Yes — DNS only |
| Rationale chain | Token `sub` claim | `why_ref` — traces authorization to human-approved rationale |
| Jurisdiction/compliance | Out of scope | OBO profiles (PSD3, NHS, UAE…) |
| Two agents, no prior relationship | Requires shared AS or federation | OBO Credential verifiable from DNS alone |
| Reference implementation | None (AAuth, draft-klrc) or protocol-only (A2A) | Running Go implementation, end-to-end exercised |

### The audit gap — named explicitly

draft-klrc-aiagent-auth states:

> *"Deployments must maintain durable, tamper-evident audit logs
> recording authenticated agent identifier, delegated subject,
> accessed resource, requested action, authorization decision,
> and timestamp."*

Then: format out of scope.

That requirement, with a specified portable wire format, is the OBO
Evidence Envelope. The gap is named in the most authoritative current
IETF draft in this space. OBO fills it.

### The naming collision

draft-klrc uses "OBO semantics" to mean RFC 8693 token exchange —
a `sub` claim carrying the delegating principal. This is a token-level
delegation hint. OBO (this standard) is a two-artefact evidence
system: a pre-transaction credential and a post-transaction sealed
envelope. The name overlap is coincidental; the scope is not the same.

### Composition

These efforts and OBO are not competing. They are layers:

```
WIMSE / SPIFFE       →  agent identity and workload credentials
AAuth / OAuth        →  dynamic authorization flow (agent gets permission)
                              ↓
                     output becomes an OBO Credential
                     (pre-committed scope, DNS-anchored, offline-verifiable)
                              ↓
                     agent acts within corridor
                              ↓
OBO Evidence Envelope  →  sealed proof of what happened
                           portable, offline-verifiable, indefinitely
```

Dick Hardt's `purpose` and OBO's `intent_phrase` + `intent_hash` are
the same instinct from two directions. The difference: OBO seals the
intent into a tamper-evident record that cannot be retrospectively
disputed by any party.

---

## Status and roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | RFC draft | ✅ Complete — this repository |
| 1 | JSON Schemas and examples | ✅ In this repository |
| 2 | DNS zone templates (deployable today) | ✅ In this repository |
| 3 | Independent implementation reports | 🔲 Seeking contributors |
| 4 | Jurisdiction profiles (PSD3, UAE, NHS) | 🔲 Seeking contributors |
| 5 | D.4b suffix privacy circuit review | 🔲 Seeking cryptographic reviewers |
| 6 | IETF submission | 🔲 After Phase 3–4 validation |

---

## Interlinked open standards

OBO is one layer in a family of interlinked open standards that emerged
from the same implementation work. Each addresses a distinct layer of
the cross-org, cross-border agentic trust problem:

```
RTGF  — Regulatory Token Governance Framework
        Why was this agent authorised? Human-approved rationale chain,
        jurisdiction-mapped, anchored in DNS. The why_ref root.
        github.com/kevin-biot/rtgf-open  [ publication imminent ]

        ↓  rationale compiles into a bounded execution contract

PACT  — Pack-based Agentic Contract for Trust
        What concepts and actions are admissible? Classical ontologies
        (OWL, open-world inference) are unsafe for agent execution —
        an agent can reason itself into actions never authorised.
        PACT compiles ontologies into bounded, signed, time-valid packs:
        scoped vocabulary (SKOS), closed-world validation (SHACL),
        intent mappings, Ed25519-signed manifest, revocation epochs.
        Structural prompt-injection defence: out-of-scope requests
        fail closed regardless of JSON validity.
        github.com/kevin-biot/pact-public  [ specification published ]

        ↓  pack reference carried in credential

OBO   — On Behalf Of  ← this standard
        Pre-transaction: who, authorised for what, under whose governance
        (governance_framework_ref → PACT pack).
        Post-transaction: what happened, within what scope, tamper-evident.

        ↓  routed through governed corridors

aARP  — Agentic Authorization and Routing Protocol
        Which corridor should this agent use? Proof-based admission,
        DNS-published predicates, route evidence sealed per hop.
        [ draft in progress ]

        ↓  payment steps settled with evidence anchoring

SAPP  — Secure Agent Payment Protocol
        Payment settlement for Lane² corridors. Signs PSP receipts,
        verifies regulatory tokens, anchors Merkle evidence so aARP,
        RTGF, and policy gates can deliver deterministic payments.
        github.com/kevin-biot/sapp-profiles-public  [ publication imminent ]
```

These standards are independent and additive — each can be adopted
alone. Together they close the full loop:

```
rationale (RTGF)  →  execution contract (PACT)  →  credential + evidence (OBO)
                  →  routing (aARP)  →  settlement (SAPP)
```

**Every layer is built and running as reference implementation code.**
This is not a paper standard family. Each specification above has a
working Go implementation that has been exercised end-to-end across
the full chain. The specifications are the distillation of what the
running code required — not the other way round.

The OBO fields that connect them:

| OBO field | Points to |
|---|---|
| `why_ref` | RTGF rationale token — the human-approved authorisation root |
| `governance_framework_ref` | PACT pack — the bounded ontology execution contract |
| `intent_namespace` | PACT pack domain (e.g. `urn:obo:ns:payments`) |
| `corridor_ref` | aARP corridor — the governed routing layer |
| `stage3_ref` | SAPP settlement receipt — the payment anchor |

The chain is tamper-evident end to end.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions welcome:

- Implementation experience (what was ambiguous, what worked)
- DNS key publication reports (did Phase 1 work in your environment?)
- Jurisdiction profiles (how OBO maps to your regulatory context)
- Cryptographic review (Appendix D.4b gnark PLONK suffix circuit)
- Co-authorship on the RFC

This is an open standard. There is no approved network. There is no
co-signature gate. A rising tide raises all boats.

---

## Specification

- [draft-obo-agentic-evidence-envelope-00.md](draft-obo-agentic-evidence-envelope-00.md) — full specification
- [draft-obo-agentic-evidence-envelope-00.pdf](draft-obo-agentic-evidence-envelope-00.pdf) — rendered PDF

## Authors

K. Brown — Lane2 Architecture
Contributors welcome — see [CONTRIBUTING.md](CONTRIBUTING.md)
