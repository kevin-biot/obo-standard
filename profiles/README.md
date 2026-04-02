# OBO Jurisdiction and Domain Profiles

This directory contains profiles that map OBO fields to specific regulatory
contexts, jurisdictions, or domain verticals.

## What is a profile?

A profile is a document that:

1. Maps OBO Credential and Evidence Envelope fields to specific regulatory
   requirements in a named jurisdiction or domain.
2. Defines any additional required fields beyond the OBO minimum for that context.
3. Specifies how the corridor tier model maps to local regulatory concepts.
4. Provides worked examples of credentials and evidence envelopes for that context.

Profiles do not modify the base OBO specification. They are additive.

## How to contribute a profile

1. Create a file `profiles/<domain>-<jurisdiction>.md`
   (e.g. `profiles/payments-psd3-eu.md`, `profiles/healthcare-nhs-uk.md`)
2. Follow the template below.
3. Open a pull request.

## Profile template

```markdown
# OBO Profile: <Domain> — <Jurisdiction>

**Status:** Draft
**Author:** <name, organisation>
**Regulatory basis:** <regulation name, article, jurisdiction>
**Date:** <YYYY-MM-DD>

## Scope

What transactions this profile covers.

## Credential field mapping

| OBO field | Regulatory equivalent | Notes |
|---|---|---|

## Additional required fields

Fields beyond the OBO minimum required for this regulatory context.

## Corridor tier mapping

How OBO corridor tiers map to regulatory concepts in this jurisdiction.

## Examples

Link to or inline credential and envelope examples for this profile.
```

## Existing profiles

| Profile | Domain | Jurisdiction / Scheme | Status | Conformant examples |
|---|---|---|---|---|
| [payments-mastercard-vi.md](payments-mastercard-vi.md) | Payments | Mastercard Verifiable Intent + PSD3 (EU) | Draft, non-normative | [payment-lifecycle/](../examples/envelopes/payment-lifecycle/) · [regulated-why-ref.json](../examples/envelopes/regulated-why-ref.json) |
| [payments-swift-iso20022.md](payments-swift-iso20022.md) | Payments | SWIFT correspondent banking + ISO 20022 | Draft, non-normative — **contributors invited** | [envelopes/swift-correspondent/](../examples/envelopes/swift-correspondent/) *(in progress)* |

Profiles map OBO fields to regulatory contexts. The **conformant examples**
column links to concrete JSON artefacts that instantiate each profile —
they are the living proof that the field mappings work end-to-end.

---

## Open contribution invitations

### SWIFT / ISO 20022 profile

The `payments-swift-iso20022.md` profile is the first draft of OBO
applied to correspondent banking — the original multi-hop, cross-
jurisdiction, no-shared-AS problem. Contributions explicitly sought from:

- **SWIFT member institution operations teams** — field mapping
  validation, `SplmtryData` extension guidance, gpi Tracker integration
- **ISO 20022 working group participants** — ontology compilation into
  `pact.iso20022.payments.core` PACT pack (see §7 of the profile)
- **Correspondent banking practitioners** — nostro/vostro agent scope,
  sanctions screening integration, RTGS corridor guidance

The ISO 20022 open OWL/RDF model is the upstream source for a PACT
pack that makes ISO 20022 ontology runtime-safe for agents. If you work
on ISO 20022 ontology or schema, this is where PACT and ISO 20022
directly intersect.

### New jurisdiction profiles

| Gap | What's needed |
|---|---|
| Healthcare / NHS | OBO field mapping to HL7 FHIR delegation, NHS DSP toolkit |
| UAE / CBUAE | Payment regulation 2021, DIFC/ADGM agent rules |
| US ACH / Fedwire | Nacha rules, Fedwire RTGS, CHIPS |
| EU AI Act high-risk | Full `why_ref` chain requirements for in-scope systems |

To contribute a profile, use the template at the bottom of this file.
