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

Existing standards answer questions 1–3 well within a trust domain.
OBO adds question 4 — the accountability layer they were not designed to
provide — and composes with them rather than replacing them:

- **OAuth** is the right choice inside a trust domain with a shared AS.
  OBO fills the cross-org, no-shared-AS case: a DNS-anchored credential
  that any counterparty can verify offline, without calling anyone.
- **WIMSE / SPIFFE** provide strong workload identity within an organisation.
  OBO carries that identity *across* the trust domain boundary, where
  workload certificates have no verifier.
- **W3C Verifiable Credentials** carry portable identity claims.
  OBO adds the per-transaction layer: what scope was exercised, what
  happened, sealed and tamper-evident after the fact.
- **A2A agent protocols** handle capability discovery and task routing.
  OBO is the accountability layer A2A explicitly left out of scope —
  the two compose directly (see `examples/integrations/a2a/`).

---

## Start here — two artefacts, zero infrastructure

OBO is two JSON objects. That is the minimum. Everything else is optional.

```
OBO Credential        — carried by the agent before the transaction
                        answers: who, authorised for what, under whose governance

OBO Evidence Envelope — sealed by the agent after the transaction
                        answers: what happened, within what scope, tamper-evident
```

**To try it now:**

```bash
cd examples/integrations/a2a
python keygen.py --operator-id your-domain.com   # generates Ed25519 keypair
cp .env.example .env                              # paste values from keygen output
docker-compose up --build                         # three containers, full evidence chain
```

Seven test scenarios run automatically — two clean accepts, five rejection
edge cases with error codes. The output is a real Merkle receipt from SAPP.
No infrastructure beyond Docker and one DNS TXT record.

**What is optional vs. required:**

| Capability | Required for | How hard |
|---|---|---|
| OBO Credential + Evidence Envelope | All use cases | Two JSON objects |
| One DNS TXT record (`_obo-key`) | Cross-org verification | 30 seconds in Route 53 |
| SAPP / Merkle anchoring | Regulated audit trails | SAPP container in docker-compose |
| RTGF / `why_ref` | Regulated high-risk AI, PSD3 | Optional field, ignored if absent |
| aARP | Intent routing (separate protocol) | Not required for OBO |

Start with the first two rows. Add rows as your use case requires.

---

## The full solution

Both artefacts are verifiable **offline, without contacting any central
service**, by anyone who can resolve DNS — including organisations that
have never met the agent, share no infrastructure with its operator,
and are in a different jurisdiction.

> **DNS as the universal trust anchor.** Every organisation on the
> internet can resolve DNS. No shared AS required. No pre-registration.
> No approved network. Operator signing keys are published as DNS TXT
> records — the same infrastructure pattern DKIM has used for email
> trust for twenty years.
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
[specification](draft-obo-agentic-evidence-envelope-01.md).

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

