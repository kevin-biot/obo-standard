# Reputation Systems and Agent Accountability: Why They Are Not the Same Thing

**Version:** 0.4.9
**Date:** 2026-04-05

---

## Abstract

As multi-agent systems mature, a class of proposals has emerged that
uses reputation scores — aggregated from counterparty attestations,
success rates, and interaction history — as a trust signal for agent
selection and authorisation. This paper examines why reputation systems
are structurally insufficient for accountable agentic transactions,
catalogues the attack vectors that make reputation scores unreliable,
and explains why accountability — declared authority plus sealed
evidence — is the correct foundation for governed agentic systems.

This is not a criticism of reputation systems as a category. It is a
precise description of what they do and do not provide, and why they
cannot substitute for accountability in regulated, high-stakes, or
cross-organisational agentic deployments.

---

## 1. The Distinction That Matters

**Reputation** answers: *"has this agent behaved well in the past,
according to the people who reported on it?"*

**Accountability** answers: *"who is the legal entity behind this
agent, what were they authorised to do, what did they actually do, and
is that record tamper-evident and independently verifiable?"*

These are not two approaches to the same problem. They are answers to
different questions. In casual, low-stakes interactions — agent
discovery, task routing, capability selection — reputation may be
useful. In regulated transactions, cross-organisational operations,
dispute resolution, and regulatory audit, reputation is insufficient
and accountability is mandatory.

The error is treating reputation as a proxy for accountability. It is
not. A high reputation score does not establish who is liable. A sealed
evidence record does.

---

## 2. What Reputation Systems Actually Measure

Most reputation systems in the agentic space work as follows:

1. Agent A performs a task for Agent B
2. Agent B submits a signed attestation about A's performance
3. Attestations accumulate in a graph or database
4. Queries return a score, history, or "credibility packet"
5. Consumers use the score to decide whether to trust A

The score measures **what counterparties reported**. Nothing more.
It does not measure:

- What actually happened
- Whether the outcome caused downstream harm
- Whether the reporting counterparty was independent
- Whether the task was within a governed scope
- Whether a human principal authorised the action
- Who is liable if the action causes harm

---

## 3. The Score Tells You Less Than It Appears To

### 3.1 The Severity Collapse Problem

A 99% success rate collapses risk, severity, domain, and consequence
into a single number. All information is destroyed in the compression.

Consider an agent with the following history:

| Task type | Volume | Success rate |
|-----------|--------|-------------|
| Read-only queries | 9,800 | 100% |
| Translation | 180 | 100% |
| Payment execution | 15 | 47% |
| Medical triage | 5 | 20% |

Aggregate success rate: 99.1%. The agent is catastrophically bad at
the two highest-stakes task types. The score conceals this completely.

Skill-scoped attestation systems partially address this — but only if:
- The skill scope is granular enough to capture the distinction
- Counterparties correctly identify which skill was exercised
- Volume in each skill is sufficient for statistical validity

In practice, early deployments have thin attestation history in exactly
the categories that matter most.

### 3.2 The Base Rate Problem

A 99% success rate over 10 transactions is statistically meaningless.
Even over 10,000 transactions, the score says nothing about transaction
10,001. Past performance in stochastic systems does not predict future
outcomes. This is not a controversial claim — it is the standard
disclaimer on every financial product.

Reputation systems applied to high-stakes agentic transactions face the
same problem. The score provides false confidence calibrated to
historical volume that may be unrepresentative of the current task.

### 3.3 The Definition Problem

Success by whose definition?

- Transaction executed = success?
- Transaction executed correctly = success?
- Transaction executed correctly and principal's intent was served = success?
- No downstream harm within the relevant time window = success?

Counterparties report what they noticed at the time they noticed it.
Harm that manifests later, downstream, or indirectly is invisible to
the attestation system. A pharmaceutical agent that successfully
executed a prescription query but triggered a dangerous drug
interaction two weeks later will have a 100% success rate in the
attestation graph.

---

## 4. Reputation Systems Are Gameable

### 4.1 The Sybil Attack

