# OBO Profile: Payments — Swift / ISO 20022

**Status:** Draft (non-normative)
**Author:** Kevin Brown, Lane2
**Regulatory basis:** ISO 20022 financial messaging standard; SWIFT correspondent banking; PSD2/PSD3 (EU); local equivalents per jurisdiction
**Date:** 2026-04-03

---

## Scope

This profile covers agentic payment instructions carried over the SWIFT
network using ISO 20022 message formats, where the instructing agent
acts on behalf of a corporate treasury, financial institution, or
payment operator.

The correspondent banking chain is the original multi-hop, cross-
jurisdiction, no-common-infrastructure problem. SWIFT solved message
routing fifty years ago. This profile solves the agentic delegation and
evidence layer that SWIFT does not address: who authorised the agent to
send this instruction, what scope was granted, and what tamper-evident
record survives the full correspondent chain for dispute replay.

**This profile is non-normative and draft.** Contributions from SWIFT
member institutions, ISO 20022 working group participants, and
correspondent banking operations teams are explicitly invited.

---

## 1. The correspondent banking chain as an OBO use case

A corporate treasury agent initiates a cross-border credit transfer:

```
Treasury agent
      ↓  pacs.008 credit transfer instruction
Sending bank          (e.g. HSBC London — UK jurisdiction)
      ↓  SWIFT message
Correspondent bank 1  (e.g. Deutsche Bank Frankfurt — EU jurisdiction)
      ↓  SWIFT message
Correspondent bank 2  (e.g. JPMorgan New York — US jurisdiction)
      ↓  SWIFT message
Receiving bank        (e.g. Emirates NBD Dubai — UAE jurisdiction)
```

Four legal entities. Four jurisdictions. Four regulatory regimes.
Zero shared authorisation server.

Each bank in the chain needs the same answer: was this instruction
authorised by a human with standing to issue it, within declared
scope, under a governance framework this institution can verify?

The OBO Credential provides that answer, verifiable from DNS alone,
without any bank needing a prior relationship with the agent's
operator.

---

## 2. ISO 20022 field mapping

### 2.1 OBO Credential → ISO 20022 context

| OBO field | ISO 20022 equivalent | Notes |
|---|---|---|
| `agent_id` | `InitgPty` / `DbtrAgt` agent identifier | The instructing agent's DNS-anchored identifier |
| `operator_id` | `InitgPty` name / BIC | The legal entity accountable for the agent |
| `principal_id` | `Dbtr` (debtor) | The human or corporate principal delegating authority |
| `intent_namespace` | `SvcLvl` / `LclInstrm` | Payment service level and local instrument scope |
| `action_classes` | Payment instruction type ceiling | A/B = non-RTGS; C = RTGS/high-value; D = bulk/file |
| `governance_framework_ref` | — | Points to PACT `pact.iso20022.payments.core` pack |
| `expires_at` | `ReqdExctnDt` / session window | Credential must cover the full execution window |
| `why_ref` | — | RTGF rationale token — human CFO/treasurer approval anchor |

### 2.2 OBO Evidence Envelope → ISO 20022 identifiers

| OBO field | ISO 20022 equivalent | Notes |
|---|---|---|
| `trace_id` | `UETR` (Unique End-to-End Transaction Reference) | RFC 4122 UUID — the natural cross-chain correlation key |
| `envelope_id` | `MsgId` | Per-envelope unique identifier |
| `intent_phrase` | `Purp` / `RmtInf` (remittance information) | Human-readable statement of the payment intent |
| `action_class` | Message type class | pacs.008 → C; pacs.009 → D; camt.056 recall → C |
| `outcome` | `TxSts` (transaction status) | allow → ACSC/ACCC; deny → RJCT |
| `stage3_ref` | `OrgnlMsgId` / confirmation receipt | Points to the SWIFT payment confirmation or camt.025 |
| `prior_evidence_ref` | `OrgnlUETR` | Links to the prior envelope in a multi-hop chain |
| `sealed_at` | `CreDtTm` | Envelope seal time |