See [Appendix E](draft-obo-agentic-evidence-envelope-01.md#appendix-e-dns-anchoring-profile)
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

**OBO composes with VI, not against it.**

Mastercard VI's delegation chain (L1 → L2 → L3) is serious,
well-designed work. The VI credential carries delegation authority
through the chain. An OBO Evidence Envelope wrapping a VI transaction
adds the post-transaction accountability layer: sealed, tamper-evident,
offline-verifiable proof of what the agent did within its delegated
scope. Every VI merchant becomes addressable — OBO adds to what VI
delivers, not an alternative path.

The structural point applies to any approach that makes the agent the
signing principal rather than an instrument of a signing principal:

```
operator_id   — the legal entity accountable for this agent's actions
principal_id  — the human who delegated authority
why_ref       — traces to the human-approved rationale (RTGF token)
```

Agents are not legal persons. An agent cannot be summoned, cannot
testify, cannot be held liable. The OBO Evidence Envelope records what
the agent did and traces accountability to the **operator** — a
company, a regulated PSP, a legal person who can go to court and
demonstrate: *"here is what our agent was authorised to do, here is
what it did, here is the governance pack that defined the boundary."*

**The operator is the legal person. The agent is the instrument.**

This is how payment networks have always worked. Visa and Mastercard
hold merchants, acquirers, and issuers accountable — not the card
terminal. OBO extends that proven accountability model to agents.

---

## A parallel task: teaching the agentic market

OBO has two jobs. The first is technical: define the minimum
interoperable artefacts that make agentic transactions accountable
across organisational boundaries.

The second is educational. Most agent systems being built today are
getting the architecture wrong — not because the teams are careless,
but because the right patterns have not been clearly named. OBO names
them:

**Positive patterns OBO establishes:**
- Intent before tools — scope is pre-committed, not discovered at runtime
- Authority and execution are separate layers — the OBO Credential
  carries authority; workload identity (SPIFFE, IRSA, k8s) carries
  execution credentials; they do not substitute for each other
- Policy is external and deterministic — the corridor enforces it;
  the agent does not decide its own scope
- The principal is the accountable party — the agent is an instrument,
  not a legal person
- Evidence is a first-class artefact — not a log format left to the
  implementor, but a specified, portable, offline-verifiable record

**Antipatterns OBO names explicitly:**
- LLM as policy judge — non-deterministic, prompt-injectable, produces
  no verifiable record (§1.9, Appendix G.10)
- Agents as API surfaces — treating cross-org agentic transactions as
  microservice-to-microservice calls and applying OAuth perimeter
  thinking to them (§1.2)
- Runtime scope negotiation — the agent discovering and expanding what
  it can do as it goes, rather than carrying pre-committed, sealed
  authority (§1.4)

Most RFCs describe existing practice. OBO names the patterns and
antipatterns before the market has made its mistakes at scale. The RFC format
provides the precision required for interoperability. The narrative
structure in §1 provides the teachability required for adoption.

If you are building an agentic system today and these patterns are
useful regardless of whether you adopt OBO's wire format, that is a
successful outcome.

---

## How OBO composes with other work

OBO is a layer, not a replacement. The right mental model:

```
VI / x402 / A2A / OAuth    →  move the transaction
OBO                        →  prove what happened and who was accountable
```

An x402 payment with an OBO Evidence Envelope in the metadata gets
the Visa/Mastercard/Stripe settlement infrastructure *plus* the
accountability chain that regulators and courts will eventually require.
An A2A agent carrying an OBO credential composes the two directly —
see `examples/integrations/a2a/` for a runnable reference.

OBO fills one specific gap: **cross-organisation, cross-border,
no shared AS.** Inside a trust domain with a shared authorisation
server, use OAuth. At the boundary where no shared AS exists — two
organisations meeting for the first time, no prior relationship,
different jurisdictions — OBO is the layer that makes the interaction
auditable without either party calling anyone.

DNS is the only shared infrastructure assumed. Every organisation on
the internet already has it.

### Where each layer composes

| Layer | What it does well | Where OBO adds |
|---|---|---|
| **OAuth / RFC 8693** | Delegated access within a trust domain. Mature, widely deployed. | OBO adds the cross-org case where no shared AS exists, plus sealed post-transaction evidence OAuth does not produce. |
| **Mastercard VI / Visa TAP** | Delegation chain through the card network (L1→L2→L3). | OBO wraps the VI transaction and adds tamper-evident post-transaction proof. Every VI merchant is addressable. |
| **x402 / HTTP payment protocols** | Payment rail — moves money over HTTP. | OBO is the accountability layer riding on the settlement. The Foundation's infrastructure plus OBO = complete regulated stack. |
| **A2A agent protocols** | Capability discovery, task routing, Agent Cards. | OBO fills the accountability gap A2A explicitly left out of scope. Declared in the Agent Card as `authentication.schemes: ["obo"]`. |
| **WIMSE / SPIFFE** | Workload identity within an organisation. | OBO carries identity *across* the trust domain boundary where workload certificates have no external verifier. |
| **W3C Verifiable Credentials** | Portable identity claims, DID-anchored. | OBO adds per-transaction bounded-execution evidence — what scope was exercised, what happened, sealed after the fact. |
| **AAuth / draft-klrc** | Dynamic authorisation flow, agent-as-OAuth-client. | OBO adds the no-AS case and the sealed evidence record both leave open. |
| **OBO** — this standard | Cross-org, no-AS accountability. Offline-verifiable by any party. | Working draft. Running Go reference implementation. Seeking independent implementations. |

### The one thing OBO does that the others do not

**Sealed, portable, offline-verifiable post-transaction evidence,
anchored to a legal-entity accountability chain, verifiable by any
party with DNS.**

No AS required. No prior relationship required. No shared
infrastructure required beyond DNS — which every counterparty already has.

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

## Reference implementation

A working end-to-end demo ships in this repository. Three Docker containers,
real Ed25519 keys, a live DNS trust anchor, and seven test scenarios covering
both the happy path and five failure modes.

**Verify the trust anchor right now — no setup needed:**

```bash
dig +short TXT _obo-key.lane2.ai @8.8.8.8
# → "v=obo1 ed25519=vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"
```

**Results from the live run (2026-04-04):**

```
[FlightSearchAgent] OBO key ready  source=dns-txt  key=vqiddGZ0skvsek13nUks…

  SCENARIO 1 — Flight search LHR→JFK        → allow  ✓  SAPP checkpoint_idx: 0
  SCENARIO 2 — Hotel search New York         → allow  ✓  SAPP checkpoint_idx: 1
  SCENARIO 3 — Tampered intent               → 422    OBO-ERR-005  ✓
  SCENARIO 4 — Missing OBO extension         → 422    OBO-ERR-001  ✓
  SCENARIO 5 — Expired credential            → 422    OBO-ERR-003  ✓
  SCENARIO 6 — Forged Ed25519 signature      → 422    OBO-ERR-004  ✓
  SCENARIO 7 — Replayed credential_id        → 422    OBO-ERR-008  ✓
```

For each allowed transaction, 14 leaves are committed to the SAPP Merkle tree —
binding operator identity, principal DID, intent hash, task correlation reference,
outcome, and Ed25519 envelope signature into a single `merkle_root`. For rejected
transactions the gate fires before any task executes; no evidence is minted.

**The evidence chain for Scenario 1:**
```
OBO credential issued    → credential_sig: Ed25519 over intent_hash + principal_id
A2A task dispatched      → extensions.obo carries the credential inline
FlightSearchAgent verifies  DNS lookup _obo-key.lane2.ai → pubkey → Ed25519 check
Evidence envelope sealed → evidence_digest + envelope_sig: Ed25519
SAPP Merkle anchored     → merkle_root: 4f29251a3d5a565c53a1…  checkpoint_idx: 0
```

**Run it yourself:**
```bash
cd examples/integrations/a2a
python3 keygen.py --operator-id your-domain.com
# Set DNS TXT record, fill .env, then:
docker compose up --build
```

Full runbook → [`examples/integrations/a2a/README.md`](examples/integrations/a2a/README.md)

---

## Status and roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | RFC draft | ✅ Complete — this repository |
| 1 | JSON Schemas and examples | ✅ In this repository |
| 2 | DNS zone templates (deployable today) | ✅ In this repository |
| 2a | A2A reference implementation (Docker, live DNS) | ✅ In this repository |
| 3 | Independent implementation reports | 🔲 Seeking contributors |
| 4 | Jurisdiction profiles (PSD3, UAE, NHS) | 🔲 Seeking contributors |
| 5 | E.4b suffix privacy circuit review | 🔲 Seeking cryptographic reviewers |
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

aARP  — Agentic Authorisation and Routing Protocol
        Which corridor should this agent use? Runtime intent routing
        without hardcoded endpoints — DNS-published admission predicates,
        proof-based corridor membership, route evidence sealed per hop.
        The missing link between OBO accountability and dynamic agent
        discovery at runtime. aARP is a live component of the Lane2
        architecture today, exercised end-to-end with OBO credentials
        in production pipeline runs. The reference server is currently
        private. The authors intend to publish aARP as an open standard
        protocol and release the reference server as soon as the
        specification has stabilised. [ forthcoming ]

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
- Cryptographic review (Appendix E.4b gnark PLONK suffix circuit)
- Co-authorship on the RFC

This is an open standard. There is no approved network. There is no
co-signature gate. A rising tide raises all boats.

---

## Specification

- [draft-obo-agentic-evidence-envelope-01.md](draft-obo-agentic-evidence-envelope-01.md) — full specification

## Authors

K. Brown — Lane2 Architecture
Contributors welcome — see [CONTRIBUTING.md](CONTRIBUTING.md)
