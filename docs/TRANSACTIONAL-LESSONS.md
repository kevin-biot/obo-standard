# Lessons from Transactional Infrastructure

**Version:** 0.4.13
**Date:** 2026-04-05

---

## A Note on Tone

This document is not a criticism of anyone building in the agentic AI
space. It is an attempt to make available, for free, a set of lessons
that the financial, healthcare, and regulated infrastructure industries
learned the hard way over thirty years — through failures, frauds,
regulatory interventions, and legal proceedings that were expensive,
painful, and in some cases irreversible.

Every rule in SWIFT's operating manual exists because a bank lost
money. Every requirement in PSD2 exists because consumers were
defrauded. Every clause in GDPR exists because data was abused at
scale. The rules look like bureaucracy. They are crystallised disaster.

The agentic AI ecosystem is building infrastructure that will process
real transactions, handle real money, affect real people, and operate
across real legal jurisdictions. These lessons are available. You do
not have to repeat the failures that produced them.

---

## 1. The $5 Problem

A single $5 transaction going wrong is trivial. A million $5
transactions going wrong simultaneously is a regulatory incident, a
class action, and a company-ending event.

Automation does not change the consequence of individual failures. It
changes the **rate at which they occur** and the **scale at which they
compound**.

Developers building agentic systems for low-value transactions
frequently reason: *"the stakes are low, so the governance overhead is
disproportionate."* This reasoning fails at scale in several ways:

**Volume multiplies harm.** A 0.1% error rate on 10 million
transactions is 10,000 failures. Each one affects a real person. At
some volume, even a tiny error rate produces harm that is no longer
acceptable — legally, regulatorily, or reputationally.

**Consumer protection law does not care about transaction size.** The
EU's PSD2 applies to a €1 payment with the same force as a €1,000,000
one. GDPR applies to the processing of one person's data with the same
force as a billion people's. The obligation scales with the nature of
the action, not the value of the transaction.

**Small transactions teach the architecture.** The patterns you
establish at $5 are the patterns you will use at $50,000. Building
without accountability at low value teaches developers — and codebases
— that accountability is optional. It is not optional at high value.
The time to learn the patterns is when the cost of getting them wrong
is still low.

**Fraud finds the lowest-value automation first.** Automated systems
processing low-value transactions at high volume are attractive to
fraudsters precisely because the per-transaction harm is below human
review thresholds. The automation that makes the system efficient makes
the fraud efficient too.

---

## 2. Failure Modes Are Designed, Not Discovered

In early software systems — and in many agentic systems being built
today — failure modes are discovered when they occur. Something goes
wrong, the team investigates, a fix is deployed. This is reasonable for
a web application returning incorrect search results.

It is not reasonable for a system that moves money, processes medical
instructions, or acts on behalf of a human in a legally consequential
context.

**Transactional infrastructure inverts this.** The question asked
before building is not *"what should the system do when it works?"* but
*"what should the system do when it fails?"*

- What happens if the agent executes an action that the principal did
  not intend?
- What happens if the action is irreversible and the outcome is wrong?
- What happens if two systems disagree about whether a transaction
  completed?
- What happens if the agent is compromised mid-session?
- What happens if the counterparty disputes the outcome six months
  later?

These questions have answers in financial infrastructure. The answers
were not designed in advance by visionaries. They were extracted from
failures and codified as requirements. The ISO 20022 pain.002 payment
status report exists because payments got lost and nobody could agree
on whether they had completed. The SWIFT gpi tracker exists because
correspondent banking chains were opaque and money disappeared into
them.

Agentic systems will encounter analogous failures. The question is
whether the architecture was designed to handle them or will need to be
redesigned after they occur.

---

## 3. Authorisation Is Explicit or It Does Not Exist

*"The system let it happen"* is not authorisation.

In transactional infrastructure, authorisation means a specific,
identified, legally accountable entity explicitly declared that a
specific action was permitted, in advance of that action occurring.
Implicit permission — inferred from capability, inferred from prior
behaviour, inferred from the absence of a prohibition — is not
authorisation in any regulated context.

