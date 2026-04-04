# AGNTCY + OBO: Infrastructure and Accountability for the Internet of Agents

**Version:** 0.4.7
**Date:** 2026-04-05
**Spec refs:** §3, §4, §9, Appendix J

---

## Overview

[AGNTCY](https://agntcy.org) (Linux Foundation, formative members: Cisco, Dell,
Google Cloud, Oracle, Red Hat) is building the Internet of Agents — the
infrastructure layer that lets agents discover each other, establish identity,
communicate securely, and be observed across organisational boundaries.

**AGNTCY answers four infrastructure questions:**

1. How do agents find each other? (OASF + Agent Directory)
2. How do agents prove who they are? (decentralised identity)
3. How do agents communicate? (SLIM, A2A, MCP)
4. How do operators monitor what agents are doing? (observability)

**OBO answers four accountability questions AGNTCY does not touch:**

1. Under what authority does an agent act on behalf of a human principal?
2. What governance framework constrains the agent's actions?
3. What did the agent actually do — sealed, immutable, independently verifiable?
4. How is that record produced at dispute time, regulatory audit, or AI Act review?

AGNTCY is the Internet. OBO is the audit trail of what happened on it.

Neither standard replaces the other. Together they provide a complete stack
for accountable agentic AI: agents that can be found, identified, and trusted
to communicate — and whose actions are governed, evidenced, and provable.

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│         agent workflows, tools, human-in-the-loop        │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
┌─────────▼──────────┐           ┌──────────▼──────────┐
│   AGNTCY           │           │   OBO               │
│   Infrastructure   │           │   Accountability    │
│                    │           │                     │
│  · OASF discovery  │           │  · OBO Credential   │
│  · Agent identity  │           │  · Evidence Envelope│
│  · SLIM transport  │           │  · Governance Pack  │
│  · A2A / MCP       │           │  · Evidence Anchor  │
│  · Observability   │           │  · Merkle log       │
└─────────┬──────────┘           └──────────┬──────────┘
          │                                 │
          └────────────────┬────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│               Regulated Transaction                      │
│   agent acts, AGNTCY carries it, OBO seals the record    │
└─────────────────────────────────────────────────────────┘
```

---

## Composability Map

| AGNTCY Component | OBO Complement | Relationship |
|-----------------|---------------|--------------|
| **OASF agent schema** | OBO Credential `agent_id` | OASF describes agent capabilities; OBO Credential binds the agent to a principal and governance framework |
| **Agent identity** | OBO Credential `agent_id` + `operator_id` | AGNTCY identity answers *who is the agent*; OBO Credential answers *on whose authority does it act* |
| **Agent Directory** | Governance Pack `corridor_id` | Directory enables discovery; governance pack declares what the agent may do in a corridor once found |
| **SLIM transport** | OBO Evidence Envelope | SLIM carries the message; the OBO envelope seals the accountability record of what was carried |
| **A2A messaging** | OBO Evidence Envelope `stage3_ref` | A2A completes the agent-to-agent transaction; OBO records it as a sealed, Merkle-anchored artefact |
| **MCP tool calls** | OBO Evidence Envelope `intent_class` | MCP invokes the tool; OBO governs the intent that caused the invocation and seals the evidence — tools are implementation detail, intent is the accountability unit |
| **Observability** | OBO Evidence Anchor | AGNTCY observability monitors live behaviour; OBO anchors a tamper-evident record for retrospective audit |

---

## Transaction Flow

A regulated payment agent operating over AGNTCY infrastructure with OBO
accountability:

```
1. DISCOVERY
   Agent queries AGNTCY Agent Directory using OASF schema
   → finds payment corridor operator endpoint

2. IDENTITY
   Agent presents AGNTCY cryptographic identity
   → corridor verifies agent identity across org boundary

3. AUTHORITY (OBO)
   Agent presents OBO Credential
   → corridor verifies: principal, action classes, governance framework,
     intent namespace, expiry

4. EXECUTION
   Agent constructs payment intent
   → intent normalised to urn:obo:ns:payments:credit-transfer
   → SLIM / A2A carries the transaction message to the target service

5. EVIDENCE (OBO)
   Agent seals OBO Evidence Envelope:
   · action_class: C
   · intent_class: urn:obo:ns:payments:credit-transfer
   · outcome: allow
   · stage3_ref: <ISO 20022 pacs.008 transaction ID>
   · evidence_digest: sha256:<hex>

6. ANCHORING (OBO)
   Evidence Envelope submitted to Evidence Anchor declared in Governance Pack
   → Merkle receipt returned
   → receipt independently verifiable without trusting any single party

7. OBSERVABILITY
   AGNTCY observability layer sees live transaction metrics
   OBO Merkle log holds immutable accountability record
   Both available independently at audit time
```

---

## The Explicit Gap AGNTCY Does Not Fill

AGNTCY's documentation does not define:

- A pre-transaction authority contract binding agent to principal
- A post-transaction sealed evidence record
- An immutable, independently verifiable audit log
- A governance framework constraining what an agent may do
- A dispute resolution mechanism grounded in tamper-evident records
- EU AI Act Article 12 compliance (mandatory logging for high-risk AI)

These are not gaps by accident. AGNTCY is infrastructure — it deliberately
does not reach into application-layer accountability. OBO is the
accountability layer designed to sit above it.

---

## EU AI Act Article 12 Mapping

High-risk AI systems operating over AGNTCY infrastructure are subject to
mandatory logging requirements under EU AI Act Article 12. AGNTCY
observability provides runtime monitoring. OBO provides the tamper-evident
log that satisfies the Article 12 archival and auditability requirement.

| Article 12 Requirement | AGNTCY | OBO |
|------------------------|--------|-----|
| Automatic logging of events | Observability (live) | Evidence Envelope (sealed) |
| Logs enabling post-market monitoring | Partial — monitoring only | ✓ Merkle-anchored, independently verifiable |
| Logs sufficient for incident investigation | No accountability record | ✓ Sealed evidence chain |
| Retention and integrity | Not specified | ✓ Append-only log, cryptographic integrity |

---

## Identity Composability

AGNTCY agent identity and OBO Credentials are complementary and
non-overlapping:

```
AGNTCY identity  →  answers: is this agent who it claims to be?
                    cryptographic proof of agent identity
                    cross-organisational trust

