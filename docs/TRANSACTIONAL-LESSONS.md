# Lessons from Transactional Infrastructure

**Version:** 0.4.11
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

*OBO standard: https://github.com/kevin-biot/obo-standard*
*Feedback and commentary welcome via GitHub Issues.*
