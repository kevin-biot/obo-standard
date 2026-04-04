# The Scope Problem

## Why a certificate is not enough

An agent has a key pair. The operator registers it. The agent signs every
action it takes. The certificate tells any verifier: *this agent signed this
transaction.* That is the identity problem, and certificates solve it well.

Then something goes wrong. The agent books a first-class flight instead of
economy. Or initiates a £50,000 transfer when the user asked about a £500 one.
Or cancels a subscription the user never mentioned.

The user says: I did not authorise that.
The operator says: the user delegated to our agent.
The judge in the payments dispute says: **show me the scope of the delegation
at the time the agent signed.**

Silence.

The certificate proves the agent signed. It does not prove what the agent was
permitted to sign. The key has a name on it. It does not have a fence around it.

That is the scope problem.

---

## The fence OBO adds

OBO does not replace the certificate. It adds a credential that travels with
the agent and commits — cryptographically, before the transaction — to exactly
what the agent is permitted to do:

```
Without OBO
───────────
Agent key:   "I am agent X"
             (says nothing about scope)

With OBO
────────
OBO Credential:
  operator_id:   lane2.ai              ← who is responsible
  principal_id:  did:key:z6Mk…         ← whose authority is being delegated
  intent_hash:   SHA-256(             ← the exact scope, hash-locked
                   "Book cheapest economy flight LHR→JFK 15 April"
                 )
  action_class:  C                    ← ceiling: irreversible, not regulated
  not_after:     2026-04-04T12:05:00Z ← expires in minutes
  credential_sig: Ed25519(all of the above, operator private key)
```

The credential is issued before the transaction. It is signed by the operator.
It is verified by the receiving service before any action is taken. The
`intent_hash` is the fence: the agent can only act within the scope of the
phrase whose SHA-256 matches that hash. Any deviation — different destination,
different class, different amount — produces a hash that does not match. The
receiving service rejects the action before it executes.

---

## The human signature

For Class C and D actions — irreversible or regulated — OBO adds a second
layer: the principal's own signature over the intent phrase.

```
Intent Artifact (§3.4):
  phrase:              "Book cheapest economy flight LHR→JFK 15 April"
  principal_sig:       Ed25519(phrase, Alice's private key)
  intent_authorised_at: 2026-04-04T11:54:58Z
  authorisation_method: explicit_approval
```

Alice's `principal_sig` is her digital signature over the exact words she
approved. Not a click-through. Not a session cookie. A cryptographic commitment
to a specific phrase at a specific time.

When the dispute arises, the judge does not need Alice to testify. The judge
has:

1. **What Alice authorised** — her `principal_sig` over the exact phrase
2. **What the agent did** — the evidence envelope: outcome, task reference,
   timestamp
3. **Whether they match** — compare `intent_hash` in the credential to
   `SHA-256(executed_phrase)` in the evidence envelope
4. **That none of this has been altered** — a Merkle root over all evidence
   leaves, anchored in an append-only log, signed by the SAPP operator

The record testifies. No Alice. No operator. No expert witness. No one needs
to be in the room.

---

## What happens when the agent exceeds scope

Three cases:

**Case 1 — No credential presented.**
The receiving service has no OBO credential to verify. Under fail-closed
rules (ADR-003), the action is rejected before execution. `OBO-ERR-001`.
No action occurs. No evidence is minted for an action that did not happen.

**Case 2 — Credential presented, intent hash does not match.**
The agent presents a valid credential but the intent phrase of the actual
request does not hash to `intent_hash`. The receiving service rejects before
execution. `OBO-ERR-005`. The credential — with the correct scope — is in the
evidence record. The mismatch is provable.

**Case 3 — Credential presented, action class exceeded.**
The credential is Class B (reversible). The requested action is Class C
(irreversible). The receiving service rejects. `OBO-ERR-010`. The ceiling is
enforced at the boundary, not after the fact.

In all three cases, the agent cannot act outside its credential's scope. The
scope fence is enforced before execution, not reconstructed from logs afterward.

---

## Scope MUST NOT widen across delegation hops

In multi-hop scenarios — an orchestrating agent delegates to a sub-agent, which
delegates further — the scope of each child credential MUST NOT exceed the scope
of its parent. An agent cannot grant authority it does not have.

This is OBO-REQ-004 and is enforced by the Delegation Chain Artifact (§3.3):
each link carries the delegating party's signature over the chain digest, and
the receiving service verifies the full chain before executing a Class C/D
action.

The effect: a corporate travel policy that permits economy-only bookings cannot
be overridden by an agent three hops downstream deciding it is authorised to
book business class. The scope ceiling set at issuance propagates through every
hop.

---

## On certificates, DNS, and scope

DNS is doing something specific in OBO: it anchors **who the operator is**.
The `_obo-key.<operator_id>` TXT record publishes the operator's Ed25519 public
key, so any verifier can confirm the credential was signed by the entity that
controls that domain. That is the identity proof — and DNS is a reasonable
mechanism for it, even if not the only one (see ADR-001).

But DNS does not fence scope. DNS answers: *is this key really lane2.ai's?*
It does not answer: *was lane2.ai authorised to book first class?*

The scope fence is in the credential fields — `intent_hash`, `action_class`,
`not_after`, `principal_sig` — and it is enforced at the verifier at transaction
time. These are two different problems:

| Problem | Solved by |
|---------|-----------|
| Who is this operator? | DNS-anchored Ed25519 key (ADR-001) |
| What were they authorised to do? | `intent_hash` + `action_class` in credential |
| Did a human explicitly approve this scope? | `principal_sig` in Intent Artifact (§3.4) |
| Has anything been altered after the fact? | Merkle root + SAPP checkpoint |

OBO addresses all four. A certificate addresses only the first.

---

## The payment dispute in one paragraph

The agent booked first class. Alice disputes the charge. The operator says
Alice delegated. The bank asks for the authorisation record. The OBO credential
shows `intent_hash = SHA-256("Book cheapest economy flight LHR→JFK")` and
`action_class: C`. The evidence envelope shows the agent booked a different
flight at a different class. The intent hashes do not match. The credential did
not authorise what the agent did. The bank has its answer without calling Alice,
without calling the operator, and without an expert explaining how the system
works. The record is self-describing and self-verifying.

That is what fencing scope means in practice.