This distinction matters practically:

**Capability is not permission.** An agent that can call a payment API
is not thereby authorised to make payments. The API accepting the call
is not authorisation. The technical ability to execute an action has
never constituted legal permission to execute it. This is as true for
software agents as it is for humans.

**Prior behaviour is not standing permission.** An agent that
successfully executed 1,000 transactions last month is not thereby
authorised to execute transaction 1,001. Each transaction requires
that authorisation exist at the time of execution, from an entity with
standing to grant it.

**Scope matters as much as permission.** Authorisation to make payments
up to €1,000 is not authorisation to make payments up to €1,000,000.
Authorisation to query account balances is not authorisation to
initiate transfers. The scope of authorisation must be declared
explicitly and enforced mechanically.

**Authorisation must be verifiable by the counterparty.** An agent
claiming to be authorised is not sufficient. The counterparty receiving
the agent's request must be able to verify that authorisation
independently — without calling the agent's operator, without trusting
a shared registry, without prior relationship. This is the unsolved
problem in most current agentic frameworks. It is the problem OBO was
designed to address.

---

## 4. If It Is Not Recorded, It Did Not Happen

This is not a philosophical claim. It is a legal, regulatory, and
operational one.

In regulated industries, the record is the event. A payment that
executed but left no auditable trail did not happen, officially. A
consent that was granted but not recorded cannot be relied upon in a
dispute. A medical instruction that was issued but not documented is
clinically and legally void.

The record must be:

**Tamper-evident.** A log that can be modified after the fact is not a
record. It is a story that can be rewritten. Financial audit trails are
tamper-evident by design, not by policy. Policy can be changed. A
Merkle-anchored log cannot be silently altered.

**Independent of the parties.** A record held only by the party that
benefits from its contents is not a trusted record. Certificate
Transparency logs are operated by independent parties precisely because
a CA-held record of its own certificate issuance would be worthless as
accountability infrastructure.

**Temporally anchored.** When did the event occur? Not approximately.
Exactly. To a standard that a court will accept. Timestamp manipulation
is a common fraud vector. Records must be anchored to an external time
source that cannot be retroactively adjusted.

**Complete.** Partial records are worse than no records in some
contexts — they create the appearance of accountability while obscuring
the parts that matter. The record of a transaction must include the
authority under which it was executed, not just the execution itself.

Agentic systems that log to application databases, that store records
only with the executing party, or that record outcomes without
recording the authority and governance context, are not producing
accountable records. They are producing stories.

---

## 5. Liability Must Be Assigned Before Execution

The question *"who is responsible if this goes wrong?"* must have an
answer before the first transaction executes. Not before the first
failure. Before the first transaction.

This is not a legal formality. It is an architectural constraint. A
system that cannot answer the liability question at design time cannot
answer it at incident time — and incident time is the worst possible
moment to discover that the liability chain is ambiguous.

**Agents are not legal persons.** An AI agent cannot be sued. It cannot
be fined. It cannot be held criminally liable. It cannot sign a
contract. The human or legal entity that deployed it, configured it,
and authorised it to act is the legally accountable party. If that
entity is not clearly identified and bound at the time the agent acts,
the liability chain is broken.

**"The AI did it" is not a defence.** Regulators in every major
jurisdiction have been explicit on this point. The EU AI Act, the FCA's
guidance on automated decision-making, the ECB's expectations for
algorithmic trading — all place accountability with the deploying
entity, not the algorithm. An agent acting without a clearly identified
human principal and operator is an agent whose actions may be
legally attributable to no one — which is precisely the outcome that
benefits bad actors.

**Liability assignment must precede capability.** In practical terms:
before an agent executes any action with real-world consequences, there
must be a declared, verifiable binding between that agent and a legal
entity that has accepted responsibility for its actions. This is not
bureaucracy. It is the minimum condition for the system to be
governable.

---

## 6. Automation Amplifies Everything

Automation does not change the nature of what is being automated. It
changes the speed, scale, and consistency with which it occurs.

