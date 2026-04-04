# Payment Lifecycle Examples

These five OBO Evidence Envelopes trace a single agentic payment transaction
across its full operational lifecycle — from authorisation through capture,
decline, chargeback, and dispute resolution.

They demonstrate two paths:

```
Success path:   01-payment-authorized  →  02-payment-captured
Decline path:   03-payment-declined
Dispute path:   01-payment-authorized  →  02-payment-captured
                    →  04-chargeback-opened  →  05-dispute-resolved
```

## What links these envelopes

| Field | Value | Purpose |
|---|---|---|
| `correlation_id` | `corr_order_8472` | Business-level event chain |
| `trace_id` | per-envelope | OpenTelemetry-style span chain |
| `prior_evidence_ref` | previous envelope ID | OBO tamper-evident lifecycle linkage |
| `credential_ref` | `cred_vi_pay_20260402_0001` | Same OBO Credential authorised all steps |
| `vi_evidence.vi_chain_refs.delegation_chain_id` | `dlg_vi_chain_20260401_a1` | Same VI delegation chain throughout |

## Regulatory context

These examples are scoped to the EU regulated corridor under PSD2/PSD3 + SCA:

- PSD2 Article 97 / RTS SCA Article 5: dynamic linking binds authentication
  to specific amount and payee; any change invalidates the authorisation.
- GDPR Article 5(2) / Article 30: accountability and records of processing.
- eIDAS Article 25 / Article 26: e-signatures as legal evidence; detectability
  of post-signature changes.
- EU AI Act (2024/1689): traceability and documentation for in-scope systems.

The Merkle-committed `vi_evidence` leaves in each envelope satisfy these
requirements: tamper-evident, minimally disclosable, deterministically
replayable by any party holding the root hash.

## Profile

These examples conform to the
[payments-mastercard-vi](../../profiles/payments-mastercard-vi.md) profile.
The `vi_evidence` extension carries VI chain hashes, SCA context, delegation
proof, transaction binding, and dispute-readiness fields.

## Notice

Illustrative examples only. Not legal advice. Not official Mastercard or
Verifiable Intent artefacts. Derived from Evidence Anchor (Secure Agent Payment Protocol)
evidence framework work.