The canonical attack on reputation systems is the Sybil attack: create
multiple identities, use them to attest to each other, manufacture a
reputation that appears legitimate.

In agentic systems this attack is not merely theoretical — it is
**trivially executable** and scalable. The attack proceeds as follows:

```
Phase 1 — Infrastructure (months 1-3):
  Spin up Agent-A, Agent-B, Agent-C, Agent-D
  All controlled by the same bad actor
  Different identities, different keypairs, different apparent operators

Phase 2 — Reputation laundering (months 1-3):
  Transact among each other at low value
  Cross-attest: "A performed excellently", "B was reliable"
  Build attestation graphs that appear independent
  Scores accumulate: all four agents reach high credibility

Phase 3 — Exploitation (month 4+):
  All four agents now appear trusted
  Approach real counterparties simultaneously
  Execute high-value fraud across all four
  Four trusted agents, four times the damage

Phase 4 — Reset:
  Abandon all four identities
  Repeat with four new ones
  Prior fraud is not visible in the new agents' history
```

The attestation graph has no ground truth. It records what was
submitted. It cannot distinguish a real independent counterparty from a
sock puppet. Ed25519 signatures verify that the attester signed the
attestation — they do not verify that the attester was independent of
the attested agent.

### 4.2 Collusion Rings

A weaker variant of the Sybil attack requires no single bad actor to
control multiple identities. A collusion ring — a group of agents
operated by different but cooperating bad actors — achieves the same
result:

- Agents transact among ring members, building mutual reputation
- Ring members attest positively to each other
- Each agent's score reflects the ring's collective attestation volume
- Scores are used to approach real targets outside the ring

Detection requires graph analysis that identifies suspiciously dense
attestation clusters. This requires access to the full graph, which is
not always available to individual consumers, and sophisticated anomaly
detection that most deployments will not run.

### 4.3 The Success Rate Manufacturing Attack

Even without Sybil attacks, success rates can be manufactured by
carefully controlling the composition of transactions reported:

```
Real task portfolio:    40% high-value payments (50% success rate)
                        60% low-value queries  (100% success rate)

Reported portfolio:     Report all low-value queries
                        Do not report high-value payment failures

Apparent success rate:  100%
Actual success rate:    70%
```

Counterparty attestation is voluntary in most systems. Strategic
omission — not reporting failures, or structuring the reported task
mix to suppress failure rates — is undetectable from the attestation
graph alone.

### 4.4 Temporal Gaming

Reputation systems that use recency weighting or decay functions are
vulnerable to temporal gaming:

- Establish high reputation over a long baseline period
- Exploit the high score in a short burst of high-value fraud
- The fraud represents a small fraction of the total history
- Score recovers quickly after the burst if the agent continues

The attacker treats the reputation score as a financial instrument —
accumulate it cheaply, spend it profitably, recover it for the next
cycle.

### 4.5 The Cold-Start Inversion

Reputation systems cannot assess new agents. By definition, a new
agent has no history. The system returns silence, which is
indistinguishable from:

- A genuinely new agent with no track record
- An agent with a suppressed bad track record operating under a new identity

The cold-start problem means reputation systems provide the least
signal precisely when signal is most needed: first contact with an
unknown agent.

OBO inverts this completely. A new agent with a freshly issued OBO
Credential has full, declared authority from day one — because a
human principal made an explicit declaration, not because the agent
accumulated a history. Authority does not need to be earned. It needs
to be declared by an accountable entity.

---

## 5. What Accountability Provides Instead

OBO is not a reputation system. It does not aggregate historical
signals. It provides two things reputation systems do not:

### 5.1 Declared Authority — Not Earned Trust

The OBO Credential declares:

- Which human principal authorised this agent
- Which legal entity operates it
- What action classes it is permitted to execute
- Under what governance framework
- For what intent namespace
- Until what date

This declaration is made at issuance by a real, accountable entity. It
is DNS-anchored and offline-verifiable. It requires no history. It
cannot be manufactured by transacting among sock puppets.

To fabricate an OBO Credential, an attacker must:
- Register a real domain (traceable, costs money)
- Publish DNS records pointing to a governance framework (auditable)
- Issue a credential under a real operator identity (legally attributable)
- For Class C/D actions: pass KYC (real identity required)

