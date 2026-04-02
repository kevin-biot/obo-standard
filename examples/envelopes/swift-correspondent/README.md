# Swift Correspondent Banking Examples

OBO Evidence Envelopes for a cross-border SWIFT pacs.008 credit
transfer routed through a four-bank correspondent chain.

## The scenario

A corporate treasury agent, authorised by the CFO of a UK company,
initiates a USD 5,000 payment to a supplier in Dubai. The payment
routes through Deutsche Bank Frankfurt and JPMorgan New York before
reaching Emirates NBD.

```
Treasury agent (London)
        ↓
HSBC London        (sending bank, GB)
        ↓  SWIFT pacs.008
Deutsche Frankfurt (correspondent, DE)
        ↓  SWIFT pacs.008
JPMorgan New York  (correspondent, US)
        ↓  SWIFT pacs.008
Emirates NBD Dubai (receiving bank, AE)
```

Four jurisdictions. Zero shared authorisation server. One UETR
threads the full chain. Each envelope is independently verifiable
from the sending bank's DNS-anchored OBO key.

## Files

| File | Event | Party | Notes |
|---|---|---|---|
| [01-instruction-initiated.json](01-instruction-initiated.json) | Instruction issued by agent | Treasury agent | OBO Credential ref + full swift_evidence |
| [02-sending-bank-accepted.json](02-sending-bank-accepted.json) | HSBC accepts and forwards | HSBC London | prior_evidence_ref → 01 |
| [03-payment-confirmed.json](03-payment-confirmed.json) | Emirates NBD confirms receipt | Receiving bank | prior_evidence_ref → 02, stage3_ref → camt.025 |

## What these demonstrate

- **UETR as trace_id** — same UUID across all three envelopes, crosses
  the full correspondent chain
- **`prior_evidence_ref` chain** — tamper-evident lineage from
  instruction to confirmation
- **`correspondent_chain`** — full BIC/jurisdiction map in the
  `swift_evidence` extension
- **Multi-jurisdiction corridor** — `regulated` tier, RTGF rationale
  from human CFO approval anchored via `why_ref`
- **DNS-only verification** — no envelope requires the correspondent
  banks to have a prior relationship with the agent's operator

## Profile

Conforms to [payments-swift-iso20022.md](../../../profiles/payments-swift-iso20022.md).
