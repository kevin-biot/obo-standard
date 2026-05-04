# AI Identity Paper Mapping

Informative note mapping OBO to:

Takumi Otsuka, Kentaroh Toyoda, and Alex Leung,
*AI Identity: Standards, Gaps, and Research Directions for AI Agents*,
[arXiv:2604.23280v1](https://arxiv.org/abs/2604.23280), 25 Apr 2026.

The paper is useful because it separates AI identity into model, agent,
workload, and delegated identity, then frames identity as the relationship
between what an agent declares and what observers can verify from behavior.
OBO fits inside that frame as the portable delegation and evidence layer.

## OBO's Legal Premise

OBO starts from a simple premise: every software service call, past or present,
is a delegation event from a legal entity to a workload.

AI agents make that delegation more dynamic, autonomous, and risky. They do not
change the legal fact that the workload has no independent legal standing. An
agent does not attend a court hearing. A legal entity does.

Courts and regulators will test the legal entity's authority, controls, duty of
care, governance, and evidence. They will ask whether the entity had a lawful
basis to delegate, whether the scope was reasonable, whether controls were
adequate, and whether the resulting action can be proven.

A workload cannot determine the legal basis of its own delegation. It could not
do that before AI agents, and it cannot do it now. The workload can only carry
machine-readable authority, be constrained by policy, and emit evidence. Market
desire for an agent to solve its own legal authority does not make that possible.

OBO therefore records legally inspectable facts:

- which principal delegated authority
- which operator issued and runs the workload
- which agent or workload acted
- what bounded intent and action class were authorized
- which governance framework and policy snapshot applied
- what happened, with what outcome and reason code
- which signatures and digests make the record attributable and tamper-evident

This is protocol framing, not jurisdiction-specific legal advice.

## Mapping The Paper's Identity Layers

The paper's final model has three layers: declaration, observation, and
confidence. OBO directly covers the first two and intentionally leaves the third
to monitoring, reputation, risk engines, or regulated profiles.

| Paper layer | OBO mapping | Boundary |
|---|---|---|
| Declaration layer | OBO Credential | Declares principal, agent, operator, bounded intent, action ceiling, governance, expiry, digest, and signature. |
| Observation layer | OBO Evidence Envelope | Records what happened under the credential, including outcome, reason code, policy snapshot, digest, and signature. |
| Confidence layer | Out of base scope | Confidence scores may be useful for monitoring or routing, but they are not a substitute for delegated authority or evidence. |

This distinction matters. A confidence score can decay, improve, or be tuned by
a risk engine. Delegated authority must be inspectable at the moment of action
and replayable later in a dispute.

## Mapping The Paper's Identity Types

| Paper identity type | OBO interpretation |
|---|---|
| Model identity | Useful provenance input, but not a legal actor. Model cards, hashes, and supply-chain attestations can be referenced by profile fields. |
| Agent identity | Captured by `agent_id`, but `agent_id` alone is only a workload tag unless bound to delegation. |
| Workload identity | SPIFFE, WIMSE, mTLS, TEE, cloud workload IDs, and similar systems can feed instance or operator assurance. OBO does not replace them. |
| Delegated identity | The OBO Credential. This is the legally meaningful identity in a transaction: who acts, on whose authority, within what limits. |

## Mapping The Five Gaps

| Paper gap | What OBO covers | What OBO does not claim |
|---|---|---|
| Semantic intent verification | `intent_hash`, `intent_class`, `action_classes`, and evidence bind the presented action to an authorized task fence. | OBO does not prove an agent's inner reasoning was genuine or uncorrupted. |
| Recursive delegation accountability | Binding proofs, delegation references, credential digests, and evidence envelopes provide a transaction-level accountability substrate. | Full multi-hop chain validation and scope attenuation need profile-level or draft-level expansion. |
| Agent identity integrity | `agent_id`, `operator_id`, signatures, DNS keys, expiry, and replay checks make credentials attributable and bounded. | OBO does not prove model uniqueness, prevent cloning, or replace runtime attestation. |
| Governance opacity and enforcement | `governance_framework_ref`, `policy_snapshot_ref`, `reason_code`, and sealed evidence make decisions replayable. | OBO does not provide continuous fleet monitoring by itself. |
| Operational sustainability | Base OBO uses lightweight JSON, SHA-256, Ed25519, and DNS rather than requiring ZKP or TEE verification on every call. | High-assurance profiles may still need cost and sustainability analysis. |

## The OpenID OBO Naming Collision

The paper discusses OpenID and OAuth On-Behalf-Of flows. That is a different
thing from the OBO standard in this repository.

OpenID/OAuth OBO is an intra-authorization-server token exchange pattern. It is
useful where the parties share an identity provider or authorization server.

OBO Standard is a cross-organization delegation and evidence format. It is for
the boundary case where the counterparty has no prior relationship with the
agent operator, no shared authorization server, and still needs to verify
authority, scope, accountability, and evidence.

The two can compose:

```text
OAuth / OIDC / SPIFFE inside the operator boundary
        |
        v
OBO Credential at the cross-organization boundary
        |
        v
OBO Evidence Envelope after the transaction
```

## Implications For OBO

The paper supports OBO's current positioning:

- OBO is not the whole AI identity stack.
- OBO is not reputation or confidence scoring.
- OBO is not runtime attestation.
- OBO is not a legal decision engine.
- OBO is the transaction-level declaration and evidence substrate that AI
  identity systems need when agents cross organizational boundaries.

The strongest public claim is therefore precise:

> OBO records the delegation of a legal entity to a workload and the evidence of
> what that workload did under that delegation.

Everything else can compose around that core: workload identity, model
provenance, runtime attestation, policy engines, confidence scoring, reputation,
wallets, and regulatory profiles.

## Follow-On Work

This paper points to useful next steps for OBO:

- define a delegation-chain profile with monotonic scope attenuation
- define a runtime-attestation profile for SPIFFE, WIMSE, TEE, and cloud
  workload identity inputs
- define telemetry export guidance so Evidence Envelopes can feed SIEM,
  observability, and risk engines
- define high-assurance profiles only where the action class or jurisdiction
  justifies the verification cost
- keep legal responsibility anchored to the delegating legal entity, not the
  workload
