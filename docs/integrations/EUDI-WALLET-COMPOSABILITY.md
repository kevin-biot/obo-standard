# EUDI Wallet + OBO: EU-Sovereign Accountable Agentic AI

**Version:** 0.4.1
**Date:** 2026-04-04
**Spec refs:** §3.4, §3.4.4, §3.4.4.1, ADR-007

---

## Overview

The European Digital Identity (EUDI) Wallet (eIDAS 2.0) and the OBO standard
address adjacent problems that together form a complete solution for
accountable agentic AI on EU-sovereign infrastructure.

**EUDI Wallet answers one question: who is the human?**

It provides a government-issued, cryptographically verifiable digital
identity — name, nationality, date of birth, and qualified attributes —
using open standards (SD-JWT, ISO 18013-5 mdoc, OpenID4VP) and EU-governed
trust anchors (national PID issuers such as ANTS in France, BSI in Germany).

**OBO answers four questions EUDI does not touch:**

1. What is the agent permitted to do on behalf of that human?
2. On what authority does the agent act?
3. What did the agent actually do?
4. Is the record intact and independently verifiable?

Neither standard replaces the other. Together they close the accountability
loop for agentic transactions involving EU citizens.

---

## Strategic Context: EU Digital Sovereignty and the Agentic Layer

### The identity sovereignty problem

For most EU citizens today, the practical options for digital identity are:

- Sign in with Google
- Sign in with Apple
- Sign in with a national eID system that works only within that member state

The first two are US corporations subject to US law (the CLOUD Act grants US
government access to data held by US companies regardless of storage location),
operating under terms of service the user cannot negotiate, and able to revoke
or restrict access unilaterally. In 2022, Apple suspended access to App Store
accounts for users in one jurisdiction within 48 hours of a policy decision.
That is the risk model for an identity layer owned by a foreign private entity.

The European Commission's response is eIDAS 2.0 and the EUDI Wallet:
government-issued, open-standard, cross-EU-interoperable digital identity
that no private platform controls. Every EU member state is required to
provide a EUDI-compliant wallet to every citizen and resident by 2026.

**EUDI is the EU's sovereign answer to Apple ID and Google ID.** This is not
a metaphor — it is the explicit policy objective of eIDAS 2.0.

### The EU pattern: building sovereign infrastructure at critical layers

The EU has a consistent track record of building sovereign infrastructure when
US platform dominance creates strategic risk at a critical layer:

| Layer | Platform dominance | EU sovereign response |
|-------|-------------------|----------------------|
| Payments | Visa / Mastercard | SEPA (2008), PSD2 open banking (2015) |
| Cloud | AWS / Azure / GCP | GAIA-X framework (2020) |
| Identity | Google / Apple Sign-In | EUDI Wallet / eIDAS 2.0 (2024) |
| **Agentic accountability** | **No framework exists yet** | **OBO (candidate)** |

The pattern is clear. The EU does not ban US platforms; it builds sovereign
alternatives at layers where dependency creates unacceptable strategic risk.
Agentic AI is the next critical layer. No EU-sovereign accountability
framework for agentic transactions exists yet. OBO is positioned to be that
framework.

### The agentic gap

EUDI gives every EU citizen a sovereign digital identity for
human-to-service interactions: authenticate to a bank, prove age at a
pharmacy, present a driving licence to a rental car company. That is the
2024–2026 use case and EUDI handles it well.

The 2026+ use case is different: the human does not interact with the service
directly. The AI agent does. And here EUDI stops.

EUDI does not answer:
- How the agent proves it was authorised by the human
- What the scope of that authorisation is
- What the agent actually did during the interaction
- Who is accountable if the action exceeds authorisation or causes harm
- How these facts are recorded in a form acceptable to an EU regulator or court

**If you have sovereign identity but no agent accountability framework, the
sovereignty claim is incomplete.** You have protected the identity layer and
left the action layer exposed. A human's EUDI identity can be used by an agent
that acts beyond its mandate, with no accountable record of what happened.