---

## 3. `swift_evidence` extension object

For SWIFT/ISO 20022 transactions, the OBO Evidence Envelope **SHOULD**
carry a `swift_evidence` extension containing ISO 20022 message
identifiers and correspondent chain references:

```json
{
  "swift_evidence": {
    "message_type": "pacs.008",
    "message_id": "msg-20260403-001",
    "uetr": "123e4567-e89b-12d3-a456-426614174000",
    "instruction_id": "INSTR-20260403-001",
    "end_to_end_id": "E2E-20260403-001",
    "sending_bic": "HBUKGB4BXXX",
    "receiving_bic": "EBILAEAD",
    "amount_minor": 500000,
    "currency": "USD",
    "value_date": "2026-04-04",
    "correspondent_chain": [
      { "bic": "HBUKGB4BXXX", "role": "sending_bank",        "jurisdiction": "GB" },
      { "bic": "DEUTDEDBFRA", "role": "correspondent_bank_1", "jurisdiction": "DE" },
      { "bic": "CHASUS33XXX", "role": "correspondent_bank_2", "jurisdiction": "US" },
      { "bic": "EBILAEAD",    "role": "receiving_bank",       "jurisdiction": "AE" }
    ],
    "liability_profile": "swift_iso20022_v1",
    "evidence_bundle_ref": "bundle-20260403-001"
  }
}
```

### 3.1 `swift_evidence` field definitions

| Field | Required | Description |
|---|---|---|
| `message_type` | required | ISO 20022 message type: `pacs.008`, `pacs.009`, `camt.056`, etc. |
| `message_id` | required | ISO 20022 `MsgId` — unique per message |
| `uetr` | required | RFC 4122 UUID — maps to OBO `trace_id`; crosses the full correspondent chain |
| `instruction_id` | required | ISO 20022 `InstrId` |
| `end_to_end_id` | required | ISO 20022 `EndToEndId` |
| `sending_bic` | required | BIC of the instructing/sending institution |
| `receiving_bic` | required | BIC of the receiving institution |
| `amount_minor` | required | Amount in minor currency units |
| `currency` | required | ISO 4217 currency code |
| `value_date` | required | ISO 8601 value date |
| `correspondent_chain` | recommended | Ordered list of BICs, roles, and jurisdictions in the payment chain |
| `liability_profile` | required | Liability framing identifier (e.g. `swift_iso20022_v1`) |
| `evidence_bundle_ref` | required | Reference to the full evidence bundle for dispute replay |

---

## 4. Corridor tier mapping

| OBO corridor tier | Payment type | ISO 20022 message | Action class |
|---|---|---|---|
| `open` | Low-value, domestic or SEPA | pacs.008 (`SEPA`) | A–B |
| `domain-gated` | Cross-border, non-RTGS | pacs.008 (`SWIFT`) | B–C |
| `regulated` | RTGS / high-value | pacs.009 | C–D |
| `sovereign` | Central bank settlement | pacs.009 + jurisdiction-specific | D |

For `regulated` and `sovereign` corridors the `_obo-crq` DNS record
**MUST** include `rtgf-required=true`. The RTGF rationale token anchors
the human treasury/CFO approval that authorised the instruction.

---

## 5. PACT governance pack

The OBO Credential's `governance_framework_ref` for this profile
points to a PACT `pact.iso20022.payments.core` pack containing:

| PACT artifact | Content |
|---|---|
| `vocab.skos.jsonld` | ISO 20022 party roles (debtor, creditor, agent, correspondent), message types, instrument types, currency concepts |
| `shapes.ttl` | SHACL constraints: IBAN format, BIC format, UETR UUID, amount bounds, value date |
| `intent-mappings.json` | pacs.008 credit transfer → class C; pacs.009 FI transfer → class D; camt.056 recall → class C |
| `bundle.json` | Ed25519-signed, time-bounded, revocable by epoch |

