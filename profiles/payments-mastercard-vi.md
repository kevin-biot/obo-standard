# OBO Profile: Payments — Mastercard Verifiable Intent

**Status:** Draft (non-normative)
**Author:** Kevin Brown, Lane2
**Regulatory basis:** Mastercard Verifiable Intent open specification (verifiableintent.dev); PSD2/PSD3 SCA context (EU)
**Date:** 2026-04-02

---

## Scope

This profile covers agentic payment transactions where the agent's delegation
authority is expressed as a Mastercard Verifiable Intent (VI) credential chain
(L1/L2/L3) and the downstream evidence envelope must be portable across
merchant, PSP, acquirer, issuer, and payment network for dispute replay.

It defines how OBO Credential and OBO Evidence Envelope fields map to VI
chain elements, what additional fields are required for payment-network
evidence portability, and how OBO corridor tiers map to VI chain modes and
SCA requirements.

**This profile is non-normative and untested.** It is a design-accelerator for
teams evaluating OBO + VI joint deployment. It is not legal advice and not an
official Mastercard artefact. Implementors must follow applicable scheme rules
and jurisdiction-specific requirements.

---

## 1. Relationship Between OBO and Verifiable Intent

VI and OBO address different layers of the same problem:

| Layer | Addressed by | What it provides |
|---|---|---|
| Delegation authority chain | Verifiable Intent (L1/L2/L3) | Cryptographic proof that the agent is authorised to act |
| Operational evidence envelope | OBO Evidence Envelope | Portable, replayable record of what was decided and why |

OBO does **not** replace or fork VI. The OBO Evidence Envelope wraps the VI
chain by reference (via hashes), adding the surrounding operational proof
needed for cross-party dispute replay. The two standards are additive.

---

## 2. Credential Field Mapping

The OBO Credential is issued to the agent by its operator **before** the
transaction. For VI-backed deployments the following mappings apply.

| OBO field | VI equivalent | Notes |
|---|---|---|
| `agent_id` | L1 agent key identifier | Must match the key used to sign the VI chain |
| `operator_id` | L1 identity context (PSP / merchant) | The entity that bound the user to the agent |
| `obo_credential_id` | — | OBO credential UUID; no direct VI equivalent |
| `issued_at` | L1 issuance time | Should be ≤ L1 issuance |
| `expires_at` | L2 delegation expiry | Must not exceed L2 constraint window |
| `action_classes` | L2 constraint scope | See §5 below |
| `intent_namespace` | L2 intent category | `urn:obo:ns:payments` for payment operations |
| `why_ref` | L2 hash / delegation proof reference | RTGF rationale chain should reference the VI L2 hash |
| `corridor_binding` | VI verifier domain | Corridor `_obo-crq` record references the VI-accepting network |

---

## 3. Additional Required Fields

For payment transactions using VI chain evidence, the OBO Evidence Envelope
**SHOULD** carry VI chain evidence in `profile_evidence` with
`profile_id: "payments-mastercard-vi"`.

### 3.1 `vi_evidence` Extension Object

```json
{
  "vi_evidence": {
    "chain_mode": "immediate | autonomous",
    "vi_chain_refs": { ... },
    "counterparty_verification": { ... },
    "authorization_context": { ... },
    "delegation_context": { ... },
    "transaction_binding": { ... },
    "dispute_readiness": { ... }
  },
  "evidence_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "envelope_sig": "Ed25519:..."
}
```

#### 3.1.1 `vi_chain_refs` (required)

References and SHA-256 hashes of the exact VI artefacts used at decision time.

| Field | Type | Required? | Description |
|---|---|---|---|
| `chain_mode` | string | required | `immediate` or `autonomous` |
| `l1_hash` | hex64 | required | Hash of L1 identity-binding credential |
| `l2_hash` | hex64 | required | Hash of L2 intent/delegation credential |
| `l2_sd_hash` | hex64 | required | Hash of L2 selective disclosure set |
| `l2_checkout_hash` | hex64 | if immediate | Hash of L2 checkout-side credential |
| `l2_payment_hash` | hex64 | if immediate | Hash of L2 payment-side credential |
| `l3a_hash` | hex64 | if autonomous | Hash of L3 checkout-side fulfilment proof |
| `l3b_hash` | hex64 | if autonomous | Hash of L3 payment-side fulfilment proof |
| `l3_sd_hash` | hex64 | if autonomous | Hash of L3 selective disclosure set |
| `disclosure_set_hash` | hex64 | required | Hash of the disclosure set presented to this verifier |
| `signing_key_ref` | string | required | Key identifier (DID or DNS-anchored key ref) used to sign the chain |