The cost and traceability of credential fabrication are orders of
magnitude higher than manufacturing attestation history.

### 5.2 Sealed Evidence — Not Reported Outcomes

The OBO Evidence Envelope is sealed by the emitter at transaction time
and submitted to a Merkle-anchored log. It records:

- What the agent intended (intent hash)
- What class of action was taken (A/B/C/D)
- What the outcome was
- What governance framework applied
- A tamper-evident digest covering all fields

This record is not submitted by a counterparty. It is not voluntary. It
is not retrospectively alterable. The anchor's Merkle receipt proves
the record existed at a specific time. No attestation, no social signal,
no counterparty cooperation required.

The Sybil attack fails at the evidence layer: cross-attestation
transactions between sock puppet agents are permanently recorded in the
Merkle log. A forensic analyst observing that four agents transacted
exclusively with each other for three months, then simultaneously
approached real counterparties, has tamper-evident evidence of the
pattern. It cannot be erased.

---

## 6. The Precedent: How Financial Networks Actually Work

The debate about reputation systems for agents has a clear precedent in
financial infrastructure. SWIFT, Visa, and every major payment network
operate at global scale, across organisational boundaries, with
counterparties that have never previously interacted. None of them use
reputation scores.

They use two things: **admission** and **adherence**.

**Admission** answers: are you a legal entity, bound by the network's
rules, with a declared identity that can be held accountable? For SWIFT,
this means a BIC — a Bank Identifier Code issued to a legal entity that
has signed the SWIFT membership agreement. No BIC, no message. No legal
entity, no BIC. The question is not "are you trustworthy?" It is "are
you admitted?"

**Adherence** answers: is your message conformant to the standard? An
ISO 20022 pacs.008 credit transfer is either well-formed or it is not.
The schema validates. The required fields are present. The IBAN is
valid. The amount is within corridor limits. Adherence is binary.

Nobody asks HSBC's reputation score before accepting a SWIFT message.
The question is whether HSBC is a member and whether the message
conforms. That is sufficient — because if HSBC causes harm, there is a
legal entity, bound by a membership agreement, that is liable.

### 6.1 Admission and Adherence for Agents

The same model applies to governed agentic systems. The questions that
matter at transaction time are not:

- *"Does this agent have a good reputation?"*
- *"Has this agent succeeded 99% of the time?"*
- *"What do other agents say about it?"*

The questions that matter are:

- *"Is this agent admitted — backed by a legal entity, under a
  declared governance framework, with a binding commitment?"*
- *"Is this agent's action conformant — within declared action
  classes, for a governed intent, producing a sealed evidence record?"*

Admission is declared in the OBO Credential. Adherence is enforced by
the corridor governance pack. Evidence of adherence is the sealed OBO
Evidence Envelope.

This is the SWIFT model applied to agents. It has worked at global
scale in financial infrastructure for decades. It does not require
reputation, attestation graphs, or success rate aggregation. It
requires legal entities and binding commitments.

### 6.2 The Human Decision Layer

Reputation systems also conflate two things that should remain
distinct: **automated execution** and **human selection**.

When a human chooses a hotel, a contractor, or a service provider, they
apply judgment that cannot be reduced to a score. Proximity, personal
recommendation, specific context, and risk tolerance all factor in.
These are human decisions — and they should remain human decisions.

An agent selecting a hotel based on a reputation score is not making a
human decision. It is executing a pre-determined preference function
dressed up as autonomous choice. The human who configured that
preference function made the real decision — the agent is a tool
executing it.

For high-stakes selections — which contractor do I hire, which agent
do I delegate my finances to, which service provider handles my health
data — the selection decision itself requires human accountability.
Reputation scores do not provide accountability. They provide a number
that launders a human decision through an automated proxy, removing the
human from the accountability chain precisely where their presence
matters most.

The correct model: agents execute within declared scopes under human
authority. Selection of counterparties above a consequence threshold is
a human decision, not an agent optimisation.

---

## 7. Accountability and Reputation Are Complementary, Not Competing