OBO closes this gap. It is not an alternative to EUDI — it is what makes EUDI
useful in the agentic era.

### EU AI Act Article 12: the regulatory mandate

EU AI Act Article 12 (Transparency and provision of information to users)
requires that providers of high-risk AI systems ensure those systems are
designed and developed with capabilities for automatic recording of events
(logs), sufficient to enable post-hoc accountability.

This requirement exists in law. The technical answer for what that logging
looks like at the agentic transaction level does not yet exist in any standard.

The OBO Evidence Envelope + Evidence Anchor is the Article 12 technical answer:

- **Automatic recording:** Every OBO transaction produces a sealed Evidence
  Envelope submitted to an Evidence Anchor before the action is considered
  complete
- **Post-hoc accountability:** The Merkle-anchored root is independently
  verifiable by any party with the root hash — no access to the original
  system required
- **Sufficient for regulatory scrutiny:** Class D evidence chains include
  identity verification reference (`kyc_ref`), biometric proof, explicit human
  approval signature (`principal_sig`), delegation chain, and outcome — the
  complete picture in one hash

EUDI provides the identity layer that feeds into the OBO Intent Artifact.
OBO provides the Class D evidence chain that satisfies Article 12. Both are
open standards. Both are EU-governed. Neither depends on a US platform.

---

## How EUDI and OBO Compose

### What each standard provides

| Question | EUDI Wallet | OBO |
|----------|-------------|-----|
| Who is the human? | ✅ PID (name, nationality, DoB, national ID) | ✅ `principal_id` in credential |
| Biometric proof of human presence? | ✅ Wallet holder binding (liveness at provisioning) | ✅ `biometric_provider`, `biometric_score` in §3.4 |
| Selective disclosure of attributes? | ✅ SD-JWT, mdoc | ✅ `kyc_ref` hash (attributes stay with operator) |
| What is the agent permitted to do? | ❌ | ✅ `intent_hash` + `action_class` |
| Scope fence (cannot exceed)? | ❌ | ✅ `intent_hash` binds to exact phrase; scope MUST NOT widen |
| Agent delegation chain? | ❌ | ✅ §3.3 Delegation Chain Artifact |
| Cross-org trust without shared AS? | ❌ | ✅ DNS anchoring (§E) |
| Post-transaction evidence? | ❌ | ✅ OBO Evidence Envelope + Evidence Anchor |
| Regulator-ready audit chain? | Partial (identity only) | ✅ Class D Merkle chain |
| EU AI Act Article 12? | Partial | ✅ Complete |

### The agent carries OBO, not EUDI

A common architectural question: does the agent carry the EUDI credential to
downstream services?

**No.** EUDI holder binding uses the human's wallet signing key, which is
device-bound and cannot be delegated to an agent. The EUDI credential stays
in the wallet.

The correct architecture:

1. The operator verifies the human via EUDI Wallet (OpenID4VP presentation)
2. The operator bakes the verification reference into the OBO Intent Artifact
   as `kyc_ref` (a SHA-256 hash of the presentation bytes, per §3.4.4.1)
3. The agent carries the OBO Credential to all downstream services
4. Downstream verifiers trust the OBO chain — they see proof that qualified
   identity verification occurred, without receiving PID attributes

The EUDI Wallet proves who the human is once, to the operator. OBO carries
that proof forward into every transaction, across every organisation, without
propagating PID data.

### The transaction flow

