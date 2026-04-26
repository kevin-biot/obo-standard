# OBO 8 Mapping

Customer Futures described eight minimum things an agent acting On Behalf Of
someone else needs to carry or prove. OBO turns that market framing into a
portable credential and a sealed evidence record.

OBO is not only Know Your Agent. KYA answers who the agent is. OBO answers who
the agent represents, what authority it has, what it actually did, and what a
counterparty or regulator can prove later without calling anyone.

| OBO 8 item | OBO field or artifact | What it proves |
|---|---|---|
| Principal identifier | `principal_id` | The person, organisation, or machine whose authority is being delegated. |
| Agent identifier | `agent_id` | The agent presenting the credential and executing the task. |
| Binding proof | `binding_proof_ref`, Delegation Chain Artifact | The relationship between the principal and the agent, including upstream delegation when present. |
| Delegation scope | `intent_hash`, `intent_namespace`, `action_classes`, `scope_constraints`, `expires_at` | The exact task fence, the governed namespace, the action severity ceiling, optional resource limits, and the time window. |
| Task intent | Intent Artifact, `intent_hash`, `intent_class` | The human-approved or system-approved intent, hash-bound before execution and repeated in the evidence envelope. |
| Agent operator | `operator_id`, `issuer_id` | The legal entity operating or issuing for the agent, whose DNS-published key verifies the credential. |
| Agent reputation | Profile or discovery layer input, not a base trust primitive | Reputation may help select agents, but it does not establish authority or liability. OBO records accountable authority instead. |
| Data-sharing governance | `governance_framework_ref`, `policy_snapshot_ref`, `why_ref` | The machine-readable governance pack, transaction policy snapshot, and regulated rationale chain when required. |

## The Two Artifacts

The OBO Credential is carried before the transaction. It answers who is acting,
on whose authority, under which governance, within what intent and action
limits, and until when.

The OBO Evidence Envelope is sealed after the transaction. It answers what
happened, under which credential, under which policy snapshot, with what outcome
and reason code. The envelope digest and signature make the record
tamper-evident and attributable to the operator.

## Why Reputation Is Not Enough

Reputation answers whether an agent has reportedly behaved well before. It does
not prove the agent was authorised for this transaction, does not identify the
liable legal entity, and does not produce a record a court or regulator can
verify.

OBO treats reputation as useful context outside the base wire model. The base
model requires declared authority and sealed evidence because those are the
parts needed for disputes, chargebacks, regulated audit, and cross-organisation
first contact.

## Where Embedded Identity Fits

Embedded identity makes authentication and data sharing disappear into a
customer journey. OBO does the same for delegated agent authority: the
counterparty receives a machine-readable credential and evidence envelope as
part of the task flow rather than asking the user to complete a separate trust
ceremony.

That is the practical bridge between digital identity and agentic commerce:
identity becomes a bounded, inspectable delegation object carried by the agent,
not a standalone product step.
