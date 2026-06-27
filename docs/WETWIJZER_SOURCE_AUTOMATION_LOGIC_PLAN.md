# WetWijzer Source Automation Logic Plan

This document defines safe source-automation boundaries for WetWijzer-related tooling. It replaces the inherited inherited municipal automation plan with a Netherlands-focused source policy.

## Allowed Sources

- `wetten.overheid.nl`
- Official BWB/SRU endpoints
- Official `/informatie` pages
- Curated local fixtures derived from official Dutch source metadata

## Non-Negotiable Boundaries

- Do not claim legal validity beyond parsed official metadata.
- Do not treat generated proof, GraphRAG, BM25, or vector output as legal advice.
- Do not perform official actions on behalf of users.
- Do not persist private session data or credentials.
- Prefer fixture-first validation before live network work.

## Devhub-Surface Categories

The inherited tooling may still use generic terms such as `devhub` for automation boundaries. In WetWijzer, those categories refer only to source-ingestion and validation surfaces, not to legacy municipal portals.

## Validation

Validation should use deterministic fixtures and local checks by default. Live source refreshes must be explicit, bounded, logged, and limited to official Dutch legal sources.