OBO Credential   →  answers: is this agent authorised to act?
                    binds agent to principal
                    declares action classes, governance, expiry
                    carries kyc_ref for Class C/D actions
```

An agent MAY carry both an AGNTCY cryptographic identity and an OBO
Credential simultaneously. They bind at `agent_id`: the AGNTCY identity
and the OBO Credential SHOULD reference the same agent identifier.

---

## OASF and OBO Governance Pack

The Open Agent Schema Framework (OASF) describes what an agent *can* do —
its capabilities, interfaces, and supported protocols.

The OBO Governance Pack declares what an agent *may* do in a specific
corridor — permitted action classes, intent namespace, domain SHACL
profile, evidence anchor, and scope constraints.

These are complementary declarations operating at different abstraction
levels:

| | OASF | OBO Governance Pack |
|-|------|---------------------|
| **Scope** | Agent capabilities (universal) | Corridor permissions (context-specific) |
| **Content** | Interfaces, protocols, formats | Action classes, governance, evidence anchor |
| **Audience** | Agents discovering each other | Agents seeking corridor admission |
| **Binding** | None — informational | Yes — credential issued under pack |

---

## Tool-First vs Intent-First

MCP and OASF operate on a **tool-first paradigm**: an agent advertises
tools, another agent discovers and calls them. The tool is the primary
abstraction.

```
Tool-first:   discover tool → call tool → get result
                                ↑
                     no principal, no authority,
                     no intent, no accountability record
```

This model has a fundamental accountability gap. A tool call carries
no declaration of:

- **Who authorised it** — no principal binding
- **Why it was invoked** — no intent record
- **What constrained it** — no governance framework
- **What the consequences are** — no action class, no write-bearing rules

OBO operates on an **intent-first paradigm**: the human has an intent,
the agent is authorised to pursue it within a governed scope, and tools
are implementation details invisible to the accountability layer.

```
Intent-first: principal intent → authority → governed action → evidence
              ↑                  ↑            ↑                 ↑
              human declared     OBO Cred     action class      sealed
              in advance         verified     enforced          forever
```

Tools MAY be MCP underneath. OBO does not care what invocation
mechanism was used. The accountability unit is the **intent and its
governed execution** — not the tool call.

This distinction matters acutely for regulated domains. A sequence of
MCP tool calls that together constitute an irreversible financial
transaction is a Class C action requiring a sealed evidence record —
regardless of which tools were called or in what order. The tools are
verbs. The intent is the sentence. OBO governs the sentence.

### aARP and Corridor Admission

AGNTCY's OASF and Agent Directory answer *"what can this agent do?"*
— general capability discovery, functionally equivalent to A2A Agent
Cards. They are pull-based schema documents: an agent publishes its
capabilities, another agent reads them.

OBO's aARP (Agent Address Resolution Protocol, Appendix E §E.7)
answers a different question entirely: *"is this agent admitted to
THIS corridor under THIS governance pack?"* It is DNS-based, corridor-
specific, and mutual — both the agent and the corridor operator verify
each other's DNS-published commitments.

```
OASF / Agent Cards  →  "I have these capabilities"
                        universal, informational, pull-based

aARP                →  "I am admitted to this corridor"
                        specific, normative, cryptographically bound
```

AGNTCY has no equivalent to aARP. Discovering an agent's capabilities
does not grant it admission to a governed corridor. Admission requires
authority — and authority requires OBO.

---

## Known Limitations and Open Questions

1. **No shared identifier scheme** — AGNTCY and OBO currently use independent
   identifier formats for agent identity. Alignment on a common DID method
   (e.g. `did:web`) would improve composability. See Appendix F.

2. **SLIM and evidence transport** — OBO does not specify how evidence
   envelopes are transported to anchors. SLIM is a candidate transport for
   high-throughput agentic evidence submission. Not yet defined.

3. **OASF capability advertisement of OBO support** — An OBO-capable agent
   SHOULD advertise its OBO Credential namespace and supported action classes
   in its OASF schema entry. Schema extension not yet defined.

4. **Observability correlation** — AGNTCY observability trace IDs and OBO
   `orchestration_trace_id` fields are not yet correlated. Alignment would
   enable end-to-end tracing from infrastructure telemetry to accountability
   record.

---

## References

- [AGNTCY Documentation](https://docs.agntcy.org/)
- [AGNTCY.org](https://agntcy.org/)
- [Linux Foundation AGNTCY Announcement](https://www.linuxfoundation.org/press/linux-foundation-welcomes-the-agntcy-project-to-standardize-open-multi-agent-system-infrastructure-and-break-down-ai-agent-silos)
- OBO RFC: draft-obo-agentic-evidence-envelope-01
- OBO Governance Pack: `schemas/obo-governance-pack.json`
- EUDI Wallet Composability: `docs/integrations/EUDI-WALLET-COMPOSABILITY.md`
