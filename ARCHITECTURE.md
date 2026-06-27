# WetWijzer Architecture

WetWijzer is a static Vite/React site for Netherlands legal information search. It preserves the useful generic browser functionality from the fork while replacing the old jurisdiction-specific corpus with Dutch law metadata and dataset configuration.

## Application Flow

1. `src/main.tsx` mounts `src/AppStatic.tsx`.
2. `src/AppStatic.tsx` renders `src/components/WetWijzerLegalResearchApp.tsx`.
3. `loadWetWijzerCorpus()` reads browser-ready artifacts from `public/corpus/netherlands/current/`.
4. The search panel combines BM25-style keyword search with optional browser embeddings.
5. The chat panel builds cited answers from retrieved local evidence.
6. The graph panel reads local JSON-LD-derived entity and relationship artifacts.
7. Article rows carry inherited law status fields such as `law_status`, `is_current`, `valid_from`, `valid_to`, `status_source`, and `status_confidence`.

## Data Stack

The production dataset stack is published on Hugging Face:

- `justicedao/ipfs_netherlands_laws`
- `justicedao/ipfs_netherlands_laws_vector_index`
- `justicedao/ipfs_netherlands_laws_bm25_index`
- `justicedao/ipfs_netherlands_laws_knowledge_graph`

The browser bundle includes a small deterministic sample cache so the static app can build and run without downloading the full corpus at runtime. The manifest records the Hugging Face dataset IDs and the current project metadata.

## Source Semantics

WetWijzer uses official Dutch government source references:

- `wetten.overheid.nl`
- official BWB/SRU metadata
- official `/informatie` pages when available

Status labels are metadata parsed from official sources. A status of `unknown` means the site could not determine a normalized status from the available metadata; it should not be treated as a guess.

## Build

The site is built with Vite:

```bash
npm install
npm run prepare:netherlands-corpus
npm run build
npm test
```

No Hugging Face tokens or other private credentials are required for the static build.
