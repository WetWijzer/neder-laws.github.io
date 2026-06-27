# WetWijzer

WetWijzer is a Netherlands-focused legal information and search site. It provides a static React interface for browsing and querying a quality-audited partial Dutch legal corpus with cited evidence, knowledge graph context, local search, and law status metadata.

WetWijzer is not legal advice. Laws and articles may be labeled `current`, `historical`, `repealed`, `superseded`, or `unknown` based on parsed official metadata. Always verify the official text, version, and legal effect on [wetten.overheid.nl](https://wetten.overheid.nl/).

## Data Sources

The site is configured around official Dutch government sources and the published JusticeDAO Netherlands dataset stack:

| Purpose | Dataset |
| --- | --- |
| Normalized laws and articles | [`justicedao/ipfs_netherlands_laws`](https://huggingface.co/datasets/justicedao/ipfs_netherlands_laws) |
| Vector index | [`justicedao/ipfs_netherlands_laws_vector_index`](https://huggingface.co/datasets/justicedao/ipfs_netherlands_laws_vector_index) |
| BM25 index | [`justicedao/ipfs_netherlands_laws_bm25_index`](https://huggingface.co/datasets/justicedao/ipfs_netherlands_laws_bm25_index) |
| JSON-LD knowledge graph | [`justicedao/ipfs_netherlands_laws_knowledge_graph`](https://huggingface.co/datasets/justicedao/ipfs_netherlands_laws_knowledge_graph) |

Official source references include:

- [wetten.overheid.nl](https://wetten.overheid.nl/)
- Official BWB/SRU metadata where available
- Official `/informatie` pages for law status and version metadata

The currently referenced published corpus is a quality-audited partial Dutch corpus, not a claimed full Dutch corpus. Project metadata records the audited package size as 4,999 laws, 89,737 articles, and 94,736 CID rows. The browser ships a small deterministic sample cache for static hosting; the full published package is hosted on Hugging Face.

## Features

- Browse Dutch laws and article groups.
- Search by law, article, citation, status, or topic.
- Ask local corpus questions with cited evidence.
- Inspect related knowledge graph nodes and edges.
- Display law status/version fields inherited by article records.
- Link back to the official text on `wetten.overheid.nl`.

## Development

Install dependencies:

```bash
npm install
```

Generate or validate the browser-ready Netherlands sample cache:

```bash
npm run prepare:netherlands-corpus
npm run validate:netherlands-corpus
```

Run the app locally:

```bash
npm run dev
```

Build and test:

```bash
npm run build
npm test
```

## Runtime Data Layout

Static browser artifacts live under:

```text
public/corpus/netherlands/current/
```

The manifest at `public/corpus/netherlands/current/artifacts.manifest.json` records the Hugging Face dataset stack and the browser sample artifact list. Do not hardcode Hugging Face tokens or private credentials into this repository.

## Legal Notice

WetWijzer provides legal information and retrieval tooling only. It does not determine legal validity, does not replace official publication, and does not provide legal advice. Users should verify official Dutch law text and metadata on `wetten.overheid.nl` and consult a qualified legal professional for advice.