This paper does not argue that reputation systems have no value. In
low-stakes, high-volume, within-trust-domain scenarios — agent
discovery, task routing, capability selection — reputation signals
provide useful, fast, lightweight guidance.

The argument is precisely scoped:

1. Reputation cannot substitute for accountability in regulated,
   high-stakes, or cross-organisational transactions.

2. Reputation scores are gameable at the systematic level described
   in Section 4.

3. Reputation scores collapse severity information in ways that make
   them misleading for risk assessment (Section 3).

4. Accountability — declared authority plus sealed evidence — is
   not gameable by the same mechanisms, because it is grounded in
   real legal entities and tamper-evident records rather than social
   signals.

The complete stack for accountable agentic systems requires both:

```
Reputation layer     →  has this agent been reliable?
                        useful for discovery and task routing
                        not sufficient for regulated transactions

Accountability layer →  who authorised this agent?
                        what did it actually do?
                        who is liable?
                        required for regulated transactions,
                        dispute resolution, regulatory audit
```

OBO provides the accountability layer. It does not compete with
reputation systems. It completes the stack they cannot complete alone.

---

## 7. Implications for System Design

For designers of agentic systems operating in regulated domains, the
following principles follow from the analysis above:

**1. Do not gate regulated transactions on reputation scores.**
Use declared authority (OBO Credential) and sealed evidence (OBO
Evidence Envelope). Reputation may inform agent selection before
authority verification; it must not replace it.

**2. Treat success rates as lagging, severity-blind indicators.**
If you use success rates, scope them narrowly to the specific task
type, weight by consequence severity, and require minimum volume
thresholds before treating them as meaningful.

**3. Design attestation systems with graph-level Sybil detection.**
If you operate a reputation system, assume collusion rings exist and
deploy graph-level anomaly detection as a baseline. Thin attestation
graphs with high mutual density are suspicious by default.

**4. Require accountable legal entities behind agents, not just
reputation scores.**
The question is not "does this agent have a high score?" The question
is "which organisation is liable if this agent causes harm?"
Reputation scores do not answer this question. OBO Credentials do.

**5. Treat the cold-start problem as a design constraint, not an edge
case.**
First-contact scenarios are normal in cross-organisational agentic
systems. Reputation systems provide zero signal at first contact. OBO
Credentials provide full authority signal at first contact. Design for
the cross-org case, not the within-trust-domain case.

**6. Use admission and adherence, not reputation, as the primary
trust signal for regulated transactions.**
The financial networks that operate at global scale — SWIFT, Visa, and
equivalents — do not use reputation scores. They use admission (is this
a legal entity bound by the network's rules?) and adherence (is this
message conformant?). These are the right primitives for governed
agentic systems. Reputation is a supplement for low-stakes selection,
not a substitute for admission and adherence in regulated corridors.

**7. Do not delegate high-consequence selection decisions to agents.**
Choosing a counterparty above a consequence threshold — which agent
handles my finances, which service processes my health data, which
contractor is admitted to act in this corridor — is a human decision.
Automating it through a reputation score removes the human from the
accountability chain at precisely the point their accountability
matters most. Agents execute within declared scopes. Selection of
those scopes, and the parties within them, remains a human
responsibility.

---

## 8. Conclusion

Reputation systems measure social signal. Social signal can be
manufactured, gamed, suppressed, and misinterpreted. In the limit, a
sufficiently motivated attacker with sufficient time can construct a
reputation that is indistinguishable from a legitimate one — at which
point the score provides negative value, because it creates false
confidence.

Accountability is not reputation. Accountability is a declared,
legally-attributable, tamper-evident record of who authorised what,
and what actually happened. It is grounded in real legal entities, real
governance frameworks, and real cryptographic commitments — not in what
counterparties chose to report.

For casual agent interactions: reputation is useful.
For regulated transactions, cross-org operations, and dispute
resolution: accountability is mandatory.

The two are not substitutes. The complete stack requires both.

---

*OBO standard: https://github.com/kevin-biot/obo-standard*
*Feedback and commentary welcome via GitHub Issues.*
