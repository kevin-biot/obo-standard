# OBO — On Behalf Of: Minimum Evidence Standard for Agentic Transactions

**draft-lane2-obo-agentic-evidence-envelope-00**
Status: Working Draft · Seeking contributors and implementation experience

> **Trust anchor: DNS.** No central registry. No approved network. No live
> authorisation server at verification time. Operator signing keys, governance
> pack digests, corridor admission predicates, and nullifier epoch roots are
> all published as DNS TXT records — the same infrastructure pattern DKIM has
> used for email trust for twenty years.

---

## The problem in thirty seconds

An agent acts on behalf of a person to book a flight, initiate a payment, or
instruct a healthcare service. The target — an airline, a bank, a clinic — has
never met this agent before. No shared infrastructure. No prior relationship.

The target asks four questions:

1. **Who are you, and who sent you?**
2. **What are you authorised to do?**
3. **What did you actually do?**
4. **Can I prove all of this to a regulator after the fact, without calling anyone?**

No existing standard answers all four. OAuth requires a live authorisation server.
W3C Verifiable Credentials cover identity claims but not per-transaction evidence.
A2A agent protocols enumerate tool surfaces without proving bounded execution.

OBO answers all four with two artefacts and one trust anchor:

```
OBO Credential        — carried by the agent before the transaction
                        answers: who, authorised for what, under whose governance

OBO Evidence Envelope — sealed by the agent after the transaction
                        answers: what happened, within what scope, tamper-evident

DNS TXT records       — the only shared infrastructure required
                        operator key  →  _obo-key._domainkey.<operator>
                        governance    →  _obo-gov.<version>.<operator>
                        corridor gate →  _obo-crq.<corridor-id>.<corridor>
                        nullifier     →  _obo-null.<epoch>.<corridor>
```

Both artefacts are verifiable offline, without contacting any central service,
by anyone who can resolve DNS.

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

## Trust without shared infrastructure

OBO Credentials are verified against signing keys published in DNS —
the same pattern DKIM has used for email signing for twenty years:

```
_obo-key._domainkey.<operator-domain>   TXT
  "v=obo1; k=ed25519; p=<base64url-public-key>"
```

No authorisation server contact required at verification time.
No CA. No registry. DNS only.

See [Appendix D](draft-obo-agentic-evidence-envelope-00.md#appendix-d-dns-anchoring-profile)
for the full DNS Anchoring Profile including governance pack digest anchoring,
nullifier epoch roots, and agent domain control proofs.

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

- **Regulated lane** — adds `why_ref` rationale chain for EU AI Act / PSD3 compliance
- **Local / offline** — credential verifiable without network access
- **Corridor-bound** — corridor co-signs the evidence envelope
- **Multi-step** — each step has its own envelope; steps chain via `prior_evidence_ref`
- **DNS anchoring** — operator key, governance pack, nullifier root, domain control proof

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
