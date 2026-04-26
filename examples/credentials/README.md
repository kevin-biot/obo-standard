# OBO Credential Examples

Concrete JSON examples of OBO Credentials. Each credential is the
pre-transaction artefact carried by an agent. The post-transaction
evidence envelopes that these credentials authorise are in
[../envelopes/](../envelopes/).

## Index

| File | Profile | Scenario | Action classes | Corridor tier |
|---|---|---|---|---|
| [open-lane.json](open-lane.json) | *(base spec)* | Travel namespace, no `why_ref` | A, B | open |
| [regulated-lane.json](regulated-lane.json) | [payments-mastercard-vi](../../profiles/payments-mastercard-vi.md) | Payments namespace, full `why_ref` chain, offline verifiable | A, B, C | regulated |
| [signed-demo.json](signed-demo.json) | *(base spec)* | Verifier CLI smoke-test credential | A | none |

## Relationship to envelopes

```
OBO Credential  (pre-transaction, carried by agent)
      │
      │  obo_credential_ref + credential_digest_ref
      ▼
OBO Evidence Envelope  (post-transaction, sealed by agent)
```

The `obo_credential_ref` in every envelope points back to the credential
that authorised it. The `credential_digest_ref` makes that binding
tamper-evident.

For the full authorise → capture → dispute lifecycle showing this
chain in action, see
[envelopes/payment-lifecycle/](../envelopes/payment-lifecycle/).