#### 3.1.2 `counterparty_verification` (required)

Record of who verified the VI chain, with which policy, and what decision was
made.

| Field | Type | Description |
|---|---|---|
| `verifier_id` | string | Identifier of the verifying party |
| `verifier_role` | enum | `merchant`, `payment_network`, or `psp` |
| `decision` | enum | `accepted`, `rejected`, or `accepted_with_override` |
| `policy_ref` | string | Policy identifier used at verification time |
| `receipt_hash` | hex64 | SHA-256 of the verifier's decision receipt |

#### 3.1.3 `authorization_context` (required)

SCA or exemption context for the payment authorisation.

| Field | Type | Required when | Description |
|---|---|---|---|
| `mode` | enum | always | `sca` or `exemption` |
| `sca_method` | string | mode=sca | SCA method applied (e.g. `possession+inherence`) |
| `user_auth_assurance` | string | mode=sca | Assurance level (e.g. `aal2_plus`) |
| `user_auth_event_ref` | string | mode=sca | Reference to user authentication event |
| `auth_artifact_ref` | string | mode=sca | Reference to authentication artefact |
| `exemption_code` | string | mode=exemption | Exemption code claimed |

#### 3.1.4 `delegation_context` (required)

Delegation proof and liability framing.

| Field | Type | Description |
|---|---|---|
| `delegator_ref` | string | Identifier of the delegating user (may be pseudonymous) |
| `delegate_agent_ref` | string | Identifier of the acting agent |
| `delegation_proof_hash` | hex64 | SHA-256 of the delegation proof artefact |
| `delegation_scope_hash` | hex64 | SHA-256 of the delegation scope/constraints |
| `liability_profile` | string | Liability framing identifier (e.g. `eu_psd2_vi_v1`) |

#### 3.1.5 `transaction_binding` (required)

Explicit cryptographic binding of the evidence record to the transaction.

| Field | Type | Description |
|---|---|---|
| `alg` | string | Hash algorithm: `sha256` |
| `binding_hash` | hex64 | SHA-256 over the bound fields |
| `bound_fields` | array | At least: `transaction_id`, `amount_minor`, `currency`, `payee_id`, `merchant_id`, `nonce` |

#### 3.1.6 `dispute_readiness` (required)

Retention and evidence-bundle anchors for later dispute replay.

| Field | Type | Description |
|---|---|---|
| `evidence_bundle_ref` | string | Reference to the full evidence bundle |
| `immutable_log_anchor` | string | Immutable log anchor (e.g. Merkle root reference) |
| `retention_until` | date-time | Retention deadline (≥ scheme minimum, typically 5–7 years) |

---

## 4. Corridor Tier Mapping

| OBO corridor tier | VI chain mode | SCA requirement | Typical action class | Notes |
|---|---|---|---|---|
| `open` | immediate | Not required | A–B | Low-risk, below SCA threshold |
| `domain-gated` | immediate or autonomous | Conditional | B | PSP-domain-gated; SCA if amount threshold exceeded |
| `regulated` | autonomous | Required (SCA) | B–C | PSD2/PSD3 regulated lane; RTGF token required |
| `sovereign` | autonomous | Required (SCA + local auth) | C–D | Jurisdiction-specific sovereign payment rails |

For `regulated` and `sovereign` tiers the corridor `_obo-crq` DNS record
**MUST** include `rtgf-required=true` and reference an RTGF issuer whose
rationale chain includes the VI L2 delegation proof hash.

---

## 5. Action Class Mapping

| OBO action class | VI scope equivalent | Example payment operations |
|---|---|---|
| A | Read-only | Balance check, transaction status query |
| B | Write, reversible | Payment initiation, below SCA threshold |
| C | Write, significant | Payment initiation, above SCA threshold; mandate setup |
| D | Write, systemic | Bulk payment file; direct debit authority |

`ContinueOnError` in multi-step plan envelopes **MUST** be `false` for any
step carrying class B or above (write-bearing).

---

## 6. `why_ref` Chain for Regulated Payments

For `regulated` corridor deployments, the `why_ref` chain in both the OBO
Credential and OBO Evidence Envelope should link:

```
RTGF rationale token
  → OBO Credential why_ref (RTGF token reference)
    → aARP fact envelope (domain-admission proof, corridor nonce)
      → VI L2 delegation proof hash
        → OBO Evidence Envelope why_ref (sealed post-transaction)
```

