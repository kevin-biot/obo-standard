Internet-Draft: draft-lane2-obo-agentic-evidence-envelope-00
Intended status: Experimental
Expires: 2 October 2026
Individual Submission – Lane2 Architecture

Lane2 Architecture                                             2 April 2026

---

# On Behalf Of (OBO): Minimum Evidence Envelope for Agentic Transactions

**draft-lane2-obo-agentic-evidence-envelope-00**

*Status:* Working Draft 0.1
*Editors:* K. Brown (Lane2 Architecture)
*Date:* 2026-04-02

---

## Status of This Memo

This Internet-Draft is submitted in full conformance with the provisions
of BCP 78 and BCP 79. Internet-Drafts are working documents of the
Internet Engineering Task Force (IETF). Note that other groups may also
distribute working documents as Internet-Drafts. The list of current
Internet-Drafts is at https://datatracker.ietf.org/drafts/current/.

Internet-Drafts are draft documents valid for a maximum of six months
and may be updated, replaced, or obsoleted by other documents at any
time. It is inappropriate to use Internet-Drafts as reference material
or to cite them other than as "work in progress."

This document is subject to BCP 78 and the IETF Trust's Legal
Provisions Relating to IETF Documents
(https://trustee.ietf.org/license-info) in effect on the date of
publication. Please review these documents carefully, as they describe
your rights and restrictions with respect to this document.

---

## Abstract

This document defines the On Behalf Of (OBO) minimum evidence envelope
for agentic transactions. An OBO-compliant transaction produces two
artefacts: an OBO Credential carried by the agent before the
transaction, and an OBO Evidence Envelope sealed after it. Together
these artefacts answer the questions a regulator, counterparty, or court
requires of any autonomous agent acting on behalf of a human or
organisational principal.

This specification defines minimum required fields and their semantics.
It does not mandate credential issuance mechanisms, token formats,
corridor implementations, or policy enforcement mechanisms. Profiles for
regulated lanes, local/offline agents, and corridor-bound deployments
are defined as optional extensions.

The OBO envelope is domain-agnostic. It applies equally to payment
initiation, healthcare instruction, legal instruction, consumer commerce,
and any other context where an agent acts on behalf of a principal.

---

## 1. Introduction

### 1.1 The On Behalf Of Problem

Autonomous agents act on behalf of human and organisational principals
at increasing scale. A user instructs an agent; the agent interacts with
one or more target services; actions with real-world consequences occur.

The current standards landscape does not provide a minimum evidence
standard for this interaction class:

- OAuth 2.0 / OBO [RFC 8693] covers token delegation between known
  parties sharing common authorization infrastructure. It does not cover
  one-time transactions between parties with no prior relationship, local
  agents without access to authorization servers, or the sealed evidence
  record of what the agent actually did.

- W3C Verifiable Credentials [VC-DATA-MODEL] provide portable identity
  claims. They do not define the per-transaction evidence envelope.

- Emerging A2A agent protocols focus on tool enumeration and capability
  advertisement. These create reconnaissance surfaces without providing
  evidence that the advertised capabilities were exercised within
  declared scope.

None of these standards addresses the dominant consumer case: a local
or consumer-side agent transacting with an unknown target service on a
one-time basis, where the target has no prior relationship with the
originating agent and no shared authorization infrastructure.

### 1.2 The Core Requirement

An agent acting on behalf of a principal MUST be able to demonstrate,
to any party after the fact, without requiring a live authorization
server:

1. Who authorised the agent to act (principal binding)
2. What the agent was authorised to do (scope)
3. What the agent actually did (evidence)
4. That the action stayed within the authorised scope (integrity)
5. Under what governance framework the action occurred (authority chain)

This specification defines the minimum data structures that carry these
five properties.

### 1.3 The Two-Agent First Contact Problem

The dominant case in agentic commerce is two agents that have no prior
relationship, share no authorization infrastructure, and have never
transacted before. Agent A (originating) approaches Agent B (target).
Agent B faces a fundamental challenge:

> "Who are you? Who sent you? What are you allowed to do?
> And if I proceed, how will I prove what actually happened?"

The current standards landscape provides no answer to this in one place.
OAuth 2.0 [RFC 8693] requires shared infrastructure. W3C VCs provide
identity claims but not per-transaction bounded evidence. A2A tool
enumeration describes capability surfaces but does not answer the
authorisation or evidence questions.

The OBO Credential is Agent A's minimum answer to Agent B's challenge:

1. I act for principal P — `principal_id` and `binding_proof_ref`
2. My authority derives from governance framework G — `governance_framework_ref`
3. I am authorised for action classes X in namespace N — `action_classes`, `intent_namespace`
4. My authority window is bounded — `issued_at`, `expires_at`
5. This credential is tamper-evident — `credential_digest`

Agent B does not need to know Agent A in advance. It evaluates the
credential against its own acceptance parameters: is the namespace
acceptable? Is the declared action class within my ceiling for this
operation? Is the governance framework one I recognise? Is the
credential signature verifiable?

If yes: proceed. If no: reject. No phone-home required. No central
registry lookup required. This is the first contact trust floor.

### 1.4 Minimal Trust and Progressive Deepening

OBO provides a **trust floor**, not a trust ceiling. Accepting an OBO
Credential does not mean the target fully trusts the originating agent.
It means the target has verified the minimum basis to proceed.

Trust deepens progressively through the interaction:

```
Stage 1 — Intent admission
  OBO Credential verified: scope within ceiling, signature valid,
  namespace accepted, credential not expired.
  Trust floor established. Proceed to intent evaluation.

Stage 2 — Evidence sealed
  OBO Evidence Envelope produced: outcome recorded, intent hash bound,
  action class confirmed within credential scope.
  Evidence of bounded execution created.

Stage 3 — Legal precision (where applicable)
  Payment, digital signature, consent receipt, or data release
  provides legal precision for the specific action class.
  Trust deepened to the level required for that action class.
```

Stage 3 is not always required. For class A (read-only) operations,
Stage 2 evidence is sufficient. For class B/C/D operations, Stage 3
provides the legal anchor appropriate to the action's reversibility
and regulatory exposure.

**Evidence accumulates into reputation without a central registry.**
Each sealed OBO Evidence Envelope is a verifiable record of prior
bounded behaviour. A target that has received envelopes from Agent A
across prior transactions can evaluate the pattern. Reputation is not
a score assigned by a central authority; it is the accumulated,
tamper-evident history of what the agent actually did. OBO enables
reputation without requiring a reputation registry.

**The agent card problem.** Protocols that require an agent to
enumerate its tool surface before interaction invert this model: they
answer "what can you do?" rather than "who are you and what are you
authorised for?". Tool enumeration creates a reconnaissance surface —
a complete map of the agent's capabilities — without providing any
evidence that those capabilities were exercised within declared scope.
OBO is intent-first: the originating agent declares what it intends,
not what it is capable of. The target determines whether that intent
class is within its acceptance parameters.

### 1.5 Evidence, Authorisation, and Intent Are Not Separable

Several current frameworks in the agentic trust space treat evidence as
a separable concern — a logging requirement to be addressed by deployment
teams, a format to be defined in a future document, an audit trail whose
structure is explicitly out of scope. This section explains why that
treatment is architecturally incorrect and legally untenable.

#### 1.5.1 What the law actually requires

Legal standards that govern consequential transactions do not permit the
evidence layer to be deferred or left unspecified. Selected examples:

- **PSD2 (EU) Article 74**: liability in disputed payment transactions
  rests on the party who authorised the transaction. Establishing that
  liability requires tamper-evident evidence of the authorisation act,
  the identity of the authorising party, and the scope of what was
  authorised. Format is not optional — the evidence must be producible
  to a regulator or court by any party to the chain.

- **EU AI Act Article 12**: high-risk AI systems must maintain logs
  sufficient to enable appropriate oversight and post-hoc audit. The
  logs must capture the AI system's inputs and outputs. An agent
  operating in a regulated context is a high-risk AI system; its
  evidence chain is a compliance obligation, not a deployment choice.

- **eIDAS 2.0**: electronic transactions and qualified signatures require
  evidence of the authentication act, the intent expressed, and the
  binding of that intent to the outcome. Evidence format is part of the
  conformance requirement.

- **GDPR Article 7**: where processing is based on consent, the
  controller must be able to demonstrate that consent was given. For
  agents acting on a principal's behalf, that demonstration requires
  sealed evidence of the delegation, the scope, and the outcome.

- **Payment network rules (Mastercard, Visa, SWIFT)**: dispute
  resolution requires the complete chain from authorisation to
  settlement. An acquirer or issuer that cannot produce this chain loses
  the dispute by default. "The audit log format was out of scope" is not
  a recognised defence.

The pattern is consistent: where transactions have legal or regulatory
consequences, evidence format is not optional. It is a conformance
requirement imposed by the legal system, not a preference of the
implementer.

#### 1.5.2 Why the components must be interlinked

Authentication, authorisation, intent, and evidence are not independent
layers that can be specified separately and composed later. Each element
of a complete accountability chain references and seals the others:

```
Principal intent
  → sealed in the OBO Credential (intent_namespace, action_classes)
  → carried by the agent to the target
  → verified against DNS-anchored operator key

Authorisation act
  → credential_digest_ref in the Evidence Envelope binds the outcome
    to the credential that authorised it
  → why_ref traces the authorisation to the human-approved rationale

Execution outcome
  → intent_hash binds the Evidence Envelope to the specific intent
    that was admitted
  → action_class in the envelope must not exceed the credential ceiling
  → prior_evidence_ref chains multi-step transactions into a
    tamper-evident sequence

Accountability
  → operator_id in both artefacts identifies the legal entity
    responsible for the agent's actions
  → all fields hashed and signed; any modification invalidates
    the chain
```

Each reference is cryptographic. Removing any element — treating
evidence as separable, leaving intent undefined, omitting the
authorisation anchor — breaks the chain. A broken chain cannot be
produced to a court, a regulator, or a counterparty in a dispute. It is
not a weaker chain. It is no chain at all.

#### 1.5.3 The cost of deferral

When an authentication and authorisation framework declares evidence
format out of scope, the practical consequence is not that evidence is
handled elsewhere. It is that:

1. Each deployment invents its own evidence format, making cross-party
   verification impossible.
2. The evidence cannot be verified by a counterparty who was not party
   to the original deployment agreement.
3. The evidence cannot be verified offline, after the fact, by a
   regulator who was not present at transaction time.
4. Disputes cannot be resolved without a live service operated by the
   original parties — precisely the parties with the most to gain from
   an ambiguous record.

OBO's design starts from the opposite premise: the evidence format is
the specification. The authentication and authorisation fields exist to
make the evidence verifiable. The two artefacts — OBO Credential and
OBO Evidence Envelope — are not separate concerns. They are the two
sides of a single accountability record, specified together so that any
party, anywhere, can verify the complete chain from principal intent to
transaction outcome without contacting anyone.

### 1.6 Design Principles

**Intent first.** The primitive is a normalised intent, not a tool
invocation list. The target service does not need to enumerate its
internal tools. The originating agent declares what it intends; the
target determines whether it can serve that intent class.

**Evidence over reputation.** Agent reputation is not a score assigned
by a central registry. It is accumulated from tamper-evident evidence
records of prior transactions. A target agent verifies the evidence
chain, not a reputation score.

**Routing-agnostic.** OBO does not depend on any specific routing,
corridor, or capability-discovery protocol. It operates equally over
aARP governed corridors, A2A agent card discovery, direct HTTPS, or
any other transport. The evidence envelope records what happened and
who was accountable — it does not specify how the agent was located or
how the capability surface was negotiated. Routing mechanisms advertise
what an agent can do; OBO seals what it was authorised to do and what
it actually did. These are different layers and OBO does not collapse
them.

**Payment is Stage 3, not Stage 1.** Authorization is not established
at intent time via a pre-issued token. It deepens as the interaction
proceeds. Payment, signature, or data release at Stage 3 provides legal
precision for that interaction class. The OBO envelope records the
complete Stage 1 → Stage 2 → Stage 3 journey.

**Offline and local.** The OBO Credential MUST be verifiable without a
live authorization server. The Evidence Envelope MUST be sealable
without network connectivity. This enables consumer-side and device-local
agents that cannot perform online re-resolution at execution time.

**Intent is sealed because it will be disputed.** In any contested
transaction — a chargeback, a regulatory inquiry, a liability question —
the first question is: what did the principal actually intend? The
`intent_hash` in the Evidence Envelope is SHA-256 of the normalised
intent at the moment of execution. It binds the sealed record to the
specific governing purpose, making retrospective reframing by any party
impossible. The `why_ref` extends this further: it traces the intent to
the upstream human-approved rationale that authorised it. Disputes about
intent are resolved by evidence. OBO is the evidence.

**Delegation origin travels; it does not re-root.** In a multi-agent
chain, the `principal_id` of the originating human and the `why_ref`
of their approved rationale are carried unchanged through every hop.
No intermediate agent in the chain has authority to substitute a new
principal or issue a new root rationale. When human-in-the-loop
intervention is required at any point in a multi-agent chain, the human
to consult is always the originating principal — the one identified in
the credential that started the chain. This is not a deployment policy
choice left to implementations. It is a structural property of OBO's
credential model: authority traces to a human at the root of the
delegation tree, and that root does not move.

**Agents execute under delegated authority; they do not originate it.**
An agent is a workload that acts on behalf of a human or legal entity
principal. Agents may be classified, risk-scored, attested, and
registered for execution control purposes — but none of this confers
legal standing on the agent itself. Legal authority originates with the
`principal_id` (the human) and the `operator_id` (the accountable legal
entity). The agent is a party in the evidence record, not an authority
source. Authorization systems that evaluate agent identity for risk
controls (scope ceiling, TTL, step-up requirements, attestation checks)
are performing workload classification — a legitimate and necessary
security function — but that classification does not transfer legal
authority to the agent. The delegation chain always traces back to a
human or legal entity. There is no mechanism in OBO by which an agent
acquires independent legal standing.

---

## 2. Terminology

This specification uses the keywords MUST, MUST NOT, SHALL, SHALL NOT,
SHOULD, SHOULD NOT, and MAY as described in RFC 2119 and RFC 8174 when,
and only when, they appear in all capitals.

| Term | Definition |
|---|---|
| Principal | The human or organisational entity on whose behalf the agent acts. |
| Agent | The autonomous software entity executing actions on behalf of the principal. |
| Operator | The entity that deploys and operates the agent (may differ from principal). |
| Target | The service or agent receiving the intent and executing the action. |
| OBO Credential | The portable, pre-transaction artefact carried by the agent declaring its authority to act. |
| OBO Evidence Envelope | The sealed, per-transaction artefact recording what happened. |
| Intent | The normalised expression of what the principal wishes to accomplish, sealed in the evidence record at transaction time. Intent is a legal construct: it defines the scope of the agent's authority and is the primary evidence in any dispute about whether the agent's actions were authorised. It is distinct from the tasks the agent performed — tasks are the mechanical execution; intent is the governing purpose that authorises the task set. Sealing the intent at transaction time makes retrospective reframing impossible. |
| Task | A discrete action or step performed by the agent in service of the intent. Tasks are within scope when they fall within the intent's authorised class and namespace; they are out of scope when they exceed it. Task-level evidence is the domain of profiles (e.g. SAPP for payment tasks); OBO seals the governing intent that authorises the task set. |
| Intent Class | A governed category of intent mapped to an action class and scope boundary. |
| Action Class | A severity classification of the action implied by the intent (read-only through irreversible). |
| Corridor | A governed, evidence-chained channel between an originating agent and a target. |
| Why-Reference | An immutable pointer to the upstream rationale authority that established the meaning of the transaction's governing concept. |
| Governance Framework Ref | A stable pointer to the machine-readable policy and ontology pack governing the transaction. |

Requirement identifiers follow the pattern OBO-REQ-NNN.

---

## 3. OBO Credential

The OBO Credential is carried by the agent. It is issued before the
transaction and is valid for a declared period or scope. It is
cryptographically signed by the operator or an authorised issuer.

OBO credentials are pull-issued. The agent authenticates to the
credential issuer using its runtime identity (mTLS client certificate,
client credentials grant, PACT attestation, or equivalent) and receives
a signed credential in response. No inbound channel, callback URI, or
listening socket is required on the agent. Deployments that cannot
accept inbound connections — CLI tools, container workloads, scheduled
jobs, bots operating behind NAT — are fully supported without
modification to this specification. Callback-based OAuth flows
(Authorization Code Grant, CIBA) are not precluded, but are not assumed
and are not required.

The translation between an OBO credential and legacy downstream
authentication mechanisms (API keys, service account tokens, OAuth
access tokens for third-party services) is a corridor gateway concern,
not a credential protocol concern. The agent presents its OBO credential
to the corridor; the corridor's tool execution layer handles downstream
authentication using whatever credentials it holds for that service. The
agent does not receive, store, or present raw API keys or equivalent
secrets.

OBO credentials are transport-agnostic. They are application-layer
artifacts carried in HTTP headers or request bodies. TLS termination
by network intermediaries — load balancers, API gateways, WAF proxies,
service mesh sidecars — does not affect OBO credential validity.
The corridor validates the OBO credential at the application layer
regardless of the transport topology between the agent and the corridor
endpoint.

### 3.1 Required Fields

OBO-REQ-001: An OBO Credential MUST contain the following fields:

| Field | Type | Description |
|---|---|---|
| `obo_credential_id` | string | Stable, globally unique identifier for this credential. |
| `principal_id` | string | Identifier of the principal on whose behalf the agent acts. Format is scheme-specific (DID, URN, or domain-qualified identifier). |
| `agent_id` | string | Identifier of the agent. MUST be bound to the credential by signature. |
| `operator_id` | string | Identifier of the entity operating the agent. MAY equal `principal_id` for self-operated agents. |
| `binding_proof_ref` | string | Reference to the proof of binding between principal and agent (e.g. signed delegation record, consent receipt, legal instrument). |
| `intent_namespace` | string | The governed intent namespace within which this credential is valid (e.g. `urn:lane2:ns:payments`, `urn:lane2:ns:healthcare`). |
| `action_classes` | array[string] | The action classes this credential authorises. Values: `A` (read-only), `B` (reversible write), `C` (irreversible write), `D` (systemic). |
| `governance_framework_ref` | string | Stable pointer to the machine-readable governance framework (ontology pack digest, policy snapshot ref, or equivalent). |
| `issued_at` | integer | Unix epoch seconds at issuance. |
| `expires_at` | integer | Unix epoch seconds at expiry. MUST be present. Short-lived credentials are RECOMMENDED. |
| `issuer_id` | string | Identifier of the credential issuer. |
| `credential_digest` | string | SHA-256 digest of the canonical JSON serialisation of this credential (excluding this field). Enables tamper detection. |

### 3.2 Optional Fields

OBO-REQ-002: An OBO Credential MAY contain the following fields:

| Field | Type | Description |
|---|---|---|
| `scope_constraints` | object | Additional scope constraints beyond action class (e.g. maximum transaction value, permitted jurisdictions, permitted target identifiers). |
| `why_ref` | object | Upstream rationale authority reference for regulated lanes. See Section 5.1. |
| `offline_verifiable` | boolean | When true, the credential MUST be verifiable without network access. Signing key MUST be embedded or pre-distributed. |
| `corridor_binding` | string | Identifier of the corridor this credential is bound to, when corridor-specific issuance applies. |
| `delegation_depth` | object | Present only in explicit multi-hop delegation chains. Contains `current` (integer, this credential's depth from the origin, starting at 0) and `max` (integer, the chain ceiling set by the originating credential). A credential with `current == max` MUST NOT be used to issue sub-credentials. Each derived credential MUST carry the same `max` and `current` incremented by one. `scope_constraints` MUST NOT widen relative to the parent credential at any hop. |
| `parent_credential_ref` | string | The `obo_credential_id` of the credential from which this credential was derived. Required when `delegation_depth.current > 0`. Enables verifiers to walk the chain and detect scope widening or revocation of any ancestor. |

### 3.3 Signing

OBO-REQ-003: An OBO Credential MUST be signed using a cryptographic
scheme that supports offline verification. Ed25519 signatures over the
canonical JSON serialisation are RECOMMENDED. The signing key MUST be
identifiable from the `issuer_id` field without requiring a live key
resolution endpoint when `offline_verifiable` is true.

---

## 4. OBO Evidence Envelope

The OBO Evidence Envelope is sealed per transaction. It is produced by
the agent (or by a governed corridor on the agent's behalf) after the
transaction completes. It is tamper-evident and independently verifiable.

### 4.1 Required Fields

OBO-REQ-010: An OBO Evidence Envelope MUST contain the following fields:

| Field | Type | Description |
|---|---|---|
| `evidence_id` | string | Stable, globally unique identifier for this evidence record. |
| `obo_credential_ref` | string | The `obo_credential_id` of the credential under which this transaction occurred. |
| `credential_digest_ref` | string | The `credential_digest` of the credential at time of transaction. Detects post-issuance credential tampering. |
| `principal_id` | string | Repeated from credential for standalone verifiability. |
| `agent_id` | string | Repeated from credential for standalone verifiability. |
| `intent_hash` | string | SHA-256 of the canonical normalised intent phrase. Binds the evidence to the specific intent that was admitted. |
| `intent_class` | string | The governed intent class to which the intent was mapped. |
| `action_class` | string | The action class of the executed action (`A`, `B`, `C`, or `D`). MUST be within the `action_classes` declared in the credential. |
| `outcome` | string | Transaction outcome. Values: `allow`, `deny`, `escalate`, `error`. |
| `policy_snapshot_ref` | string | Reference to the policy snapshot under which the action was evaluated. |
| `governance_framework_ref` | string | Repeated from credential. Enables standalone verification without credential lookup. |
| `sealed_at` | integer | Unix epoch seconds at which this envelope was sealed. |
| `evidence_digest` | string | SHA-256 of the canonical JSON serialisation of this envelope (excluding this field). |

### 4.2 Optional Fields

OBO-REQ-011: An OBO Evidence Envelope MAY contain the following fields:

| Field | Type | Description |
|---|---|---|
| `corridor_ref` | string | Identifier of the corridor through which the intent was routed. |
| `target_id` | string | Identifier of the target service or agent. |
| `stage3_ref` | string | Reference to the Stage 3 completion event (payment transaction ID, signature ref, consent receipt ID). |
| `why_ref` | object | Upstream rationale authority reference for regulated lanes. See Section 5.1. |
| `route_proof_ref` | string | Reference to the routing proof from the corridor (e.g. aARP route decision hash). |
| `prior_evidence_ref` | string | Reference to a prior evidence envelope in a multi-step transaction chain. |
| `approval_evidence` | object | Multi-party human approval record for high-impact operations. See Section 4.4. |

### 4.3 Integrity

OBO-REQ-012: The `evidence_digest` MUST be computed over the canonical
JSON serialisation of the envelope with all fields present and
`evidence_digest` set to the empty string. The canonical form uses
lexicographically sorted keys and no insignificant whitespace.

OBO-REQ-013: When `why_ref` is present and non-empty, the
`why_ref.rationale_digest` MUST be included in the canonical
serialisation before computing `evidence_digest`.

OBO-REQ-014: The `action_class` in the evidence envelope MUST be within
the `action_classes` declared in the referenced OBO Credential. A
verifier MUST reject an evidence envelope where this constraint is
violated.

### 4.4 Approval Evidence (Multi-Party HITL)

For Class C and Class D operations — irreversible writes and systemic
actions — a corridor MAY require that the evidence envelope carry a
sealed approval record. This section defines the portable structure for
that record. The approval *policy* (whether multi-party approval is
required, which roles must approve, what assurance level is sufficient)
is deployment-defined and out of scope. The evidence *structure* is
defined here so that approval records are interoperable across
deployments.

The `approval_evidence` object, when present, MUST contain:

| Field | Type | Description |
|---|---|---|
| `operation_binding` | string | SHA-256 digest of the canonical serialisation of the action payload or policy snapshot that was approved. Binds the approval to the exact operation, not a description of it. |
| `threshold` | object | `{"required": N, "obtained": M}` where `M >= N`. The number of independent approvals required and obtained. |
| `valid_from` | integer | Unix epoch seconds: earliest time at which execution under this approval is permitted. |
| `valid_until` | integer | Unix epoch seconds: latest time at which execution under this approval is permitted. |
| `approvals` | array | One entry per approver. See below. |

Each entry in `approvals` MUST contain:

| Field | Type | Description |
|---|---|---|
| `approver_ref` | string | Identifier of the approving human (same scheme as `principal_id`). |
| `role_class` | string | The role or function of the approver (deployment-defined; e.g. `"finance-controller"`, `"ciso"`). |
| `assurance_level` | string | Authentication assurance level at approval time (e.g. `"AAL2"`, `"AAL3"` per NIST SP 800-63). |
| `mfa_method` | string | MFA method used (e.g. `"fido2"`, `"totp"`, `"sms"`). |
| `approved_at` | integer | Unix epoch seconds at which this approver confirmed. |

The `approval_evidence` object MAY additionally contain:

| Field | Type | Description |
|---|---|---|
| `segregation_required` | boolean | When true, no approver in `approvals` may be the same identity as `principal_id` or any other approver. Corridors MUST enforce this constraint when the field is true. |

**Fail-closed rule.** When a corridor requires `approval_evidence` for
a Class C or D action and the envelope presents one, the corridor MUST
verify:

1. `operation_binding` matches the digest of the actual action payload
   being executed.
2. `obtained >= required` in `threshold`.
3. `valid_from <= now <= valid_until`.
4. If `segregation_required` is true, all approver identities are
   distinct and none equals `principal_id`.
5. Each `approver_ref` has not been revoked or suspended.

If any check fails, the corridor MUST reject the operation. The agent
does not participate in the approval flow. Approval is obtained by the
corridor or an upstream policy authority and sealed into the envelope
before execution reaches the agent.

---

## 5. Profiles

### 5.1 Regulated Lane Profile (why_ref)

For transactions in regulated lanes (EU AI Act high-risk AI systems,
PSD3 payment initiation, healthcare instruction), the `why_ref` object
provides immutable linkage to the upstream regulatory rationale that
established the meaning of the governing concept.

The `why_ref` object:

| Field | Type | Description |
|---|---|---|
| `rationale_id` | string | Stable identifier of the upstream rationale record (RTGF or equivalent). |
| `rationale_digest` | string | SHA-256 digest of the canonical rationale record payload. |
| `derivation_digest` | string | SHA-256 digest of the ontology derivation artefact linking the rationale to the executed concept. |

When `why_ref` is present, the verifier MAY resolve the `rationale_id`
to confirm the rationale record is not revoked. For offline verification,
the `rationale_digest` provides tamper detection without resolution.

The `why_ref` profile enables the following compliance assertion:

> "The agent did not decide what this transaction means. The meaning was
> established upstream by human-reviewed regulatory rationale, signed by
> an authorised issuer, prior to this transaction. The evidence envelope
> proves it."

### 5.2 Local / Offline Agent Profile

OBO-REQ-020: For local and consumer-side agents operating without
continuous network connectivity:

1. The OBO Credential MUST set `offline_verifiable: true`.
2. The signing key MUST be distributed to the verifier in advance or
   embedded in a pre-installed trust anchor.
3. The OBO Evidence Envelope MUST be sealable without network access.
4. Evidence envelopes MAY be batched and submitted to a corridor or
   audit endpoint when connectivity is restored.

This profile covers the dominant consumer case: device-local agents
(personal AI assistants, health agents, wallet agents) that cannot
perform online authorization re-resolution at execution time.

### 5.3 Corridor-Bound Profile

When transactions occur through a governed corridor (such as aARP):

1. The corridor MAY issue the OBO Evidence Envelope on behalf of the
   originating agent.
2. The `corridor_ref` field MUST be populated.
3. The corridor's route proof MUST be referenced in `route_proof_ref`.
4. The corridor binding does not transfer liability from the agent to
   the corridor — the OBO Credential remains the agent's responsibility.

### 5.4 Multi-Step Transaction Profile

For orchestrated multi-step transactions (e.g. book + pay + confirm):

1. Each step produces its own OBO Evidence Envelope.
2. Each envelope references the prior step via `prior_evidence_ref`.
3. The `obo_credential_ref` is consistent across all steps (same
   credential governs the plan).
4. The `action_class` in each step envelope MUST be within the
   credential's `action_classes`. A single write-bearing step in a
   plan constrains the entire plan.

#### 5.4.1 Multi-agent chains and the originating human

When a transaction passes through multiple agents — a user agent
delegating to a booking agent delegating to a payment agent — the same
accountability principle applies at every hop:

- The `principal_id` in every credential in the chain MUST trace to the
  originating human who initiated the transaction. Intermediate agents
  MUST NOT issue credentials that substitute a different principal.
- The `why_ref` rationale carried by the originating credential is the
  authority root for the entire chain. Sub-credentials and derived
  credentials in the chain reference the same rationale root; they do
  not create new ones.
- Each agent in the chain is identified by its own `agent_id` and
  operated by its own `operator_id`, making per-hop accountability clear.
  But the chain of human authority — the `principal_id` and `why_ref` —
  does not change as the delegation travels.

**Human-in-the-loop in multi-agent chains.** When any step in a
multi-agent chain requires human confirmation, the human to consult is
the `principal_id` of the originating credential — the person who
started the chain. This is not an open question for deployments to
resolve case-by-case. The OBO credential model makes it a structural
invariant: authority originates with a named human, and that human
remains the authority root regardless of how many agents the delegation
passes through.

This design is intentional. Chains where each agent re-delegates to the
next and creates a new authority root obscure accountability and create
gaps that regulators cannot audit. OBO does not prohibit multi-agent
architectures, but it requires that human authority at the root of the
chain remain traceable and unchanged throughout.

OBO's model is an **invariant-chain model**, not a re-issuance model.
The originating credential is issued once by the operator on behalf of
the human principal. Downstream agents carry that credential's
`principal_id` and `why_ref` forward — they do not issue new
credentials that substitute a fresh principal or a new rationale root.
Scope constraints narrow at each hop through corridor policy and action
class ceilings, not through credential re-issuance. This is the
structural property that makes the originating human findable and
auditable at every point in the chain.

### 5.5 Multi-Hop Assertion Model

Multi-agent chains involve three structurally distinct assertion types.
Conflating them is the source of most multi-hop identity and
authorization errors.

**Identity assertion** — who the principal is. In OBO this is
`principal_id`: a stable, pseudonymous identifier for the originating
human. It travels with the credential but is minimised by design. Raw
end-user identity assertions (session tokens, ID tokens, authentication
receipts) MUST NOT be forwarded across agent hops unless the receiving
agent is explicitly in scope for the identity domain that issued them
and the principal has consented to that forwarding. The default is
non-forwarding.

**Delegation assertion** — what the agent is allowed to do on the
principal's behalf for this action. In OBO this is the OBO Credential
itself: `intent_namespace`, `action_classes`, `scope_constraints`,
`why_ref`, and `expires_at`. The delegation assertion travels hop-by-hop
and is the primary authorization input for each corridor. It must be:

- *turn-by-turn*, not indefinite — `expires_at` bounds every hop
- *narrow in scope* — action class and scope constraints MUST NOT widen
  across hops (non-amplifying)
- *audience-bound* — `corridor_binding` constrains where the credential
  is valid
- *fail-closed* — if the delegation assertion is absent, expired, or
  outside the receiving corridor's policy ceiling, the action is denied

**Execution assertion** — the credential used to call the target service
or API. This is obtained locally by the receiving corridor or agent,
not forwarded from the calling agent. Each corridor acquires its own
execution credentials (service account, mTLS certificate, API token)
for the downstream system it governs. The calling agent never receives
or handles these credentials. This is the structural enforcement of
least privilege: authority is delegated, execution is local.

The operational pattern is:

> *Authenticate at entry. Delegate per action. Execute locally.
> Audit end-to-end.*

Authentication happens once at the trust boundary where the principal
enters the system. Every subsequent action is governed by a bounded
delegation assertion. Every execution uses credentials local to the
receiving corridor. Every hop produces an OBO Evidence Envelope. The
end-to-end audit chain is assembled from per-hop envelopes linked by
`prior_evidence_ref` and the shared `principal_id` and `why_ref`.

**Cross-organisation chains.** There is no universal credential domain
across all organisations and APIs. Cross-organisation execution cannot
rely on token portability — it must rely on delegated authority. The
OBO Credential is the portable delegation artifact; execution
credentials remain local to each organisation's corridor. This is the
only design that composes correctly across organisational trust
boundaries without requiring a shared authorization server.

Forwarding bearer tokens across trust boundaries SHOULD be prohibited.
The reasons are structural, not stylistic:

- *Audience mismatch.* A token minted for the source domain or API is
  not valid for the target API. Accepting it is authority confusion.
- *Scope amplification risk.* A forwarded token may carry broader
  permissions than the target action requires. Local minting lets the
  target corridor issue minimum scope for that exact call.
- *Policy control loss.* The target domain cannot enforce its own
  authorization policies, consent requirements, or risk checks against
  a foreign bearer token it did not issue.
- *Revocation and TTL misalignment.* The source token's lifetime and
  revocation semantics may not match the target domain's risk model.
  A locally minted token can be short-lived and bound to the specific
  action, turn, or tool call.
- *Attribution blur.* Forwarding obscures who authorized what at which
  boundary. Local exchange creates an explicit chain: origin delegation
  → target token → target action, which is the auditable record.

---

## 6. Verification

### 6.1 Credential Verification

A verifier receiving an OBO Credential MUST:

1. Verify the cryptographic signature against the declared `issuer_id`.
2. Confirm `expires_at` has not passed.
3. Confirm `credential_digest` matches the recomputed digest of the
   canonical serialisation.
4. Confirm the `intent_namespace` is within the verifier's accepted
   namespaces.
5. Confirm the declared `action_classes` are within the verifier's
   accepted action class ceiling for the target operation.

### 6.2 Evidence Envelope Verification

A verifier receiving an OBO Evidence Envelope MUST:

1. Confirm `evidence_digest` matches the recomputed digest.
2. Confirm `credential_digest_ref` matches the digest of the referenced
   OBO Credential.
3. Confirm `action_class` is within the `action_classes` of the
   referenced credential.
4. Confirm `outcome` is consistent with the claimed action class (a
   `deny` outcome with action class `D` is valid; an `allow` outcome
   with action class `D` on a credential scoped to `A` only is not).
5. When `why_ref` is present and the lane is regulated: confirm
   `why_ref.rationale_digest` is non-empty.

### 6.3 Fail-Closed Behaviour

OBO-REQ-030: Verifiers MUST fail closed. An envelope that fails any
verification step MUST be rejected. Partial verification is not
permitted for regulated lanes. For open lanes, verifiers MAY emit a
warning and continue with degraded trust, but MUST log the failure.

---

## 7. Relationship to Existing Standards

### 7.1 OAuth 2.0 Token Exchange (RFC 8693)

RFC 8693 defines token exchange for delegation between known parties
sharing authorization infrastructure. OBO is complementary, not
competing: RFC 8693 may be used as the `binding_proof_ref` mechanism
in enterprise deployments where shared authorization infrastructure
exists. OBO covers the cases RFC 8693 does not: one-time transactions,
unknown counterparties, local/offline agents.

The structural limitation of OAuth 2.0 in agentic contexts is not its
delegation model but its verification model: every credential
verification requires the authorization server to be live, reachable,
and in a prior relationship with the verifier. In a world of millions
of first-contact agent transactions this is a topology impossibility.
The DNS Anchoring Profile (Appendix D) removes this runtime dependency:
the authorization server issues the credential once; DNS provides
stateless, universally accessible key material for verification. The
authorization server is not required at transaction time.

### 7.2 W3C Verifiable Credentials

W3C VCs may be used as the OBO Credential format. The OBO Credential
fields map onto standard VC claims. This specification does not mandate
VC format but is compatible with it. The OBO Evidence Envelope has no
direct VC equivalent — it is a new artefact.

### 7.3 A2A Agent Protocols

A2A protocols that enumerate agent tool surfaces are incompatible with
the OBO intent-first design principle. The OBO model explicitly rejects
tool enumeration as a trust primitive — it creates reconnaissance
surfaces without providing evidence of bounded execution. OBO is not
a replacement for A2A transport; it is the evidence layer that A2A
transport lacks.

---

## 8. Security Considerations

### 8.1 Credential Replay

An OBO Credential is portable and may be replayed. Mitigations:

- Short-lived credentials (`expires_at` close to `issued_at`) limit
  the replay window.
- Corridor-binding (`corridor_ref`) restricts a credential to a
  specific corridor, preventing cross-corridor replay.
- The `credential_digest_ref` in the evidence envelope detects
  credential substitution after the fact.

**Cascade revocation in delegation chains.** When `delegation_depth`
and `parent_credential_ref` are present, revocation of a credential
MUST be treated as revocation of all credentials that carry it as a
`parent_credential_ref`, transitively. A verifier that checks the
nullifier sink (`_obo-null`) for a credential in a chain MUST also
check every ancestor credential referenced by `parent_credential_ref`
up to the origin. A chain is valid only if every member is valid.

This property applies only to credentials that carry `delegation_depth`.
Base credentials (single-hop, no delegation chain) are unaffected.

### 8.2 Intent Manipulation

The `intent_hash` in the evidence envelope binds the sealed record to
the specific normalised intent. Any manipulation of the intent between
admission and execution invalidates the hash. Verifiers MUST reject
envelopes where the intent hash does not match the admitted intent.

### 8.3 Action Class Escalation

An agent claiming action class `A` in its credential but executing a
class `B` or higher action produces an evidence envelope where
`action_class` violates the credential constraint. OBO-REQ-014
requires verifiers to reject this. Corridors SHOULD enforce action
class ceilings before execution, not only at verification time.

### 8.4 Upstream Rationale Revocation

When `why_ref` is present, the `rationale_id` may be revoked by the
upstream rationale authority. Verifiers in regulated lanes SHOULD
perform online revocation checks when network access is available.
Offline verifiers MUST treat a `why_ref` with a known-revoked
`rationale_id` as invalid when connectivity is restored.

### 8.5 Model Identity: Attestation, Not Proof of Computation

OBO Evidence Envelopes may carry a `model_identity_ref` field
identifying the LLM or model that the operator asserts was used during
execution of the transaction turn. This section explains precisely what
that claim represents, what it does not represent, and why the
accountability model is nonetheless sound.

**OBO is mechanism-agnostic for model identity.** The protocol does not
mandate how a model identity claim is produced — only that it is sealed
in the evidence envelope and bound to the operator's accountability
chain. Implementations MUST NOT require any proprietary, licensed, or
patented technology to produce or verify a `model_identity_ref` claim.
Any mechanism that produces a stable identifier or digest for the model
in use — deployment manifest hash, TEE enclave report, open
fingerprinting technique, or simple operator declaration — is a
conformant source for this field.

#### 8.5.1 What the sealed claim is

A `model_identity_ref` in a signed evidence envelope is an
**operator-attested assertion**. The operator — a legal entity
identified by `operator_id` and bound by the governance pack referenced
in `governance_framework_ref` — asserts that a named model was used
during this transaction turn. That assertion is:

- Sealed at transaction time, tamper-evident, and bound to the turn via
  the envelope signature.
- Traceable to a legal entity who can be held accountable for its
  accuracy.
- Verifiable by any party who can resolve the operator's DNS-anchored
  signing key.

#### 8.5.2 What the sealed claim is not

The sealed claim is **not cryptographic proof of computation**. No
currently deployed general-purpose system can provide externally
verifiable proof that a specific set of neural network weights executed
a specific forward pass on a specific input. This is a fundamental
limit of current AI infrastructure, not a gap specific to OBO.

Several technique classes have been proposed to narrow this gap:

- **Structural fingerprinting**: measuring the geometry of a model's
  internal activation distributions or output distributions during a
  forward pass to produce a stable identity digest. Published research
  demonstrates this can distinguish models across architecture families
  without weight access, including via API-only regimes. Some
  implementations of this technique are subject to patent protection;
  OBO does not reference or require any specific implementation.
- **Trusted execution environments (TEE)**: running model inference
  inside a hardware enclave and producing a signed attestation report.
  The report binds the enclave identity, not the model weights directly.
- **Supply-chain attestation**: signing the model artifact at build time
  and verifying the artifact hash at deployment. Establishes which file
  was loaded; does not establish which weights were evaluated per turn.

Each of these approaches establishes one level of evidence but all
ultimately terminate in an assertion made by some party who signed it —
the measurement operator, the enclave issuer, or the build pipeline.
The verification chain does not escape the assertion model; it relocates
where the assertion is made. Critically, each approach also requires an
**enrolled reference baseline**: someone must certify what the authentic
model's fingerprint, enclave identity, or artifact hash is. That
enrollment is itself an assertion.

This is not a flaw. It reflects how accountability works in every
regulated domain. A licensed tradesperson certifies that a specific
procedure was performed using specific tools. That certification is
signed, legally binding, and creates accountability. It is not a video
recording of every instrument used. The accountability model works
because a named legal entity made a signed claim and can be held to it
— not because the internal computation was proven.

#### 8.5.3 Why the accountability model is sound within these limits

OBO's design is explicit about where accountability sits: with the
**operator**, not the agent. The operator is a legal entity — a company,
a regulated PSP, a licensed service provider — who:

1. Deployed the agent and its underlying model.
2. Issued or accepted the OBO Credential bounding the agent's scope.
3. Sealed the Evidence Envelope asserting what occurred, including which
   model was used.
4. Is identified by `operator_id` and bound to a governance pack whose
   digest is anchored in DNS.

If a `model_identity_ref` claim is false — if the operator asserted
model X was used when model Y actually ran — the legal consequences
attach to the operator as the signing party. This is the same
accountability structure used in payment networks, regulated professions,
and supply-chain certifications: a named legal entity makes a signed
assertion and is liable for its accuracy.

The relevant question for a verifier or regulator is not *"can I prove
computationally that this model ran?"* but *"is there a named,
accountable legal entity who has signed a claim that this model ran,
and can I hold them to that claim if it proves false?"* OBO answers yes
to the second question. No current general-purpose system answers yes to
the first without relying on a trusted assertion at some layer.

#### 8.5.4 Threat: operator substitution of model without updating assertion

If an operator silently rotates the model behind a deployment without
updating the `model_identity_ref` in subsequent evidence envelopes, the
envelopes will contain a stale or false model identity claim. This is a
breach of the operator's obligations under the governance pack, not a
failure of the OBO protocol.

Mitigations available within the OBO framework — all implementable
without proprietary technology:

- **Governance pack binding**: the `governance_framework_ref` (PACT
  pack) specifies the ontology and execution contract under which the
  agent operates. Model rotation that changes the agent's effective
  behaviour may constitute a governance pack violation independently of
  the model identity claim.
- **Corridor monitoring**: corridors operating under regulated tiers MAY
  require periodic re-attestation of model identity claims and SHOULD
  treat stale or unverifiable claims as a corridor policy violation.
- **Supplementary evidence digest**: operators MAY include in
  `model_identity_ref` a digest produced by any open fingerprinting
  technique, TEE attestation report, or deployment manifest signature.
  The choice of technique is the operator's; OBO seals and attributes
  whatever digest is provided. No licensed implementation is required or
  preferred.

#### 8.5.5 Relationship to draft-klrc-aiagent-auth §7 and §14

draft-klrc-aiagent-auth [KLRC 2026] identifies a related threat class:
model substitution under valid agent credentials, where workload
identity, artifact attestation, and API authentication all remain valid
while the underlying model changes. The draft notes that §14 (Security
Considerations) is reserved for future work.

OBO's position is that this threat is real and correctly named, and that
the appropriate response is to seal an operator-attested model identity
claim in the per-turn evidence record — not to claim that the protocol
can independently verify internal computation. The per-turn evidence
architecture DOP uses (one signed attestation per pipeline turn,
chained via `prev_attestation_hash`) demonstrates that turn-level model
identity attestation is implementable and composable with existing
workload identity chains using only open standards.

The threat cannot be eliminated by protocol means given current AI
infrastructure. It can be made **attributable**: a named legal entity
makes a signed claim, that claim is sealed in a tamper-evident record,
and the entity is accountable if the claim proves false. That is what
OBO provides, and it is consistent with how accountability is
established in every other regulated domain.

OBO intentionally does not specify, endorse, or require any particular
model identity measurement technique. The evidence envelope is the
accountability layer. The measurement mechanism is the operator's choice
and the corridor's policy — both of which can be satisfied with open,
unencumbered technology.

### 8.6 Cross-Domain Trust Bootstrapping

A verifier receiving an OBO Credential from an agent it has never
previously interacted with needs to answer two questions: is the
operator's signing key trustworthy, and is the governance framework the
operator claims in force?

OBO answers both questions through DNS, without requiring out-of-band
trust anchor exchange, federation metadata endpoints, or pre-configured
certificate authorities between the parties. The operator publishes:

- `_obo-key.<operator-domain>` — the signing key or key digest used to
  sign OBO Credentials (sub-profile D.1)
- `_obo-gov.<operator-domain>` — a digest of the governance framework
  the operator is committed to (sub-profile D.2)

Any verifier with DNS access can resolve these records and verify the
credential signature and governance binding without any prior
relationship with the operator. The trust root is DNS, which is
universally accessible and DNSSEC-signable. See Appendix D for the full
DNS Anchoring Profile.

**Replay prevention at first-contact.** OBO addresses credential replay
through two independent mechanisms that do not require shared session
state between domains:

1. `expires_at` — every OBO Credential carries an expiry. Verifiers
   MUST reject credentials past their expiry. Short-lived credentials
   (minutes to hours) are RECOMMENDED for cross-domain transactions.

2. The nullifier sink (`_obo-null.<operator-domain>`, sub-profile D.3)
   — the operator publishes a Merkle root of revoked credential IDs.
   Verifiers MAY check the nullifier root for high-value or regulated
   transactions where replay risk is material.

These two mechanisms together bound both the replay window (expiry) and
enable explicit revocation (nullifier) without requiring the verifier
and issuer to share session infrastructure.

### 8.7 High-Impact Operations and Approval Evidence

For Class C (irreversible write) and Class D (systemic) operations,
generic approval — a single human acknowledged a notification — is
insufficient for regulated and high-stakes deployments. The approval
record must be independently verifiable: who approved, at what
assurance level, within what time window, and whether the approvers
were independent of each other and of the principal.

OBO defines a portable `approval_evidence` structure (Section 4.4) for
this purpose. The approval *policy* (mandatory MFA tier, required role
classes, n-of-m threshold, operation windows, segregation of duties)
remains deployment-defined and out of scope for this specification.
The evidence *structure* is standardised so that a verifier receiving
an evidence envelope from any OBO-conformant deployment can inspect and
validate the approval record using the same fields.

The agent does not initiate or participate in the approval flow. Approval
is obtained by the corridor or an upstream policy authority prior to
execution, and sealed into the evidence envelope. If the corridor
requires `approval_evidence` and it is absent, expired, underthreshold,
or fails segregation checks, the corridor MUST reject the operation
before execution. There is no fallback path.

### 8.8 LLM Output Is Not the Authorization Boundary

**Scope boundary.** The internal security architecture of LLM-based
agents — single-model, dual-model, self-critique, guard-model
orchestration, prompt injection mitigations, and post-generation safety
filters — is out of scope for this specification. OBO does not prescribe
how an agent is implemented internally. It treats agents as principals
presenting credentials and evidence, not as implementations to be
audited.

**What is in scope** is the set of authorization invariants that MUST
hold at every externally visible action boundary, regardless of what
model, pipeline, or internal architecture the agent uses:

- LLM output MUST NOT be the final authority for execution. An LLM
  generating an action request does not authorize that action. Every
  externally visible action MUST be gated by a deterministic
  authorization boundary — the corridor's policy engine — that is
  external to the LLM and not subject to prompt manipulation.

- Execution MUST be gated by a deterministic policy boundary. The
  corridor checks the OBO Credential, validates action class, enforces
  scope constraints, and applies corridor predicates before any action
  executes. An LLM that generates an out-of-scope action will be
  rejected at this boundary regardless of how the output was produced.

- Delegation artifacts MUST be bounded and non-amplifying. Intent,
  audience, scope, actor chain, and TTL are fixed at credential
  issuance. The LLM cannot extend them at inference time.

- Missing trust mapping, required consent, or required step-up MUST
  fail closed. There is no fallback path that routes around the
  authorization boundary on behalf of an agent that has generated
  an unauthorized action.

- Authorization MUST be re-evaluated at each effectful step. Session-level
  authentication does not imply authorization for subsequent tool
  invocations. Each action that produces an externally visible state
  change — a write, a payment, a network call, a data release — requires
  an independent authorization check at execution time. Global session
  authorization does not carry forward to individual tool actions.

- Evidence MUST bind the request, delegation artifact, policy context,
  and execution outcome. The evidence envelope is sealed after the
  corridor's decision — not after the LLM's output. If the corridor
  rejects the action, the rejection is the evidence.

These invariants hold for all agents regardless of their internal
architecture. A dual-model agent with a guard evaluator still operates
within the same corridor boundary. A single-model agent with no
internal safety layer still cannot execute actions the corridor's
policy rejects. The authorization boundary is external, deterministic,
and not delegatable to the LLM.

---

## 9. Privacy Considerations

OBO credentials and evidence envelopes cross organisational boundaries
by design. A target receiving an OBO Credential learns something about
the originating operator. The question is how much — and whether what
is revealed is the minimum necessary for the transaction or an
inadvertent disclosure of internal organisational detail.

### 9.1 The minimum disclosure principle

OBO-REQ-040: Operators SHOULD construct credentials and evidence
envelopes to disclose the minimum information necessary for the
receiving party to verify the presented claims and admit or reject
the intent.

This is not merely a privacy preference. Excess disclosure in a
credential that crosses an organisational boundary reveals internal
structure — team names, department codes, role hierarchies, internal
workflow identifiers — to counterparties who have no need of that
information and no obligation to protect it. In regulated contexts,
such disclosure may itself constitute a data protection violation.

### 9.2 Identifier construction

**`agent_id` and `operator_id`** are domain-scoped identifiers. The
operator domain is intentionally public — it is the accountable legal
entity whose key is anchored in DNS. The agent sub-identifier within
that domain SHOULD be an opaque or role-scoped token that does not
encode internal organisational structure.

```
Disclose less:  agent-7f3a.corp.example          (opaque token)
Disclose more:  agent.finance-dept.team-alpha.corp.example
                (reveals internal hierarchy to every counterparty)
```

**`principal_id`** identifies the delegating human. It SHOULD be a
pseudonymous identifier tied to the delegation relationship, not an
internal username, employee ID, or role title. The principal's legal
identity is relevant to the operator; it is rarely relevant to the
target service.

### 9.3 Intent phrase minimization

The `intent_phrase` is normalised before hashing and is visible to
the target. It SHOULD convey the intent class and scope sufficient
for admission decisions without embedding internal business process
identifiers, workflow names, or system references.

```
Sufficient:  "initiate payment USD 5000 to supplier"
Excessive:   "process Q1-2026 vendor invoice batch for APAC
              procurement workflow ref INV-2026-00412"
```

The intent hash binds the evidence to the specific intent. The phrase
itself does not need to contain internal identifiers to serve that
function — the hash is the binding, not the text.

### 9.4 Rationale reference opacity

The `why_ref` field carries a pointer to the upstream human-approved
rationale. The `rationale_id` within `why_ref` SHOULD be an opaque
token issued by the RTGF or rationale authority — not a descriptive
URI that reveals internal approval workflow identifiers to the target.

The target does not need to know the internal structure of the
rationale system. It needs to know that a valid rationale exists and
is reachable. An opaque token satisfies that requirement; a descriptive
URI leaks internal process detail.

### 9.5 DNS-published corridor predicates

`_obo-crq` DNS records publish corridor admission requirements. These
records are publicly resolvable by any party. Operators constructing
corridor admission predicates SHOULD be aware that the published
requirements reveal the regulatory posture of the corridor — required
compliance tiers, jurisdiction constraints, and governance framework
references — to any observer who resolves the record.

This disclosure is intentional and necessary for the DNS verification
model to work. Operators SHOULD ensure that what is published reflects
only the minimum admission requirements and does not embed internal
policy identifiers beyond what verification requires.

### 9.6 Evidence envelope sharing

The OBO Evidence Envelope is an accountability record. In most
transaction classes it is retained by the operator and produced only
in the event of a dispute, regulatory inquiry, or audit. Operators
MUST NOT routinely share evidence envelopes with counterparties beyond
what is required by the corridor profile or applicable law.

In regulated corridors where the evidence envelope is shared (for
example, with a payment network or dispute arbitrator), the corridor
profile SHOULD specify which fields are shared and under what data
processing basis. Sharing an envelope that contains `principal_id` or
`intent_phrase` with a counterparty constitutes personal data transfer
in many jurisdictions and requires an appropriate lawful basis.

### 9.7 The D.4b suffix privacy circuit

Appendix D.4b describes a gnark PLONK zero-knowledge circuit for
nullifier suffix privacy. When corridor admission requires proof that
a nullifier epoch root is satisfied without revealing which specific
nullifier was consumed, the ZK circuit provides this proof without
disclosing the nullifier value to the corridor operator. Implementers
processing high-volume regulated corridors SHOULD consider whether
nullifier disclosure creates a linkability risk and whether the D.4b
circuit is appropriate for their deployment.

### 9.8 Cross-domain activity correlation

Stable agent identifiers appearing across multiple domains enable
cross-domain activity correlation — the same concern raised for
WIMSE/SPIFFE workload identifiers. This concern applies differently
depending on whether the agent represents a legal entity or a natural
person, and the two cases must not be conflated.

#### 9.8.1 Operator agents: correlation is the accountability mechanism

When an agent represents an operator — a company, a regulated PSP,
a licensed service provider — cross-domain correlation of that agent's
`operator_id` and `agent_id` is not a privacy problem. It is the
accountability model working as designed.

A company's network traffic is correlatable across the internet today.
A company's representative signs in at a visitor desk and is
identified. A corporate card transaction is attributed to the issuing
entity. In each case, the legal entity accepts identifiability as the
price of operating in a regulated environment. The same applies to
operator agents: the operator's domain is public by design, anchored
in DNS, and intentionally consistent across all transactions that
operator's agents conduct.

OBO does not support anonymous operators. An operator who cannot be
identified cannot accept legal accountability for their agent's
actions. Correlation of `operator_id` across domains is a feature of
the accountability model, not a flaw in its privacy posture. Treating
it as a privacy problem confuses the accountability layer with the
personal privacy layer.

#### 9.8.2 Consumer agents: correlation reveals personal behaviour

When an agent represents a natural person — a consumer whose personal
agent books travel, consults medical services, and initiates payments
— the privacy calculus is different. A stable `agent_id` appearing at
Ryanair, a hotel, a hospital, and a payment provider within a day
reveals a personal behaviour profile that the individual did not
directly disclose to any of those parties.

OBO addresses this through `principal_id` pseudonymisation (§9.2) and
short-lived credentials. The `principal_id` need not be the person's
legal name or internal identifier — it is a pseudonymous delegation
anchor tied to the specific operator relationship. The operator knows
the mapping; the target does not.

Consumer agent deployments in regulated corridors SHOULD use:
- Short credential lifetimes to limit the correlation window
- Pseudonymous `principal_id` values scoped to the operator relationship
- Opaque `agent_id` sub-identifiers that do not encode personal context

Full pairwise identifiers — unique per target organisation — are
feasible for `agent_id` sub-identifiers at the cost of operational
complexity (each pair requires a separate credential). Pairwise
`operator_id` values are not feasible: the operator must be
consistently identifiable for legal accountability.

#### 9.8.3 The resolution boundary

The question "can an agent prove properties without revealing full
identity?" has a bounded answer in the OBO model:

- An agent can prove **scope** (`intent_class`, `action_classes`) without
  revealing the full principal identity — the credential carries these
  fields independently.
- An agent can prove **governance** (`governance_framework_ref`,
  `corridor_ref`) without revealing internal organisational detail.
- An agent **cannot** prove operator accountability without revealing the
  operator — accountability requires a resolvable legal entity.

The operator identity boundary is not a gap. It is the architectural
choice that makes legal accountability possible. Anonymous agents
cannot be accountable agents. Any framework that offers full agent
anonymity in regulated corridors must resolve this contradiction
separately — OBO does not attempt to.

---

## 10. Acknowledgements and Design Philosophy

### 9.1 Why an Open Standard

This specification is published as an IETF Internet-Draft rather than
a product specification or proprietary framework. That choice is
deliberate and worth stating explicitly.

Agentic commerce is in its earliest months as a real operational
problem. The decisions made now about trust models, evidence formats,
and corridor architectures will shape the infrastructure that billions
of agent transactions run on. History is unambiguous about what
happens when this window is missed: proprietary networks calcify,
fragmentation follows, and the migration cost falls on everyone except
the network operators.

HTTP beat proprietary web protocols. SMTP beat proprietary email
networks. ISO 20022 is displacing proprietary financial message
formats. TCP/IP beat everything before it. The open standard always
wins at scale. The question is only how long the proprietary
intermediary delays it and how much damage the fragmentation causes
in the meantime.

The OBO specification is designed so that any agent, in any
jurisdiction, operating under any governance framework, can participate
in agentic commerce without joining an approved network, paying for a
co-signature, or seeking permission from a central authority. The trust
anchor is DNS — infrastructure that is already universal, already
operated by governments and institutions worldwide, and not owned by
anyone in this conversation.

A rising tide raises all boats. A well-specified open standard for
agentic evidence is more valuable to every participant — including
commercial implementers — than a proprietary network that controls
who may participate. Commercial products built on open standards have
a long and successful history. Commercial products that attempt to
own the standard do not.

### 9.2 Invitation to Contributors

The authors welcome review, implementation experience, and co-authorship
from any party working on agentic trust, evidence standards, or
corridor protocols. Specifically:

- Implementation experience with the OBO Credential or Evidence
  Envelope field semantics.
- Operational experience with DNS-anchored key publication at scale
  (operators with DKIM deployment experience are especially welcome).
- Review of the DNS Anchoring Profile (Appendix D), particularly the
  D.4b gnark PLONK suffix privacy construction, which requires
  independent cryptographic review before normative status.
- Jurisdiction-specific profiles: parties operating regulated agent
  corridors in specific jurisdictions (payments, healthcare, legal)
  with knowledge of local regulatory requirements.
- Evidence from deployment: any party that implements OBO and produces
  evidence envelopes from real agentic transactions is encouraged to
  report implementation experience against this draft.

The goal is a standard that works because it has been tested against
real deployments, not one that is merely theoretically correct.

### 9.3 Acknowledgements

The authors acknowledge the foundational work of Vishnu (IACR ePrint
2025/2332) on DNS-anchored zk-SNARK proofs, which directly informed
Appendix D of this specification. The gnark library (ConsenSys)
provides the Go implementation path for the D.4b construction.

The design of the evidence chain is informed by the W3C PROV-O
provenance ontology and the ISO 20022 business model as an example
of what upstream concept authority looks like when it is done well.

---

## 11. IANA Considerations

This document requests no IANA actions at this time. A future revision
may request registration of the `application/obo-credential+json` and
`application/obo-evidence+json` media types.

---

## 12. References

### 12.1 Normative References

- [RFC2119] Bradner, S., "Key words for use in RFCs to Indicate
  Requirement Levels", BCP 14, RFC 2119, March 1997.
- [RFC8174] Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC
  2119 Key Words", BCP 14, RFC 8174, May 2017.
- [RFC8693] Jones, M. et al., "OAuth 2.0 Token Exchange", RFC 8693,
  January 2020.

### 12.2 Informative References

- [VC-DATA-MODEL] W3C, "Verifiable Credentials Data Model 2.0",
  https://www.w3.org/TR/vc-data-model-2.0/
- [PROV-O] W3C, "PROV-O: The PROV Ontology",
  https://www.w3.org/TR/prov-o/
- [ISO20022] ISO, "ISO 20022 Universal financial industry message
  scheme", https://www.iso20022.org
- [RTGF] Brown, K. et al., "Reference Token Generation Framework",
  draft-lane2-rtgf-01, 2026.
- [aARP] Lane2 Architecture, "Autonomous Agent Routing Protocol",
  work in progress.
- [EU-AI-ACT] European Parliament, "Regulation on Artificial
  Intelligence", 2024/1689, 2024.
- [PSD3] European Commission, "Payment Services Directive 3",
  proposed 2023.
- [PTX] Vishnu, A., "DNS-Anchored zk-SNARK Proofs: A Stateless
  Alternative to ACME Challenge-Response for Domain Control
  Validation", IACR ePrint 2025/2332, December 2025.
  https://eprint.iacr.org/2025/2332
- [RFC6376] Crocker, D. et al., "DomainKeys Identified Mail (DKIM)
  Signatures", RFC 6376, September 2011.
- [RFC4034] Arends, R. et al., "Resource Records for the DNS Security
  Extensions", RFC 4034, March 2005.

---

## Appendix A. OBO Credential Example

```json
{
  "obo_credential_id": "urn:obo:cred:2026:a1b2c3d4",
  "principal_id": "did:example:principal:alice",
  "agent_id": "urn:agent:lane2:travel-assistant:v1",
  "operator_id": "urn:org:lane2:ai",
  "binding_proof_ref": "urn:consent:2026:xyz789",
  "intent_namespace": "urn:lane2:ns:travel",
  "action_classes": ["A", "B"],
  "governance_framework_ref": "urn:pack:lane2:travel:sha256:abc123",
  "issued_at": 1743552000,
  "expires_at": 1743638400,
  "issuer_id": "urn:org:lane2:ai:issuer",
  "credential_digest": "sha256:def456..."
}
```

## Appendix B. OBO Evidence Envelope Example

```json
{
  "evidence_id": "urn:obo:ev:2026:e9f8g7h6",
  "obo_credential_ref": "urn:obo:cred:2026:a1b2c3d4",
  "credential_digest_ref": "sha256:def456...",
  "principal_id": "did:example:principal:alice",
  "agent_id": "urn:agent:lane2:travel-assistant:v1",
  "intent_hash": "sha256:book-hotel-dublin-2nights...",
  "intent_class": "urn:lane2:ns:travel:accommodation-booking",
  "action_class": "B",
  "outcome": "allow",
  "policy_snapshot_ref": "urn:policy:lane2:travel:v1.2.3",
  "governance_framework_ref": "urn:pack:lane2:travel:sha256:abc123",
  "sealed_at": 1743552300,
  "corridor_ref": "urn:aarp:corridor:lane2:travel:abc",
  "stage3_ref": "urn:payment:stripe:pi_xyz123",
  "evidence_digest": "sha256:ghi789..."
}
```

## Appendix C. Correspondence with OAuth Token Exchange Claims

*Status: Informative. This appendix is for readers familiar with OAuth
2.0 Token Exchange (RFC 8693) and WIMSE. It shows how OBO fields
correspond to OAuth token claims. OBO is not an OAuth profile and does
not require OAuth infrastructure.*

OAuth Token Exchange (RFC 8693) introduced the `act` and `may_act`
claims to express impersonation and delegation in JWT-based access
tokens. WIMSE workload identity builds on this to express agent-to-agent
delegation in service mesh and API gateway contexts. These are useful
mechanisms but do not fully specify the execution-time delegation
semantics required for multi-hop, cross-organisation agentic execution
(see §5.5).

The table below maps RFC 8693 / WIMSE claims to OBO fields. The
mapping is conceptual — OBO is not issued as a JWT access token and
is not obtained via a token exchange flow.

### C.1 Identity Claim Correspondence

| OAuth / WIMSE claim | Meaning | OBO equivalent | Notes |
|---|---|---|---|
| `sub` | Subject — the resource owner or principal on whose behalf the token is issued | `principal_id` | OBO requires this to be the originating human, invariant across the delegation chain (§5.4.1) |
| `act.sub` | Acting party — the entity currently acting on behalf of `sub` | `agent_id` | OBO additionally requires `operator_id` (accountable legal entity) alongside agent identity |
| `iss` | Token issuer | `issuer_id` | OBO issuer is the operator or an authorised credential issuer, not necessarily an AS |
| `aud` | Intended audience | `corridor_binding` | OBO binds to a corridor, not an API endpoint — the corridor enforces audience scoping |
| `exp` | Expiry | `expires_at` | OBO REQUIRES `expires_at`; short-lived credentials RECOMMENDED |
| `nbf` | Not-before | `issued_at` | OBO uses `issued_at`; not-before semantics are implicit |
| `may_act.sub` | Authorised actor for future exchange | Not directly expressed | OBO handles this through the originating credential's `agent_id` binding; sub-delegation uses `delegation_depth` (§3.2) |
| `scope` | Broad capability grant | `action_classes` + `intent_namespace` | OBO scopes by action severity class and intent namespace, not opaque strings |
| `authorization_details` (RAR, RFC 9396) | Fine-grained action authorization | `scope_constraints` + `intent_hash` | OBO seals the exact intent in `intent_hash`; `scope_constraints` carries resource bounds |

### C.2 What OAuth Token Exchange Does Not Specify

The `act` claim carries identity context — who is acting. It does not
specify:

- **Turn-boundedness.** OAuth access tokens are typically session-scoped
  or long-lived. OBO requires delegation to be turn-by-turn: each
  credential is short-lived and bound to the intent of that action.

- **Non-amplification across hops.** RFC 8693 does not require that each
  token exchange narrows scope. OBO requires it: action classes and
  scope constraints MUST NOT widen across delegation hops (§5.4.1,
  §3.2 `delegation_depth`).

- **Intent binding.** OAuth tokens carry scopes or `authorization_details`
  but do not seal the exact normalised intent phrase. OBO's `intent_hash`
  binds the evidence record to the specific action that was authorized,
  making it a dispute anchor (§1.6).

- **Cross-domain execution semantics.** RFC 8693 describes token exchange
  mechanics; it does not specify that receiving domains must mint local
  execution credentials, prohibit bearer token forwarding, or fail closed
  on missing trust mapping. OBO specifies all three (§5.5, §8.8).

- **Originating human invariance.** In OAuth delegation chains, `sub`
  may change at each exchange if the acting party becomes the new subject.
  OBO's `principal_id` is invariant — it always identifies the originating
  human, regardless of how many agents the delegation passes through (§5.4.1).

### C.3 Deployment Coexistence

OBO does not replace OAuth infrastructure. In deployments that use
OAuth-secured APIs:

- The agent presents its OBO Credential to the corridor.
- The corridor validates the OBO Credential and, if admission succeeds,
  uses its own OAuth client credentials or token exchange to obtain the
  execution credential for the downstream API.
- The downstream API sees a normal OAuth access token; it does not need
  to be OBO-aware.
- The OBO Evidence Envelope captures the corridor's decision and the
  execution outcome, independently of the OAuth token lifecycle.

This is the execution assertion pattern described in §5.5: OBO handles
delegation authority; OAuth handles execution plumbing. They compose
without either replacing the other.

---

## Appendix D. Relationship to DOP Evidence Contract

The DOP Evidence Contract (DOP-013) is a conforming implementation of
the OBO Evidence Envelope, extended with pipeline-specific fields
(stage artifacts, rubric evaluation, tool execution leases). The
mapping is:

| OBO Field | DOP EvidenceContract Field |
|---|---|
| `evidence_id` | `TraceID` |
| `obo_credential_ref` | `ExecutionWarrant.WarrantID` |
| `principal_id` | `SEA.SessionID` (+ delegation chain) |
| `agent_id` | `DOPInstanceID` |
| `intent_hash` | `NormalisedPhraseHash` |
| `intent_class` | `RouteDecision.IntentClass` |
| `action_class` | `ExecutionWarrant.ActionClass` |
| `outcome` | `Decision.Outcome` |
| `policy_snapshot_ref` | `PolicySnapshotID` |
| `governance_framework_ref` | `OntologySnapshotID` |
| `why_ref.*` | `WhyRefRationaleID/Digest/DerivationDigest` |
| `evidence_digest` | `ContractHash` |

## Appendix D. DNS Anchoring Profile

*Status: Informative. This appendix describes an optional anchoring
profile. Sub-profiles D.1 through D.3 are deployable with existing
DNS tooling. Sub-profile D.4 references an experimental zk-SNARK
construction [PTX] and is flagged for discussion with contributors.*

*Discussion note for contributors: The authors would welcome review
of this appendix from parties with experience in DKIM key management,
DNSSEC operational deployment, and zero-knowledge proof systems. The
D.4 sub-profile in particular is an early design sketch and has not
been security-reviewed independently of [PTX].*

### D.1 Motivation

OAuth 2.0 and PKI-based verification models require the verifying
party to have a live connection to an authorization server or CA at
verification time. For first-contact agentic transactions — two agents
with no prior relationship and no shared authorization infrastructure
— this is not achievable in general.

DNS is the one universally accessible, globally distributed, DNSSEC-
signed key-value store that every networked device already uses.
Publishing OBO trust material in DNS removes the runtime dependency on
authorization servers and CA infrastructure while preserving
cryptographic verifiability.

The DNS Anchoring Profile defines four sub-profiles of increasing
capability, each independently deployable.

### D.2 Record Naming Convention

All OBO DNS records use underscore-prefixed names to avoid collision
with operational DNS records, following the convention established by
DKIM [RFC6376] and SRV records.

The general form is:

```
_obo-<purpose>.<qualifier>.<owner-domain>   TXT   "<value>"
```

DNSSEC signing of OBO records is RECOMMENDED. Verifiers SHOULD treat
unsigned records as lower-assurance and MUST NOT treat them as
equivalent to DNSSEC-signed records for regulated lane verification.

### D.3 Sub-Profile D.1: Operator Signing Key (obo-dns-key)

An operator MAY publish its OBO Credential signing key in DNS,
following the DKIM [RFC6376] key record pattern:

```
_obo-key._domainkey.<operator-domain>   TXT
  "v=obo1; k=ed25519; p=<base64url-encoded-public-key>"
```

Field definitions:

| Field | Value |
|---|---|
| `v` | Protocol version. MUST be `obo1`. |
| `k` | Key type. `ed25519` RECOMMENDED. `rsa` permitted for legacy deployments. |
| `p` | Base64url-encoded public key. |

**Credential verification using obo-dns-key:**

1. Extract the domain component of the `issuer_id` field from the
   OBO Credential.
2. Resolve `_obo-key._domainkey.<issuer-domain>` TXT record.
3. Verify the credential signature against the published public key.
4. No authorization server contact is required.

This sub-profile is deployable today using existing DNS infrastructure
and Ed25519 tooling. It is the minimum DNS anchoring profile.

### D.4 Sub-Profile D.2: Governance Pack Digest (obo-dns-gov)

An operator MAY publish the canonical digest of its current governance
pack (ontology pack, policy snapshot) in DNS:

```
_obo-gov.<pack-version>.<operator-domain>   TXT
  "sha256=<hex-digest>; issued=<unix-epoch>; expires=<unix-epoch>"
```

**Credential verification using obo-dns-gov:**

1. Extract the `governance_framework_ref` from the OBO Credential.
   The ref MUST be a DNS-resolvable name or resolve to one via a
   registry lookup.
2. Resolve the corresponding `_obo-gov` TXT record.
3. Compare the published `sha256` digest against the
   `governance_framework_ref` digest carried in the credential.
4. Confirm the record's `expires` has not passed.

A verifier that cannot resolve the governance pack record for a
regulated lane MUST fail closed. For open lanes a warning MAY be
emitted.

This sub-profile enables pack revocation by DNS record removal:
removing the TXT record causes all credentials referencing that pack
version to fail DNS-gov verification, without requiring a live
revocation endpoint.

### D.5 Sub-Profile D.3: Credential Nullifier Epoch Root (obo-dns-null)

To support offline revocation checking without CRL distribution
points, an operator MAY publish a Merkle root of credential nullifiers
for each epoch:

```
_obo-null.<YYYY-MM>.<operator-domain>   TXT
  "root=sha256:<merkle-root-hex>; epoch=<YYYY-MM>; alg=sha256"
```

Spent or revoked credential IDs for the named epoch are accumulated
as Merkle leaf hashes. The root is updated on revocation events and
at epoch rollover.

**Verification using obo-dns-null:**

1. Agent or corridor presents a Merkle non-inclusion proof for its
   `obo_credential_id` alongside the OBO Credential.
2. Verifier resolves the current epoch's `_obo-null` TXT record.
3. Verifier checks the non-inclusion proof against the published root.
4. Proof valid and credential ID not in the nullifier set: credential
   is not revoked for this epoch.

This sub-profile is operational today. The Merkle tree construction
is the same pattern used in certificate transparency logs [RFC6962].

### D.6 Sub-Profile D.4: Agent Domain Control via zk-SNARK (obo-dns-ptx)

*This sub-profile references the experimental PTX construction [PTX]
and is provided as an informative design sketch for contributor
discussion. It has not been independently security-reviewed.*

The preceding sub-profiles anchor operator-controlled material in DNS.
This sub-profile anchors **agent identity** — enabling an agent to
prove, non-interactively, that it controls the domain behind its
`agent_id`, without interactive challenge-response and without CA
infrastructure.

The construction follows [PTX] (Vishnu, 2025). The agent generates
an ephemeral keypair `(sk, nullifier)` and publishes a commitment to
DNS:

```
_obo-ptx.<agent-domain>   TXT
  "ptx=<H(nullifier ‖ sk ‖ metadata_payload)>"
```

where `metadata_payload` is the canonical JSON serialisation of:

```json
{
  "agent_id":    "<agent_id from OBO Credential>",
  "audience":    "<target_id of this transaction>",
  "expires_at":  <unix-epoch>,
  "credential_digest": "<obo_credential_id digest>"
}
```

At credential presentation the agent generates a Groth16 zk-SNARK
proof (using the Poseidon hash function, as specified in [PTX])
demonstrating knowledge of `(sk, nullifier)` consistent with the
published TXT commitment, with `metadata_payload` bound to the
specific transaction audience and expiry.

**Verification using obo-dns-ptx:**

1. Verifier resolves `_obo-ptx.<agent-domain>` TXT record.
2. Verifier checks the zk-SNARK proof against the published commitment.
3. Verifier confirms the proof's `audience` matches `target_id` and
   `expires_at` has not passed.
4. Proof valid: agent has demonstrated domain control non-interactively.

The circuit complexity reported in [PTX] is 1,756 Groth16 constraints
with sub-15ms verification time on consumer hardware. This is
compatible with real-time corridor admission checking.

**Why this matters for first-contact trust:**

Any party can mint an `agent_id` URN. Without obo-dns-ptx, a verifier
cannot distinguish a legitimate agent from an agent spoofing another's
identity. obo-dns-ptx binds the `agent_id` to a domain the agent
demonstrably controls — without requiring a CA, an authorization
server, or any pre-established relationship between the parties.

### D.7 Corridor Mutual Verification (aARP binding)

A governed corridor such as aARP [aARP] faces a symmetric problem:
the originating agent needs to verify the corridor's identity just as
the corridor needs to verify the agent's. DNS anchoring enables
mutual, non-interactive verification at corridor admission:

**Corridor publishes:**

```
_obo-corridor.<version>.<corridor-domain>   TXT
  "ptx=<H(nullifier ‖ sk ‖ {corridor_id, namespaces, expires_at})>"
```

**At corridor admission:**

```
Agent  → presents: OBO Credential + obo-dns-ptx proof
Corridor → presents: corridor identity + obo-corridor PTX proof
Both   → resolve each other's DNS records, verify proofs locally
Result → mutual non-interactive identity confirmation, no shared
         infrastructure, no CA, DNS only
```

**Sovereign lane why_ref verification:**

For regulated lanes carrying `why_ref` fields, the upstream rationale
authority (RTGF or equivalent) MAY publish its current rationale
Merkle root:

```
_obo-rtgf.<YYYY-MM>.<rtgf-operator-domain>   TXT
  "root=sha256:<rationale-merkle-root>; epoch=<YYYY-MM>"
```

The corridor verifies `why_ref.rationale_digest` against the
published root at admission time. No live RTGF endpoint is required.
The sovereign lane becomes verifiable with DNS access only.

### D.8 DNS Anchoring Security Considerations

**DNSSEC requirement.** Sub-profiles D.1 through D.3 MUST use
DNSSEC-signed records for regulated lane verification. An attacker
with DNS spoofing capability can substitute a malicious key or
governance pack digest. DNSSEC provides the freshness and integrity
guarantee that makes DNS-anchored verification equivalent in security
posture to PKI-anchored verification for the key material involved.

**TTL and caching.** Verifiers SHOULD cache DNS records for the
duration of the record TTL. A TTL of 300 seconds (5 minutes) is
RECOMMENDED for obo-dns-key records. Shorter TTLs increase revocation
responsiveness at the cost of DNS query load. Longer TTLs reduce
load but extend the window between key rotation and verifier
awareness.

**PTX nullifier reuse.** The PTX construction [PTX] requires each
`nullifier` value to be used only once per transaction to prevent
proof replay. Implementations MUST generate a fresh nullifier per
transaction. A spent nullifier SHOULD be added to the operator's
obo-dns-null epoch set.

**DNS as a trust anchor, not a trust ceiling.** DNS anchoring provides
a universal, infrastructure-free floor for agent identity and key
verification. It does not provide the trust ceiling appropriate for
high-value regulated transactions. For class C/D actions, Stage 3
completion (payment, digital signature, consent receipt) remains
required regardless of DNS anchoring profile.

---

*End of draft-lane2-obo-agentic-evidence-envelope-00*
