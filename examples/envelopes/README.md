# OBO Evidence Envelope Examples

Concrete JSON examples of OBO Evidence Envelopes. Each example
conforms to one or more [profiles](../../profiles/).

## Index

| File / Directory | Profile | Scenario | Corridor tier |
|---|---|---|---|
| [basic.json](basic.json) | *(base spec)* | Travel booking, single step, outcome allow | open |
| [regulated-why-ref.json](regulated-why-ref.json) | [payments-mastercard-vi](../../profiles/payments-mastercard-vi.md) | SEPA credit transfer, action class C, full `why_ref` chain | regulated |
| [payment-lifecycle/](payment-lifecycle/) | [payments-mastercard-vi](../../profiles/payments-mastercard-vi.md) | Full payment lifecycle: authorised → captured → declined / chargeback → resolved | regulated |

## payment-lifecycle/ — what it demonstrates

These five envelopes are the most complete OBO example set in this
repository. They show:

- **`prior_evidence_ref` chaining** — each envelope references the
  previous one, creating a tamper-evident lifecycle record verifiable
  by any party without a live service.
- **`outcome: deny`** — the declined payment (03) shows that a deny
  is also a sealed evidence fact, not a silent failure.
- **Dispute replay** — the chargeback (04) and resolution (05) envelopes
  carry the same `delegation_proof_hash` and `transaction_binding_hash`
  as the original authorisation (01). A network arbitrator can verify
  the complete chain from SCA event to resolution using only DNS and
  Merkle roots.
- **Multi-actor corridor** — `agent_id` changes from
  `agent.pay42.psp.eu.example` (payment agent) to
  `dispute.agent11.issuer.eu.example` (dispute agent) across the
  lifecycle. The OBO Credential and VI delegation chain remain the
  authority reference throughout.

See [payment-lifecycle/README.md](payment-lifecycle/README.md) for
the full lifecycle narrative and regulatory basis.

## Adding examples

To add a new example:

1. Place the JSON file here or in a subdirectory.
2. Identify which profile it conforms to (or note it as base-spec only).
3. Add a row to the index table above.
4. If it illustrates a new profile, add or update the profile document
   in [profiles/](../../profiles/) and link back here.