This pack prevents an agent from initiating a message type outside
its authorised scope regardless of whether the instruction is
API-valid. A pacs.009 (financial institution transfer) instruction
from an agent credentialed only for pacs.008 fails closed.

---

## 6. The UETR as the cross-chain evidence anchor

The UETR (Unique End-to-End Transaction Reference) is the natural
backbone of the OBO evidence chain across a correspondent payment:

```
OBO Credential issued        →  trace_id = UETR assigned
        ↓
pacs.008 sent (envelope 01)  →  trace_id = UETR, prior_evidence_ref = credential_id
        ↓
Correspondent 1 processes    →  trace_id = UETR, prior_evidence_ref = envelope 01
        ↓
Correspondent 2 processes    →  trace_id = UETR, prior_evidence_ref = envelope 02
        ↓
Receiving bank confirms      →  trace_id = UETR, prior_evidence_ref = envelope 03
stage3_ref = camt.025 confirmation
```

Any party holding the UETR can request the evidence chain. Any
envelope in the chain is independently verifiable via the sending
bank's DNS-anchored OBO key. No correspondent needs a prior
relationship with the originating operator.

---

## 7. ISO 20022 ontology — relationship to existing work

ISO 20022 publishes a rich open data model (available at
iso20022.org) including OWL/RDF serialisations of financial message
structures. This is exactly the upstream source material that PACT
is designed to compile into a bounded, signed, runtime-safe
execution contract.

The ISO 20022 open ontology → PACT pack compilation pipeline:

```
ISO 20022 OWL/RDF  →  PACT compiler  →  pact.iso20022.payments.core
(open-world, unsigned,    (scopes, signs,    (closed-world, signed,
 unbounded scope)          time-bounds)        deterministic, revocable)
```

Contributions to `pact.iso20022.payments.core` from ISO 20022 working
group participants and SWIFT member institutions are explicitly
invited. See the PACT public specification at
github.com/kevin-biot/pact-public.

---

## 8. Regulatory basis

| Regulation | Relevance |
|---|---|
| ISO 20022 (various) | Message format, field definitions, UETR |
| SWIFT Rulebook | Correspondent banking obligations, liability between members |
| PSD2/PSD3 (EU) | Payment authorisation, SCA where applicable, dispute evidence |
| DORA (EU) 2022/2554 | ICT risk, operational resilience, audit trail requirements |
| UK PSR 2017 | Payment services regulation post-Brexit |
| UAE CBUAE Payment Regulation 2021 | UAE payment service provider obligations |
| US Fedwire / CHIPS rules | RTGS settlement obligations |

---

## 9. Open questions for contributors

1. **ISO 20022 message extension fields**: Which extension mechanism
   should carry the OBO evidence reference in production SWIFT
   messages? `SplmtryData` is the standard extension point — market
   practice guidance needed.

2. **SWIFT GPI overlay**: SWIFT gpi (Global Payments Innovation)
   already tracks payments via UETR. How does OBO evidence complement
   or integrate with the gpi Tracker? The UETR mapping is natural;
   the gpi status update (camt.056 / camt.057) needs profile coverage.

3. **ISO 20022 ontology compilation**: The ISO 20022 open OWL/RDF
   model is the upstream source for a `pact.iso20022.payments.core`
   PACT pack. Contributions from ISO 20022 ontology maintainers
   welcome — this is where PACT and ISO 20022 directly intersect.

4. **Nostro/vostro account agents**: Treasury agents managing
   correspondent account balances (nostro) operate on a different
   risk profile from payment instruction agents. Separate credential
   scope guidance needed.

5. **Sanctions screening integration**: Where in the OBO evidence
   chain does sanctions screening decision evidence belong? The
   corridor `_obo-crq` predicate or the evidence envelope extension?

---

*Non-normative, draft. Contributions from SWIFT member institutions,
ISO 20022 working group participants, and correspondent banking
operations teams explicitly invited. See [profiles/README.md](README.md).*
