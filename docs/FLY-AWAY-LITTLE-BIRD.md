# Fly Away Little Bird

*Agent deployment patterns, and the papers nobody is checking*

> *Fly away, little bird. Come back soon. Be careful who you speak to.*

That is the honest state of agentic deployment in 2026.

Every major pattern of agent deployment today — roaming cross-org
agents, corporate microservice agents, embedded consumer assistants,
computer-use agents, scheduled background agents, multi-agent swarms
— is some variation of the same gesture. An operator opens the cage.
A bird flies out. The operator hopes it comes back. The operator
hopes it did not get into trouble. The operator hopes the place it
landed was trustworthy. The operator hopes the place it landed
logged something useful in case there is a dispute.

Hope is not a standard. This document names the patterns and the
papers each pattern needs at the border.

---

## The six birds

### Bird 1 — The roaming bird (A2A / Agent Cards)

The bird flies cross-org. It finds another agent through Agent Card
discovery, sends a task, and hopes the receiver is legitimate. No
shared authorisation server. No prior relationship. No common
governance. This is the *cold-start first-contact* case: two
organisations meeting for the first time, across a jurisdictional
boundary, through intermediaries neither party controls.

The state of the art today: the receiving agent inspects the task,
runs it, and trusts. There is no credential the receiver can verify.
There is no sealed record of what happened. If the task turns out to
have been malicious, prompt-injected, or outside what the originating
human actually approved, the receiver has no way to disclaim
responsibility and the originator has no way to prove innocence.

**This is OBO's primary use case.** The credential is the bird's
passport. The Intent Artifact is its visa. The Evidence Envelope is
the customs stamp at the other end. DNS is the embassy the receiver
can call to verify the passport without calling the bird's handler.

---

### Bird 2 — The yard bird (corporate microservice agents)

The bird stays in the yard. LLM-as-a-service wrappers, OpenAI
function calling, internal agent frameworks wrapping microservice
APIs. A shared authorisation server exists. Workload identity
(SPIFFE, WIMSE, IRSA) works. OAuth 2.0 and RFC 8693 token exchange
cover the delegation cases. This is the within-trust-domain problem,
and it is largely solved.

OBO is not the primary answer here — the existing infrastructure is.
But the moment the yard bird calls an external API — Stripe, Twilio,
a partner's service, a regulator's endpoint — it crosses the fence
and becomes a roaming bird without noticing. The developer thinks
they are still making a microservice call. The auditor, a year
later, discovers they were making cross-org agentic transactions
with no accountability layer.

**OBO's role here: the boundary marker.** Inside the yard, keep
using OAuth and workload identity. At the fence, switch to OBO
credentials. The two compose. See §8 of the spec and the FAQ entry
on composition.

---

### Bird 3 — The courier (consumer app agents)

The user has delegated to an app. The app deploys an agent on the
user's behalf. The agent makes outbound calls to third-party services
— travel sites, payment processors, ticket vendors, delivery
platforms. The principal is the end user. The operator is the app
vendor. The calls are cross-org by default, even though the
developers often do not notice.

This is where *Bird 1 hides inside Bird 3*. Most developers building
consumer agent apps today do not realise they are doing cross-org
agentic transactions, because the embedded agent feels like "just
an API call" from inside their codebase. From the receiving
service's perspective it is a bird from another yard, carrying no
papers, claiming to act on behalf of a user the receiver has never
met.

**OBO's role here: making the delegation explicit.** The app vendor
becomes the `operator_id`. The end user is the `principal_id`. The
Intent Artifact carries the user's explicit authorisation
(`principal_sig`) for the specific action. The receiving service
verifies the chain offline via DNS. No account at the app vendor's
authentication system required.

---

### Bird 4 — The bird with hands (computer-use agents)

Claude Computer Use. Anthropic SDK. Browser-native agents that
click buttons, fill forms, and drive GUIs directly. The bird has
hands: it does not make API calls, it operates the user's interface
as if it were the user. The principal is literally the user at the
keyboard, and the scope is whatever the user can do from that
machine.

The interesting boundary: *local* actions (opening a file,
navigating a browser) and *remote* actions (submitting a form,
initiating a payment, sending an email) look identical to the
agent but behave very differently from an accountability
perspective. Local actions leave no cross-org trace. Remote
actions do — and the receiver at the other end has no way to
distinguish "user pressed submit" from "agent pressed submit" from
"prompt-injected agent pressed submit."

**OBO's role here: the moment of crossing.** Local computer-use is
the operator's problem. Remote computer-use is a cross-org
transaction and needs the same credential + intent + evidence chain
as any other agentic call. The Agent Card analogue is the browser's
User-Agent header, and that is where an OBO extension can attach.

---

### Bird 5 — The timer bird (background / scheduled agents)

The bird leaves on a timer. No human is watching at the moment of
execution. Cron jobs. Webhook handlers. Event-driven workers.
Overnight reconciliation agents. The intent was authorised at
*schedule creation time*, not at *execution time*, which opens a
new question: how long is intent valid for?

