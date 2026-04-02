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

*None yet. First profile contribution welcome.*