```
EU Citizen (EUDI Wallet, ANTS-issued PID)
    │
    │  1. OpenID4VP selective disclosure presentation
    │     Discloses: name + nationality only (SD-JWT)
    │     Does NOT disclose: national ID, DoB, address
    ▼
Operator Platform (French)
    │  2. Verify SD-JWT presentation against ANTS public key
    │  3. Biometric: wallet liveness (ants.gouv.fr)
    │  4. Build Intent Artifact:
    │       kyc_ref = sha256(presentation_bytes)   ← hash, not attributes
    │       eudi_pid_issuer = ants.gouv.fr
    │       biometric_provider = ants.gouv.fr
    │  5. Issue OBO Credential (Class D)
    │
    ▼
OBO Credential ─────────────────────────────► AI Agent
                                                  │
                    ┌─────────────────────────────┤
                    │                             │
                    ▼                             ▼
           Airline API (UK)             Corporate Card (NL)
           Verifies OBO:                Verifies OBO:
           • DNS key resolution         • DNS key resolution
           • credential_sig             • credential_sig
           • Class D: chain +           • Class D: chain +
             intent artifact              intent artifact
           • kyc_ref present            • kyc_level: qualified
           No PID attributes seen       PSD2 SCA: satisfied
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                          Evidence Anchor
                          Merkle leaves include:
                            kyc_ref:sha256:…
                            eudi_pid_issuer:ants.gouv.fr
                            kyc_level:qualified
                            biometric_provider:ants.gouv.fr
                          PID attributes: never in tree
```

---

## Selective Disclosure: What Goes in the Merkle Tree

EUDI PID uses Selective Disclosure JWT (SD-JWT) so the holder reveals only
the minimum attributes required. OBO's design preserves this guarantee
end-to-end.

**The rule (normative, §3.4.4.1):**

> Operators MUST NOT include raw PID attributes (name, national identifier,
> date of birth, address, or equivalent) as Merkle leaves.

The Merkle tree proves *process* — that identity verification occurred, which
authority performed it, and at what assurance level. The substance of the
verification is retained by the operator under GDPR.

| What enters the Merkle tree | What stays with the operator |
|----------------------------|------------------------------|
| `kyc_ref:sha256:<hash>` | The actual SD-JWT presentation bytes |
| `kyc_level:qualified` | Which attributes were disclosed |
| `eudi_pid_issuer:ants.gouv.fr` | The attribute values (name, DoB, etc.) |
| `biometric_provider:ants.gouv.fr` | Biometric raw data |
| `biometric_score:0.994` | — |

A regulator or auditor who needs the attribute detail can obtain it from the
operator and verify that `SHA-256(presentation_bytes)` matches the committed
`kyc_ref` leaf. The Merkle commitment proves the presentation existed and has
not been altered.

This design satisfies:
- **GDPR Article 5(1)(e):** Storage limitation — PID attributes are not
  permanently committed to an append-only log
- **GDPR Article 25:** Data protection by design — the protocol minimises
  data in the audit trail by construction, not by configuration
- **eIDAS 2.0 selective disclosure:** The holder's choice of disclosed
  attributes is respected throughout the chain

---

## Field Reference: EUDI-Specific Intent Artifact Fields

These fields extend §3.4.4 `authorisation_evidence` for EUDI Wallet integrations.

| Field | Status | Description |
|-------|--------|-------------|
| `kyc_ref` | REQUIRED (Class C/D) | `sha256:<hex>` of EUDI SD-JWT or mdoc presentation bytes. See §3.4.4.1. |
| `kyc_level` | REQUIRED (Class C/D) | `qualified` for EUDI LoA High (eIDAS Level of Assurance High). |
| `eudi_pid_issuer` | RECOMMENDED | Domain of the EUDI PID issuing national authority (e.g. `ants.gouv.fr`, `bsi.de`). |
| `eudi_presentation_alg` | RECOMMENDED | `sd-jwt` or `mdoc`. |
| `biometric_provider` | RECOMMENDED | For EUDI wallets: SHOULD match `eudi_pid_issuer` if liveness was performed at wallet provisioning. |

### Evidence Anchor leaf names

```
kyc_ref:sha256:<lowercase hex>
kyc_level:qualified
eudi_pid_issuer:ants.gouv.fr
eudi_presentation_alg:sd-jwt
biometric_method:face_id
biometric_provider:ants.gouv.fr
biometric_score:<decimal in [0,1]>
biometric_verified_at:<ISO 8601 UTC>
```