This chain provides a single auditable path from the regulatory rationale
through the delegation authority to the sealed transaction evidence.

---

## 7. Examples

### Conformant example files

Five OBO Evidence Envelopes in
[`examples/envelopes/payment-lifecycle/`](../examples/envelopes/payment-lifecycle/)
trace a single agentic payment from authorisation through capture,
decline, chargeback, and dispute resolution — all conforming to this
profile:

| File | Event | Outcome | Notes |
|---|---|---|---|
| [01-payment-authorized.json](../examples/envelopes/payment-lifecycle/01-payment-authorized.json) | `payment_authorized` | allow | SCA aal2_plus, autonomous VI chain |
| [02-payment-captured.json](../examples/envelopes/payment-lifecycle/02-payment-captured.json) | `payment_captured` | allow | `prior_evidence_ref` → 01 |
| [03-payment-declined.json](../examples/envelopes/payment-lifecycle/03-payment-declined.json) | `payment_declined` | deny | Separate order; risk threshold exceeded |
| [04-chargeback-opened.json](../examples/envelopes/payment-lifecycle/04-chargeback-opened.json) | `chargeback_opened` | allow | `prior_evidence_ref` → 02; issuer dispute hub |
| [05-dispute-resolved.json](../examples/envelopes/payment-lifecycle/05-dispute-resolved.json) | `dispute_resolved` | allow | `prior_evidence_ref` → 04; merchant prevailed |

A regulated-corridor credential and single-step evidence envelope are
also available:
- [credentials/regulated-lane.json](../examples/credentials/regulated-lane.json)
- [envelopes/regulated-why-ref.json](../examples/envelopes/regulated-why-ref.json)

---

### 7.1 OBO Credential (VI autonomous mode, regulated corridor)

```json
{
  "obo_credential_id": "urn:obo:cred:payments:vi:20260402:0001",
  "principal_id": "did:example:principal:user-anon-001",
  "agent_id": "agent.pay42.psp.eu.example",
  "operator_id": "psp.eu.example",
  "binding_proof_ref": "urn:vi:delegation:l2:20260402:0001",
  "intent_namespace": "urn:obo:ns:payments",
  "intent_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "action_classes": ["A", "B", "C"],
  "governance_framework_ref": "urn:pack:rtgf:psd3:sha256:fed987cba654",
  "issued_at": 1775110800,
  "expires_at": 1775114400,
  "issuer_id": "psp.eu.example",
  "credential_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "credential_sig": "Ed25519:...",
  "corridor_binding": "payments-psd3.corridor.eu.example",
  "offline_verifiable": true
}
```

### 7.2 OBO Evidence Envelope (VI autonomous mode, regulated corridor)