A human payment clerk making errors at the rate of 0.01% processes
perhaps 500 transactions per day. An automated system making errors at
the same rate processes 500,000 transactions per day. The error rate
is identical. The daily harm is one thousand times larger.

This amplification applies to everything:

- **Correct behaviour** scales — which is why automation is valuable
- **Errors** scale — which is why error rates that are acceptable in
  human processes are unacceptable in automated ones
- **Fraud** scales — which is why automated systems attract fraud that
  manual ones do not
- **Harm** scales — which is why the governance requirements for
  automated systems are higher than for manual ones, not lower

The common reasoning in early agentic development — *"we'll add
governance later when we scale"* — reverses the correct order. The
governance requirements at scale are determined by the architecture
established before scale. A system built without accountability cannot
have accountability added to it at scale. It must be rebuilt.

The time to establish the governance architecture is before the first
transaction, when the cost of getting it right is low and the cost of
getting it wrong has not yet been paid.

---

## 7. Discovery Is Not Trust

In agent discovery systems, finding an agent that claims a capability
is not the same as trusting that agent to execute it.

The financial equivalent: being able to find a bank's SWIFT address
does not mean you can send that bank a payment instruction. The bank
must be a SWIFT member. Your institution must have a correspondent
relationship with it, or route through one that does. The message must
conform to the applicable message standard. The transaction must be
within the limits of the bilateral agreement between the institutions.

Discovery is the beginning of a trust establishment process, not the
end of it. In SWIFT's model, the trust establishment process involves:

- Membership admission — legal entity, bound by rules
- Correspondent agreement — bilateral scope declaration
- Message conformance — technical adherence to standard

Each step is explicit and verifiable. None of them are reputation-based.
None of them depend on what other banks have said about this bank.

Agent discovery systems that return an agent card and treat it as
sufficient for task delegation have skipped all three steps. They have
found the SWIFT address and started sending payment instructions without
establishing that the recipient is a member, without agreeing a
correspondent scope, and without validating message conformance.

This is not a hypothetical failure mode. It is the architecture of most
current agent frameworks.

---

## 8. The Moment of Understanding

There is a moment, familiar to anyone who has worked in regulated
transactional infrastructure, when a developer building their first
serious system understands why the rules exist.

It usually occurs after the first real incident — a payment that cannot
be recovered because there is no record of it, a consent dispute where
the audit trail is incomplete, a fraud that was invisible until it was
too late because the governance layer was deferred.

The rules that looked like bureaucracy reveal themselves as the
residue of someone else's incident. The requirement for tamper-evident
logs exists because someone's log was tampered with. The requirement
for explicit authorisation exists because an implicit authorisation was
exploited. The requirement for liability assignment exists because
liability was genuinely ambiguous when it needed to be clear.

This document is an attempt to offer that moment of understanding
without the incident.

The agentic AI ecosystem is building systems that will, in time,
process transactions with real consequences at real scale. The
governance patterns that make such systems trustworthy are not new.
They are documented, proven, and available. The question is whether
they are applied before the failures or extracted from them.

The transactional world chose the latter. The invitation here is to
choose the former.

---

## 9. Automation Has Limits — and the Agent Cannot Choose For You

There is a strong aspiration in the agentic AI community for agents to
make selection decisions on behalf of humans. The agent finds three
hotels in Dubai. The agent selects a plumber from ten options. The
agent chooses a counterparty, a service, a path. Reputation signals,
attestation graphs, and scoring systems are largely motivated by this
aspiration: if we give the agent enough signals, it can choose well.

This aspiration should be examined carefully, because it contains a
hidden assumption that is frequently wrong.

### 9.1 Selection Is Not Execution

There is a meaningful difference between:

- **Execution** — the agent carries out a task whose parameters were
  defined by a human. Book the cheapest available flight from London
  to Paris on Tuesday. Transfer €500 to this IBAN. Query my account
  balance and return it.

- **Selection** — the agent chooses between options whose relative
  value depends on human judgment, personal context, risk tolerance,
  and preferences that cannot be fully specified in advance. Which of
  these ten plumbers should I hire? Which of these three hotels is
  right for my trip? Which counterparty should I trust with my data?

