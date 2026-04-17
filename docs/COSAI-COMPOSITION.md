# CoSAI AIAM and OBO — Two Views of Agent Authority

*Informative companion to [draft-obo-agentic-evidence-envelope-01.md](../draft-obo-agentic-evidence-envelope-01.md)
§8.4. Non-normative. Written for readers who have both documents open.*

---

## The one-line framing

**CoSAI AIAM describes how an operator runs its own authorization
server function internally. OBO describes how operators — each acting
as its own authorization server — interoperate across the namespace.**

The relationship is peer-to-peer, not stacked. CoSAI AIAM is not
"below" OBO and OBO is not "above" CoSAI AIAM. They describe two
views of the same accountable legal entity: how it governs its
agents internally, and how its agents' authority travels when they
act outside its perimeter.

### A note on "identity"

An earlier version of this document described the split as "CoSAI
does identity, OBO does evidence." That framing is imprecise and
worth correcting here so the rest of the document reads cleanly.

An agent has no independent legal standing. An agent identifier
without a delegation is therefore a workload tag, not an identity
(OBO draft §1.2.1, §1.9). *Identity* in the legally meaningful sense
— the sense that matters to a counterparty, a regulator, or a
court — is always a delegation: on whose authority is this agent
currently acting, within what limits, under what governance.

Two consequences for this document:

1. **OBO does identity, and does so more completely than CoSAI
   AIAM.** OBO's credential *is* the identity, expressed as a
   delegation of a legal entity (`principal_id` → `operator_id` →
   `agent_id`, plus intent, scope, depth, governance pack). CoSAI
   AIAM's OBO-JWT is a narrower two-layer expression of the same
   thing (principal + agent, within a single operator's perimeter).
2. **Workload-identity primitives are inputs, not substitutes.**
   SPIFFE SVIDs, enterprise service accounts, and verifiable-
   credential-based agent badges (such as AGNTCY Badges —
   see below) populate the `agent_id` and `operator_id` fields;
   they do not replace the credential as a whole.

---

## The two reference documents

- **CoSAI AIAM** — *Agentic Identity and Access Management*,
  CoSAI Workstream 4, OASIS Open, v1.0, 20 March 2026.
  Approved by the CoSAI Technical Steering Committee.
  Scope: how an enterprise provisions, attests, and governs agents
  using the IAM stack it already runs — directories, secrets
  management, OAuth/OIDC, ABAC/PBAC, SIEM.

- **OBO — On Behalf Of** — this specification (`draft-obo-agentic-evidence-envelope-01`).
  Scope: a portable credential signed by the operator and a sealed
  evidence envelope, both verifiable by any counterparty that can
  resolve DNS — no prior relationship, no shared AS, no live call
  to the operator's infrastructure at verification time.

---

## The topology, drawn correctly

Each operator is an authorization server. It signs the credentials
its agents carry. It publishes the verifying key into DNS. It binds
the governance pack its corridors admit under. A counterparty is
itself an operator with the same properties. Interoperation is
peer-to-peer between operators, mediated by the namespace.

```
   Operator A                      DNS namespace                  Operator B
   (is an AS)                      (federation layer)             (is an AS)
   ┌──────────────┐                                               ┌──────────────┐
   │              │                                               │              │
   │  CoSAI AIAM  │     publishes _obo-key, _obo-gov, ...         │  CoSAI AIAM  │
   │  internal    │ ◄──────────────────────────────────────────►  │  internal    │
   │  governance  │                                               │  governance  │
   │              │                                               │              │
   │  ↓ signs     │                                               │  ↓ verifies  │
   └──────┬───────┘                                               └──────┬───────┘
          │                                                              │
          │       OBO Credential + Evidence Envelope                     │
          │       (portable, DNS-verifiable, offline)                    │
          └──────────────────────────────────────────────────────────────┘
                                agent-to-agent
```

CoSAI AIAM describes the contents of each operator's box — how that
operator runs its internal AS function, attests its agents, and
logs into its SIEM. OBO describes the protocol that crosses the line
between the boxes — what the signed credential carries, what the
sealed envelope records, and how DNS makes both verifiable without
either operator needing to reach into the other's infrastructure.

Neither box is subordinate to the other. They are the same shape.

---

## The naming collision

CoSAI AIAM uses "OBO" to mean **OAuth 2.0 Token Exchange OBO**
(RFC 8693 `act` / `sub` claims, carried in a JWT inside an
operator's own perimeter).

This specification uses "OBO" to mean the **cross-organisation
evidence envelope**: a DNS-anchored credential plus a Merkle-anchored
sealed receipt.

Both are correct uses of the term. They refer to different artefacts
at different layers. When both are present in a deployment,
disambiguate:

- **OBO-JWT** — intra-operator, OAuth 2.0 Token Exchange, CoSAI AIAM
  Appendix D profile.
- **OBO Credential** / **OBO Evidence Envelope** — peer-to-peer
  across operator boundaries, this specification.

Draft §C.4 spells out the claim-level correspondence.

---

## What each document covers, in one line each

| Concern | CoSAI AIAM (internal governance) | OBO (peer interoperation) |
|---|---|---|
| Agent registration | Agent card + registry | Out of scope; registration is the operator's internal concern |
| Workload identity at runtime | SPIFFE SVID, OAuth client credentials, TEE attestation | `agent_id` + `operator_id` in credential, signed by the operator's DNS-anchored key |
| User delegation | OBO-JWT carrying `sub` / `act.sub` | `principal_id` + `agent_id` in credential, invariant across hops |
| Authorization decision | ABAC/PBAC at gateway (OPA/Rego, Cedar) | Corridor admission predicate + governance pack |
| Intent | `csc.intent` advisory context claim | `intent_hash` — SHA-256 of normalised intent, sealed as dispute anchor |
| Logging | OCSF/CEF events in SIEM | Evidence Envelope, Merkle-anchored, offline-verifiable by any counterparty |
| Revocation | RFC 7009 at the operator's AS | DNS nullifier epoch (Appendix E.5), published by the operator |
| Peer interoperation | "OAuth Federation extended" (deferred) | Core: every operator publishes into DNS, every counterparty verifies from DNS |
| HITL for high-impact | Required by §3.4 (mechanism unspecified) | §4.5 Approval Evidence schema + §9.7 |

---

## The convergence points (independently derived)

CoSAI AIAM and OBO arrive at the same conclusion on several core
requirements from different starting points. This is corroborating
evidence, not coincidence:

1. **Agent and OBO rights must be distinct, and the delegation chain
   must remain visible.** CoSAI principle 3; OBO §1.9 *"Delegation
   origin travels; it does not re-root"*.
2. **Attestation proves what loaded, not what ran.** CoSAI Appendix B
   (TEE flow); OBO §9.5 (the limits of attestation as proof of
   computation).
3. **Revocation must cascade across delegation chains.** CoSAI §3.4;
   OBO §G.9.
4. **High-impact or irreversible actions require human-in-the-loop.**
   CoSAI §3.4; OBO §9.7, §4.5, and the selection-vs-execution split
   in [TRANSACTIONAL-LESSONS.md](TRANSACTIONAL-LESSONS.md) §9.
5. **Gateways must fail closed for high-capability agents.**
   CoSAI §5.1; OBO §7.3.

---

## The divergences that matter

Three places where CoSAI AIAM and OBO are not equivalent, and the
difference changes deployment behaviour:

### 1. What the authorization server is

CoSAI AIAM treats the authorization server as a shared enterprise
service that agents act as clients of. Interoperation with another
organisation is framed as federation between two such services —
bilateral, configured, in need of "emerging standards" (CoSAI
Appendix F names Visa Trusted Agent Protocol and ERC-8004 as
candidates).

OBO treats the operator itself as an authorization server. The
operator signs the credential; the operator publishes the verifying
key into DNS; the operator binds the governance pack. The
counterparty is another operator with the same properties.
Interoperation is peer-to-peer, not federated — DNS is already the
federation layer, and no configured bilateral relationship is
required. There is no missing "shared AS" because the specification
does not assume ASes were ever shared.

This is a genuine structural difference, not a matter of emphasis.
CoSAI Appendix F's agent-at-web-origin case is OBO's default case.

### 2. Intent

CoSAI carries intent as `csc.intent` — a free-text advisory claim
for policy-engine context.

OBO seals `intent_hash` = SHA-256 of the normalised intent, bound to
the execution record. It is the primary evidence in any contested
transaction (chargeback, regulatory inquiry, liability question).
These are not interchangeable constructs; a `csc.intent` value is
input to OBO intent normalisation, not a substitute for it.

### 3. LLM as policy judge

CoSAI is silent on whether an LLM may itself decide whether an action
is authorised.

OBO explicitly rejects this pattern (§1.9, §9.8). The LLM is the
execution substrate that produces candidate actions; the corridor —
a deterministic, external, non-prompt-injectable component — decides
whether they execute. The LLM is not part of the trust model; the
identity, delegation, and evidence layers are substrate-independent
and apply equally whether the agent is a large language model, a
rule-based planner, or a compiled binary.

---

## The composition pattern — one deployment, both views

An operator deploying agents that cross its perimeter carries
**both** layers simultaneously:

1. **Inside the operator's perimeter** CoSAI AIAM primitives are in
   effect: SPIFFE SVID for workload identity, OBO-JWT from the
   operator's internal AS for user delegation, ABAC/PBAC at internal
   gateways, SIEM logging. This is internal AS governance.

2. **At the perimeter** the corridor admission function (itself
   operated by the operator) assembles an **OBO Credential** as
   an emission of the operator's AS role: `agent_id` and
   `operator_id` derived from the attested workload identity,
   `principal_id` from the OBO-JWT `sub`, `intent_hash` from the
   normalised intent, `corridor_binding` for the target corridor,
   signed with the operator's DNS-anchored key.

3. **Across the perimeter** another operator's counterparty agent
   verifies the credential using only DNS — no call to the issuing
   operator's infrastructure, no prior relationship required. The
   transaction proceeds under the governance pack named in the
   credential, which both sides can fetch and verify independently.

4. **After the transaction** the corridor seals an **OBO Evidence
   Envelope**. Merkle anchoring makes this verifiable offline by
   the counterparty, a regulator, or a downstream auditor.

5. **Revocation** converges across layers: RFC 7009 at the operator's
   AS invalidates the upstream OBO-JWT; the operator publishes a
   DNS nullifier (Appendix E.5) that invalidates any OBO Credential
   derived from it. Internal and peer revocation expire together.

At no point does the counterparty need access to the issuing
operator's SIEM, AS, or IAM infrastructure. The operator's AS role
is expressed to the outside world entirely through DNS publication
and signed portable artefacts.

---

## If you're reading CoSAI AIAM first

Everything that document says about how an operator runs its
internal AS function is compatible with OBO. Don't rewrite that
part. The place to start with OBO is the perimeter: where your
agents talk to counterparties whose infrastructure you are not
part of, and where audit reconstruction must work without a phone
call.

The three things CoSAI AIAM leaves as requirements-without-mechanism,
and which OBO supplies:

- Peer-to-peer verification across operator boundaries: OBO
  Appendix E (DNS anchoring; the operator *is* the AS, DNS is the
  federation layer).
- Intent as dispute anchor: OBO §1.9, §4.1.
- Human decision layer for consequential selection: OBO §4.5,
  §9.7, [TRANSACTIONAL-LESSONS.md](TRANSACTIONAL-LESSONS.md) §9.

## If you're reading OBO first

Everything OBO says about the peer-to-peer protocol between
operators stands independently. The place CoSAI AIAM is useful is
the inside of each operator's box: how that operator actually stands
up, attests, and governs the agents whose credentials it is signing
and whose evidence envelopes it is sealing.

The three things OBO defers as out-of-scope, and which CoSAI AIAM
supplies:

- Agent registries and lifecycle orchestration: CoSAI §3.5,
  Appendix C, Appendix E.
- TEE attestation flow concretisation: CoSAI Appendix B.
- OCSF/CEF SIEM mapping: CoSAI Appendix E.

---

## AGNTCY Badges as a workload-identity input

AGNTCY Identity (Linux Foundation) is a running implementation of
verifiable-credential-based agent identity badges — Go code, Apache
2.0, Issuer CLI + Node Backend, supporting BYOID from Okta, A2A
agent cards, and W3C DIDs. CoSAI WS4 is actively evaluating it in
issues #47–#49 at the time of writing.

AGNTCY Badges are a **workload-identity primitive with issuer
attestation**. In the terms of this document: a Badge identifies
the agent and attests the Issuer, but does not carry the delegation
of a legal entity. AGNTCY does not define a principal, an intent
artefact, a scope narrowing mechanism across delegation hops, or a
per-transaction evidence envelope — and properly so. That is not
its scope.

This makes AGNTCY a clean composition target:

```
AGNTCY Badge  ──►  OBO Credential  ──►  OBO Evidence Envelope
(workload          (delegation of a        (sealed record of
 identity,          legal entity, with      what was done
 Issuer-            intent, scope,          under that
 attested)          depth, governance)      delegation)
```

An AGNTCY Badge MAY populate the `agent_id` and `operator_id` fields
of an OBO Credential. The OBO Credential supplies the remaining
layers: `principal_id`, intent, scope, delegation depth, governance
pack reference, corridor binding. The Evidence Envelope seals the
transaction.

Trust-anchor observation. AGNTCY currently anchors trust in Issuer
registration at a Node Backend, with BYOID variants rooting in Okta
or W3C DIDs. An AGNTCY Issuer that additionally publishes its
signing key in DNS (OBO Appendix E.3) obtains universal offline
verifiability without requiring a live Node Backend at verification
time. This is the operator-as-AS / DNS-as-federation-layer option
that §1.2.1 describes. It is compatible with AGNTCY's current
design, not in tension with it, and it resolves the
centralised-CA-vs-W3C-DIDs tension visible in AGNTCY discussions
today.

OBO draft §8.5 carries the normative version of this positioning.

---

## Further reading

- CoSAI AIAM: *Agentic Identity and Access Management*, OASIS CoSAI
  Workstream 4, v1.0, 20 March 2026. (Referenced as [COSAI-AIAM] in
  the OBO draft §13.)
- OBO §1.2 — the category errors: microservice-with-an-LLM,
  agent-as-client-of-an-AS, and identity-as-separable-from-
  delegation.
- OBO §1.9 — design principles, including the LLM as execution
  substrate rather than protocol primitive.
- OBO §8.4: Relationship to CoSAI AIAM.
- OBO §8.5: Relationship to AGNTCY Identity Badges.
- OBO Appendix C.4: Correspondence with CoSAI AIAM OBO-JWT claims.
- OBO Appendix E: DNS Anchoring Profile.
- [THE-SCOPE-PROBLEM.md](THE-SCOPE-PROBLEM.md) — why intent is the
  primitive, not scope.
- [TRANSACTIONAL-LESSONS.md](TRANSACTIONAL-LESSONS.md) §9 — the
  selection-vs-execution split and why reputation is not a
  selection criterion.