```json
{
  "evidence_id": "urn:obo:ev:payments:vi:20260402:0001",
  "obo_credential_ref": "urn:obo:cred:payments:vi:20260402:0001",
  "credential_digest_ref": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "principal_id": "did:example:principal:user-anon-001",
  "agent_id": "agent.pay42.psp.eu.example",
  "operator_id": "psp.eu.example",
  "intent_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "intent_class": "urn:obo:ns:payments:credit-transfer",
  "action_class": "C",
  "outcome": "allow",
  "reason_code": "none",
  "policy_snapshot_ref": "urn:policy:vi:psd3:v1",
  "governance_framework_ref": "urn:pack:rtgf:psd3:sha256:fed987cba654",
  "sealed_at": 1775111662,
  "corridor_ref": "payments-psd3.corridor.eu.example",
  "corridor_admission_tier": "regulated",
  "corridor_predicate_digest": "sha256:...",
  "stage3_ref": "https://api.psp.eu.example/payments/pa_20260402_8472/sepa-confirmation",
  "profile_id": "payments-mastercard-vi",
  "profile_evidence": {
    "trace_id": "trace_vi_20260402_8472",
    "reason_codes": ["ontology:payments.credit_transfer.sepa.approved", "sca:autonomous.aal2_plus"],
    "chain_mode": "autonomous",
    "vi_chain_refs": {
      "chain_mode": "autonomous",
      "l1_hash": "14b2017f67a59c5126d0d3151dce0f6d2fd0d9f8d227a8d9b93f2b52d6dd0d61",
      "l2_hash": "ad68f34a840eebde37cd7dff2f9abdd86685a4f7da9d1b60db3d6f0a01dbfe77",
      "l2_sd_hash": "1a6f5ec384aa583e70d66cf6d14eb4ef36f16f411f34ce43922e4f0f6ad8f11a",
      "l3a_hash": "9d499e7f82a9e10d0a7a6ddb06be5f80af4a1d260f71f034f54f513c8c0d2c27",
      "l3b_hash": "6ed58bb6ed0f4e2b7c43b0bd7be4e25f72a334f4ab42d6e6fb2e17b6f99a5f2a",
      "l3_sd_hash": "2f9ef7aa09177fc9d1afee84c4f8c25cc7cb88df4632adf5d60cf349e4f4db38",
      "disclosure_set_hash": "7a121f75216d44f70b1f6d7c8ed40f4ddf9a2807cbf40bb63f91bdd03189bd8e",
      "signing_key_ref": "did:example:agent-pay42-key-1#k1"
    },
    "counterparty_verification": {
      "verifier_id": "psp_eu_node_01",
      "verifier_role": "psp",
      "decision": "accepted",
      "policy_ref": "vi_verifier_policy_psd3_v1",
      "receipt_hash": "0b3f7a2c088369775726f72f90f76a77876c9f03f7f07fccfc5f8616b9ff2f34"
    },
    "authorization_context": {
      "mode": "sca",
      "sca_method": "possession+inherence",
      "user_auth_assurance": "aal2_plus",
      "user_auth_event_ref": "auth_evt_8472_01",
      "auth_artifact_ref": "auth_artifact_ref_device_attestation"
    },
    "delegation_context": {
      "delegator_ref": "user_anon_001",
      "delegate_agent_ref": "agent.pay42.psp.eu.example",
      "delegation_proof_hash": "33b53f4c3f585eb5e2458d8e90d874b249f90e2141ac6f75f856709f8fa8f3d1",
      "delegation_scope_hash": "5f9cd3f5702867ad4e8f2d2f4df3617ac4bf8aa9831b6679df61f02d1ea7c80a",
      "liability_profile": "eu_psd3_vi_v1"
    },
    "transaction_binding": {
      "alg": "sha256",
      "binding_hash": "af43f9be05dc1f634060f5d580f1c8c8e9b9ce505f4b6514c6d3088e61f29c65",
      "bound_fields": [
        "transaction_id",
        "amount_minor",
        "currency",
        "payee_id",
        "merchant_id",
        "nonce",
        "checkout_hash",
        "event_time"
      ]
    },
    "dispute_readiness": {
      "evidence_bundle_ref": "bundle_20260402_0001",
      "immutable_log_anchor": "merkle_anchor_2026-04-02T09:14:22Z",
      "retention_until": "2031-04-02T00:00:00Z"
    }
  },
  "evidence_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "envelope_sig": "Ed25519:..."
}
```

---

## 8. VI Verification Interaction Model

When a payment corridor operates with VI chain verification, the admission
and evidence flow proceeds as follows:

```
Agent                        Corridor / PSP Gate              Verifier (PSP/Issuer)
  |                                  |                                  |
  |-- OBO Credential + VI L2 ------->|                                  |
  |   (pre-transaction)              |-- validate _obo-crq predicate    |
  |                                  |   RTGF token inclusion proof     |
  |                                  |   D.4a domain control nonce sig  |
  |                                  |<- corridor nonce issued          |
  |<- corridor nonce                 |                                  |
  |                                  |                                  |
  |   [transaction executes]         |                                  |
  |                                  |                                  |
  |-- OBO Evidence Envelope -------->|                                  |
  |   vi_evidence embedded           |-- forward to verifier ---------->|
  |                                  |                                  |
  |                                  |   verifier checks:               |
  |                                  |   - OBO envelope signature       |
  |                                  |   - VI chain hashes              |
  |                                  |   - SCA context                  |
  |                                  |   - transaction binding          |
  |                                  |<- receipt_hash                   |
  |                                  |                                  |
  |<- sealed outcome                 |                                  |
```

The OBO Evidence Envelope is the **single portable artefact** that carries
all three layers: (1) the VI chain by reference, (2) the corridor admission
proof, (3) the operational context (SCA, delegation, transaction binding)
needed for dispute replay across merchant, PSP, acquirer, issuer, and
payment network.

---

## 9. Relationship to Evidence Anchor

This profile draws on work originally developed in the Evidence Anchor (Secure Agent
Payment Protocol) evidence framework, which identified the operational
evidence gap around the Verifiable Intent specification. The `vi_evidence`
extension fields in this profile map directly to the six missing operational
objects identified in that work.

Evidence Anchor implementations may use this profile as the interoperability
bridge between their internal evidence contracts and the OBO Evidence
Envelope wire format, enabling cross-corridor portability without exposing
internal Evidence Anchor-specific structures.