Execution within declared scope is what agents are for. Selection above
a consequence threshold is what humans are for.

The distinction is not arbitrary. It reflects the structure of
accountability. When an agent executes within a declared scope, the
human who declared that scope is accountable for the outcome — they
set the parameters, they carry the responsibility. When an agent
selects on behalf of a human using reputation signals, the
accountability chain becomes ambiguous: the human did not choose, the
agent chose, and the agent has no legal personhood. If the plumber
causes damage, who is liable for the selection?

### 9.2 Reputation Signals Are Not Selection Criteria

The response to this problem in much of the current agentic ecosystem
is to provide the agent with reputation signals and treat high-scoring
options as safe selections. This is an anti-pattern for several
reasons already documented in this repository's analysis of reputation
systems. But there is a deeper issue specific to selection:

Reputation signals aggregate past behaviour across contexts that may
be entirely different from the current one. A plumber with 500 positive
reviews for bathroom installations may be the wrong choice for
electrical work. A hotel with a 4.9 star rating for business travel
may be the wrong choice for a family with young children. A financial
agent with a strong track record in bull markets may be the wrong
choice in a crisis.

The signal is real. The inference from signal to selection is not.
Selection requires understanding of the specific context, the specific
needs, and the specific risk profile of this decision, for this person,
at this time. Reputation systems do not provide that. They provide an
average across prior contexts.

Treating reputation signals as selection criteria transfers the
accountability for a human judgment to a statistical artifact. That is
not automation. It is accountability laundering.

### 9.3 The Regulatory Direction of Travel

The EU AI Act distinguishes AI systems by risk class and mandates
human oversight accordingly. For high-risk systems — those affecting
employment, credit, healthcare, law enforcement, and critical
infrastructure — human review of consequential decisions is not
optional. The system may present options. The human must decide.

This is not an arbitrary regulatory preference. It reflects a
considered judgment that certain decisions require a human accountable
party, regardless of how capable the automated system is. Capability
is not the criterion. Accountability is.

The current regulatory scope covers defined high-risk categories.
The direction of travel — as AI systems become more capable and more
consequential — is toward broader human oversight requirements, not
narrower ones. Systems built today on the assumption that agents will
autonomously select counterparties, service providers, and consequential
options may find that assumption in tension with regulatory requirements
that did not exist when the system was designed.

Building human decision points into the architecture from the start is
not a constraint on capability. It is an architectural decision that
keeps the system governable as regulatory requirements evolve.

### 9.4 The Anti-Pattern

To be precise: automated selection of consequential counterparties
using reputation signals as the decision criterion is an anti-pattern
in accountable agentic system design.

It is a pattern that will appear to work — until it fails in a way
that cannot be explained, attributed, or remedied, because the
selection decision was made by a statistical process with no
accountable principal behind it.

The correct pattern:

- Agents **present options** with transparent criteria to humans
- Humans **make selection decisions** above defined consequence thresholds
- Agents **execute** the selected option within a governed scope
- The evidence of execution is **sealed and attributable**

This is not a limitation of agentic systems. It is the correct
allocation of judgment and accountability between humans and machines.

### 9.5 A Note on Aspiration

None of this is to say that automation cannot improve selection over
time. Recommendation systems have genuine value. Filtering, ranking,
and presenting options based on declared preferences is legitimate
automation. The line is not between presenting options and selecting —
it is between presenting options transparently and selecting
opaquely, between recommendation and decision, between assistance and
substitution.

The aspiration to have agents decide is understandable. The
infrastructure being built to realise that aspiration — reputation
graphs, attestation scores, trust signals — is real work by capable
people. The concern is not with the aspiration. It is with the
assumption that sufficient signal quality makes autonomous agent
selection safe, accountable, and legally sound.

That assumption has not been tested at scale, in regulated contexts,
under adversarial conditions. The transactional world's experience
suggests it will not hold when tested. The invitation is to design
for that outcome before the test occurs.

---

*OBO standard: https://github.com/kevin-biot/obo-standard*
*Feedback and commentary welcome via GitHub Issues.*
