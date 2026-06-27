# WetWijzer Legal Corpus Implementation Plan

WetWijzer is a Netherlands legal research platform for browsing and searching Dutch legal corpus artifacts. The project uses official Dutch legal sources and published Hugging Face dataset artifacts rather than inherited municipal data.

## Source Scope

- Official Dutch law text from `wetten.overheid.nl`.
- Official BWB/SRU metadata where available.
- Published dataset artifacts under the `justicedao` Hugging Face namespace:
  - Primary unified repo: `justicedao/wetwijzer_netherlands_legal_corpus`
  - Compatibility base corpus: `justicedao/ipfs_netherlands_laws`
  - Compatibility vector index: `justicedao/ipfs_netherlands_laws_vector_index`
  - Compatibility BM25 index: `justicedao/ipfs_netherlands_laws_bm25_index`
  - Compatibility knowledge graph: `justicedao/ipfs_netherlands_laws_knowledge_graph`

## Product Scope

- Static search UI for laws and articles.
- BM25, embedding, GraphRAG, CID, and JSON-LD lookup support.
- Status metadata for current, historical, repealed, superseded, and unknown records.
- Clear source attribution and user-facing disclaimers.

## Boundaries

WetWijzer provides legal information, not legal advice. Users should verify official text, version status, and legal effect on `wetten.overheid.nl`.