---

## 10. RAR Integration for Regulated Payment Corridors

RFC 9396 Rich Authorization Requests (RAR) is an OAuth extension that
allows an OAuth client to include a structured `authorization_details`
object in an authorization request to an AS. Instead of requesting
broad scopes (`payment:write`), the client requests a precisely bounded
authorization object: amount, currency, payee, IBAN, SCA mode.

RAR is widely deployed in regulated payment infrastructure. Berlin
Group's NextGenPSD2, UK Open Banking, and several national PSD2
implementations use RAR as the mechanism for expressing payment
authorization detail to the bank's AS. If a payment corridor's AS is
RAR-capable, it will expect an `authorization_details` object when
the corridor requests authorization for a Class B or C payment action.

**Where RAR fits in the OBO model**

RAR operates inside the corridor — specifically at the point where the
corridor's internal AS issues the execution credential for the
downstream payment system (see §5.5 of the base spec: execution
credentials are obtained locally by the corridor, not forwarded from
the agent). The OBO Credential and OBO Evidence Envelope are
unaffected. The agent presents its OBO Credential to the corridor;
the corridor uses RAR internally to authorize against the bank's AS;
the resulting payment authorization is captured in `authorization_context`
within the `vi_evidence` extension.

```
Agent
  |-- OBO Credential (action_class C, intent_hash) --> Corridor
                                                           |
                                                     RAR request:
                                                     authorization_details
                                                     { type: "payment_initiation",
                                                       instructedAmount: {...},
                                                       creditorAccount: {...} }
                                                           |
                                                        Bank AS
                                                           |
                                                     Access token (scoped)
                                                           |
                                                     Payment execution
                                                           |
                                              OBO Evidence Envelope sealed
                                              (authorization_context captures
                                               SCA result, assurance level)
```

**Field correspondence**

| RAR `authorization_details` field | OBO / vi_evidence equivalent | Notes |
|---|---|---|
| `type: "payment_initiation"` | `action_class: C` | OBO class captures severity; RAR type names the operation |
| `instructedAmount` | `transaction_binding.bound_fields` (amount_minor, currency) | Exact amount sealed in transaction binding |
| `creditorAccount` | `transaction_binding.bound_fields` (payee_id) | Payee identity sealed |
| `remittanceInformationUnstructured` | `intent_phrase` | OBO intent phrase captures the human-readable instruction |
| SCA context returned by AS | `authorization_context.sca_method`, `user_auth_assurance` | OBO seals the SCA result in the evidence envelope |

**What this means for implementors**

A payment corridor that uses a RAR-capable AS SHOULD:

1. Map the OBO Credential's `scope_constraints` (if present) into the
   RAR `authorization_details` object when constructing the AS request.
2. Map the OBO Credential's `intent_hash` into a corridor-defined field
   in `authorization_details` if the AS supports it — preserving the
   sealed intent reference through the OAuth flow.
3. Capture the AS's authorization response (SCA result, assurance level,
   token expiry) in `vi_evidence.authorization_context` before sealing
   the OBO Evidence Envelope.

The RAR flow is corridor-internal infrastructure. It does not appear in
the OBO Credential or OBO Evidence Envelope as OAuth tokens or AS
references — only the outcomes (SCA method applied, assurance level
achieved) are sealed in the evidence. This preserves the OBO envelope's
portability across corridors that do and do not use OAuth AS
infrastructure.

---

## 11. Open Questions for Contributors

1. **Scheme chargeback choreography:** Should the profile specify how the
   `dispute_readiness` fields map to Mastercard chargeback reason codes? This
   requires scheme-level validation before standardisation.

2. **Issuer-side evidence receipts:** The current profile covers PSP/merchant/
   network. Issuer-side receipt capture (especially for 3DS2 flows) is not yet
   specified.

3. **ISO 20022 harmonisation:** `transaction_binding` bound fields should align
   with ISO 20022 `pacs.008` message fields. Mapping contribution welcome.

4. **Multi-PSP corridor federation:** When a payment traverses more than one
   PSP domain, how are `counterparty_verification` records aggregated? Proof
   composition across multi-hop paths is unspecified (mirrors the open question
   in the base OBO specification).

5. **VI specification evolution:** This profile was written against the open VI
   spec as observed at verifiableintent.dev in April 2026. Field names and
   chain structure may change as the VI specification matures.

---

*This profile is non-normative and untested. Contributions welcome via pull
request. See [profiles/README.md](README.md) for the contribution template.*