This is where OBO's credential lifetime question gets sharp. The
credential is short-lived (minutes). The Intent Artifact can be
pre-signed and reused across multiple runs. The operator's job is
to re-issue the credential at each execution, bound to the same
pre-signed intent, without requiring the human to re-approve every
fire of the timer.

**OBO's role here: separating authority from execution.** The
human's `principal_sig` over the Intent Artifact is the durable
authorisation. The credential (which must be refreshed) is the
short-lived execution token. The Evidence Envelope is per-run.
The chain holds across arbitrary numbers of runs without requiring
new human approvals for each one.

---

### Bird 6 — The flock (multi-agent swarms)

One bird sends another, which sends another. CrewAI, AutoGen,
orchestrator-worker chains, agentic workflows where Agent A spawns
Agent B spawns Agent C. The delegation chain may cross organisations
at any hop. The originating human's authorisation must survive
through every hop without being re-rooted, broadened, or forgotten.

The failure mode here is subtle. Each hop looks like a reasonable
delegation in isolation. The cumulative effect is that the
originating human's intent is several degrees removed from the
final action, and nobody in the chain is sure whose authority they
are acting under.

**OBO's role here: the invariant chain.** §3.3 defines the
delegation artifact: each hop signs its narrowing of scope, the
`principal_id` and `why_ref` travel unchanged through all hops,
and scope monotonically narrows at every step. A child credential
can never broaden what its parent authorised. The original human's
signature is visible at every hop. This is the only pattern where
the current OBO spec does explicit design work beyond the
two-party case.

---

## What papers does a bird need at the border?

A bird at a border crossing needs three things:

1. **A passport** — who sent it, from which legal entity, verifiable
   by anyone without calling the home country
2. **A visa** — what it is allowed to do at the destination, bounded,
   time-limited, authorised by a named human
3. **A customs stamp** — a record of what it actually did, sealed at
   the time, verifiable years later in a dispute

OBO is not a new bird species. It is the papers the birds should
have been carrying all along.

| What birds need | What OBO provides |
|---|---|
| Passport | OBO Credential — operator-signed, DNS-anchored, offline-verifiable |
| Visa | Intent Artifact — structured action, bounded parameters, dual-signed by principal and operator |
| Customs stamp | Evidence Envelope — sealed post-transaction, Merkle-anchored, independently attestable |
| Embassy | DNS — the universal resolver every counterparty already has |
| Jurisdiction | `governance_framework_ref` → PACT pack, machine-readable rules of the destination |
| Accountability | Legal entity behind the operator domain, tied to the registrar, WHOIS, and applicable law |

The papers are not optional for humans crossing borders. They are
not optional for packages crossing borders. They are not optional
for wire transfers crossing borders. They are, today, optional for
agents crossing borders — and that is the gap OBO closes.

---

## The honest headline

**Today, nobody is checking papers at the agent border because
nobody is carrying them.**

Every pattern above is running in production somewhere right now
with no credential, no sealed intent, no evidence envelope, and no
legal-entity accountability chain. The receiving services are
trusting by default. The originating operators are hoping by
default. The principals are clicking "approve" on vague permissions
dialogs and trusting that the bird will behave.

This works until it does not. The first large chargeback dispute
where an agent booked the wrong thing, the first regulatory
enforcement action where an agent violated a rule the operator
cannot prove it did not authorise, the first legal discovery
request where the operator is asked to produce tamper-evident
records of what their agent actually did — these are the moments
when papers will suddenly become mandatory.

When that happens, the question will not be *"whose standard has
the nicest developer experience?"* or *"whose SDK has the most
stars?"* It will be *"whose standard produces records a court
will accept?"* Every pattern above — every bird in the taxonomy
— will need an answer.

OBO's proposition: the papers should be anchored to infrastructure
that already exists (DNS, Ed25519, legal-entity domains), should
be verifiable offline by any party without calling anyone, and
should be sealed into tamper-evident records that survive
arbitrary delays and jurisdictional boundaries. The bird flies
away. The bird comes back. The papers prove, to any party, what
the bird was allowed to do and what it actually did — without
asking the bird's handler for permission to check.

Fly away, little bird. Come back soon. Be careful who you speak
to. And carry your papers.

---

## Related reading

- **[The Scope Problem](THE-SCOPE-PROBLEM.md)** — why a certificate
  alone is not enough
- **[USE-CASES.md](USE-CASES.md)** — concrete cross-org scenarios
  that map to each bird above
- **[FAQ.md](FAQ.md)** — the common objections, answered with spec
  references
- **[REPUTATION-SYSTEMS-AND-AGENT-ACCOUNTABILITY.md](REPUTATION-SYSTEMS-AND-AGENT-ACCOUNTABILITY.md)**
  — why reputation scores are not papers
- **Issues #16–#20** — recent technical concerns raised externally,
  captured with responses in the issue tracker