---

## PSD2 Strong Customer Authentication (SCA) Alignment

Class D OBO credentials carrying a EUDI-backed Intent Artifact satisfy PSD2
Strong Customer Authentication requirements for payment initiation:

| PSD2 SCA Element | OBO Fulfillment |
|-----------------|-----------------|
| **Possession** | EUDI Wallet (device-bound, hardware-backed key) |
| **Inherence** | `biometric_provider: ants.gouv.fr`, `biometric_score` |
| **Knowledge** | `eudi_presentation_alg: sd-jwt` (PIN-unlocked wallet) |
| Dynamic linking | `intent_hash` binds SCA to exact payment details |
| Independence | EUDI wallet + OBO credential are separate systems |

The `intent_hash` provides PSD2's "dynamic linking" requirement: the
authentication is bound to the exact transaction amount and beneficiary, not
just a general authorisation. If the agent attempts a different payment, the
`intent_hash` does not match and verification fails.

---

## EU AI Act Article 12: Technical Compliance Map

| Article 12 Requirement | OBO Evidence Chain |
|------------------------|-------------------|
| Automatic recording of events | Evidence Envelope submitted before action completes |
| Level of detail sufficient for accountability | Class D: 30 Merkle leaves, one root |
| Events recorded include inputs and outputs | `intent_hash` (input) + `obo_outcome` (output) |
| Logging period consistent with intended purpose | `expiry` in credential; Merkle checkpoints append-only |
| Traceability to specific human decision | `principal_sig` over exact intent phrase |
| Identity of the AI system | `agent_id` in delegation chain (§3.3) |

An EU AI Act notified body auditing a high-risk AI system can:
1. Receive the Merkle root from the operator
2. Verify it independently against the Evidence Anchor checkpoint
3. Request the per-leaf detail from the operator
4. Request the EUDI presentation (PID attributes) from the operator under GDPR Article 6

The Merkle root is the Article 12 compliance artefact. The PID data is held
separately under GDPR. No conflict.

---

## Known Limitations and Open Questions

**1. `principal_sig` and EUDI wallet key**

The OBO Intent Artifact requires a `principal_sig` — an Ed25519 signature by
the principal over the canonical artifact. EUDI wallets use ECDSA P-256 or
Ed25519 depending on the member state implementation. Operators SHOULD request
a signature from the wallet at authorisation time if the wallet supports it;
otherwise the operator's countersignature (`operator_sig`) carries the weight
of authorisation proof. Full `principal_sig` support depends on EUDI wallet
signing capability maturation.

**2. Agent attestation (future)**

The EUDI ecosystem is developing "legal person" credentials and software
attestations. Future OBO versions may allow the agent itself to carry an
EUDI-equivalent attestation as part of the delegation chain. This is not
yet standardised and is out of scope for v0.4.x.

**3. Cross-border PID issuer trust**

OBO verifiers resolve operator keys via DNS. EUDI PID issuer trust (for
`eudi_pid_issuer` field verification) relies on the EUDI Trust Framework and
member state trust lists — a separate and parallel trust infrastructure. OBO
does not duplicate or replace EUDI issuer trust; it references it via
`eudi_pid_issuer` without requiring verifiers to independently resolve it.

---

## See Also

- [`docs/USE-CASES.md` — D4: AI travel agent with EUDI Wallet](../USE-CASES.md)
- [`docs/adr/ADR-007-selective-disclosure.md`](../adr/ADR-007-selective-disclosure.md)
- [OBO Spec §3.4 Intent Artifact](../../draft-obo-agentic-evidence-envelope-01.md)
- [eIDAS 2.0 Regulation (EU) 2024/1183](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1183)
- [EU AI Act Article 12 (Regulation (EU) 2024/1689)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)
- [OpenID4VP specification](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html)
- [SD-JWT (draft-ietf-oauth-selective-disclosure-jwt)](https://datatracker.ietf.org/doc/draft-ietf-oauth-selective-disclosure-jwt/)
