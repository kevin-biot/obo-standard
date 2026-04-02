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

### 1.6 Design Principles

**Intent first.** The primitive is a normalised intent, not a tool
invocation list. The target service does not need to enumerate its
internal tools. The originating agent declares what it intends; the
target determines whether it can serve that intent class.

**Evidence over reputation.** Agent reputation is not a score assigned
by a central registry. It is accumulated from tamper-evident evidence
records of prior transactions. A target agent verifies the evidence
chain, not a reputation score.

**Corridor-agnostic.** The OBO envelope does not mandate a specific
routing or corridor protocol. Profiles define how OBO binds to specific
corridor implementations (aARP, direct HTTPS, local offline).

**Payment is Stage 3, not Stage 1.** Authorization is not established
at intent time via a pre-issued token. It deepens as the interaction
proceeds. Payment, signature, or data release at Stage 3 provides legal
precision for that interaction class. The OBO envelope records the
complete Stage 1 → Stage 2 → Stage 3 journey.

**Offline and local.** The OBO Credential MUST be verifiable without a
live authorization server. The Evidence Envelope MUST be sealable
without network connectivity. This enables consumer-side and device-local
agents that cannot perform online re-resolution at execution time.

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
| Intent | A normalised natural-language expression of what the principal wishes to accomplish. |
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

---

## 9. Acknowledgements and Design Philosophy

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

## 10. IANA Considerations

This document requests no IANA actions at this time. A future revision
may request registration of the `application/obo-credential+json` and
`application/obo-evidence+json` media types.

---

## 10. References

### 10.1 Normative References

- [RFC2119] Bradner, S., "Key words for use in RFCs to Indicate
  Requirement Levels", BCP 14, RFC 2119, March 1997.
- [RFC8174] Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC
  2119 Key Words", BCP 14, RFC 8174, May 2017.
- [RFC8693] Jones, M. et al., "OAuth 2.0 Token Exchange", RFC 8693,
  January 2020.

### 10.2 Informative References

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

## Appendix C. Relationship to DOP Evidence Contract

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
