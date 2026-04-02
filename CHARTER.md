# OBO Standard Charter

## Purpose

The OBO (On Behalf Of) standard defines the minimum evidence envelope for agentic
transactions: what an autonomous agent must carry and produce to prove, to any party
after the fact, that it acted within declared authority on behalf of a human or
organisational principal.

## Open Standard Commitment

This specification is developed and published as an open standard. That commitment
has concrete meaning:

**No approved network.** Any agent, operated by any party, in any jurisdiction,
may implement OBO without joining a network, paying for a membership, or seeking
approval from the authors or any other central authority.

**No co-signature gate.** The trust anchor is DNS — infrastructure that is already
universal, already operated by governments, registrars, and institutions worldwide,
and not owned by anyone involved in this specification. An operator publishes a
signing key in DNS. A verifier checks it. No intermediary is required.

**No version lock.** The specification is versioned and published openly. Any party
may implement any version. Profiles and extensions may be published by any party
without permission from the authors.

**Prior art is public.** This specification is published as an IETF Internet-Draft.
The field definitions, wire formats, verification algorithms, and DNS anchoring
constructions are prior art in the public record from the date of first publication.

## Governance

This repository is governed by rough consensus among contributors. The authors
maintain editorial control over the specification text but do not control
implementations, profiles, or extensions published by others.

Decisions about the specification are made by:

1. Filing an issue with a clearly stated proposal.
2. Discussion in the issue thread.
3. A pull request with the proposed change.
4. Rough consensus among active contributors — no formal voting.

The authors will not merge changes that:
- Introduce a mandatory central registry or approval authority.
- Require participation in a named network as a precondition for compliance.
- Add a co-signature requirement from any named commercial entity.
- Break backward compatibility with existing compliant implementations
  without a versioned migration path.

## Relationship to Commercial Products

Commercial products may be built on this specification. That is encouraged.
The history of open standards demonstrates that commercial products built on
open foundations create more value — for their builders and for the ecosystem —
than proprietary protocols attempting to own the stack.

What is not permitted under this charter:
- Claiming trademark or exclusive rights over the term "OBO" as a standard.
- Publishing a specification that is materially identical to this one under a
  different name without attribution.
- Using this specification as a starting point for a proprietary network that
  requires the approval of a commercial entity for participation.

## Why DNS

DNS is the trust anchor for this specification by design, not by default.

Every agent that can send a packet can resolve a DNS TXT record. DNSSEC provides
integrity and freshness guarantees without requiring a CA hierarchy. DKIM has proven
the key publication pattern works at internet scale for two decades. The ccTLD system
provides jurisdiction-gatable domain suffixes without requiring a private registry.

The alternative — trust anchored to a private network, a commercial CA, or a
central registry — requires every participant to have a relationship with that
anchor. In a world of millions of first-contact agent transactions between parties
with no prior relationship, that is not a viable topology.

DNS is already there. It is already universal. It is the right answer.

## A Rising Tide

The authors believe that a well-specified open standard for agentic evidence is
more valuable to every participant in the ecosystem — including commercial
implementers — than a fragmented landscape of proprietary agent trust networks.

HTTP beat proprietary web protocols. SMTP beat proprietary email networks.
ISO 20022 is displacing proprietary financial message formats. TCP/IP beat
everything before it. The open standard always wins at scale.

We are in the first months of agentic commerce being a real operational problem.
The window to establish the open standard before proprietary networks calcify is
now. This specification is our contribution to ensuring that window is used well.

A rising tide raises all boats.
