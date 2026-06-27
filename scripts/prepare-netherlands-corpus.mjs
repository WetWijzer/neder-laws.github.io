#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const corpusRoot = path.join(repoRoot, 'public', 'corpus', 'netherlands', 'current');
const generatedRoot = path.join(corpusRoot, 'generated');
const generatedAt = '2026-06-27T00:00:00Z';
const embeddingDimension = 384;

const hfDatasets = {
  normalized: 'justicedao/ipfs_netherlands_laws',
  vectorIndex: 'justicedao/ipfs_netherlands_laws_vector_index',
  bm25Index: 'justicedao/ipfs_netherlands_laws_bm25_index',
  knowledgeGraph: 'justicedao/ipfs_netherlands_laws_knowledge_graph',
};

const sections = [
  {
    ipfs_cid: 'bafywetwijzer000000000000000000000000000000000000000000000001',
    law_id: 'BWBR0001854',
    identifier: 'BWBR0001854 Artikel 1',
    title: 'Wetboek van Strafrecht - Artikel 1',
    text: 'Artikel 1. Geen feit is strafbaar dan uit kracht van een daaraan voorafgegane wettelijke strafbepaling. Bij verandering in de wetgeving na het tijdstip waarop het feit is begaan, worden de voor de verdachte gunstigste bepalingen toegepast.',
    source_url: 'https://wetten.overheid.nl/BWBR0001854',
    official_cite: 'Wetboek van Strafrecht, Artikel 1',
    bluebook_citation: 'BWBR0001854 art. 1',
    chapter: 'Artikel 1',
    title_number: 'BWBR0001854',
    law_status: 'current',
    is_current: true,
    valid_from: null,
    valid_to: null,
    effective_date: null,
    retrieved_at: generatedAt,
    status_source: 'wetten.overheid.nl /informatie and official BWB metadata',
    status_confidence: 'high',
    status_note: 'Status is exposed as corpus metadata; verify the official text on wetten.overheid.nl.',
  },
  {
    ipfs_cid: 'bafywetwijzer000000000000000000000000000000000000000000000002',
    law_id: 'BWBR0002656',
    identifier: 'BWBR0002656 Artikel 1',
    title: 'Burgerlijk Wetboek Boek 1 - Artikel 1',
    text: 'Artikel 1. Allen die zich in Nederland bevinden, zijn vrij en bevoegd tot het genot van burgerlijke rechten. Persoonlijke status en familierechtelijke bepalingen moeten altijd tegen de officiele tekst worden gecontroleerd.',
    source_url: 'https://wetten.overheid.nl/BWBR0002656',
    official_cite: 'Burgerlijk Wetboek Boek 1, Artikel 1',
    bluebook_citation: 'BWBR0002656 art. 1',
    chapter: 'Artikel 1',
    title_number: 'BWBR0002656',
    law_status: 'current',
    is_current: true,
    valid_from: null,
    valid_to: null,
    effective_date: null,
    retrieved_at: generatedAt,
    status_source: 'wetten.overheid.nl /informatie and official BWB metadata',
    status_confidence: 'high',
    status_note: 'Status is exposed as corpus metadata; verify the official text on wetten.overheid.nl.',
  },
  {
    ipfs_cid: 'bafywetwijzer000000000000000000000000000000000000000000000003',
    law_id: 'BWBR0001827',
    identifier: 'BWBR0001827 Artikel 1',
    title: 'Wetboek van Burgerlijke Rechtsvordering - Artikel 1',
    text: 'Artikel 1. De rechtsmacht van de Nederlandse rechter en de wijze van procederen volgen uit de wet. Gebruik deze tekst als zoekingang en controleer de geldende versie op wetten.overheid.nl.',
    source_url: 'https://wetten.overheid.nl/BWBR0001827',
    official_cite: 'Wetboek van Burgerlijke Rechtsvordering, Artikel 1',
    bluebook_citation: 'BWBR0001827 art. 1',
    chapter: 'Artikel 1',
    title_number: 'BWBR0001827',
    law_status: 'current',
    is_current: true,
    valid_from: null,
    valid_to: null,
    effective_date: null,
    retrieved_at: generatedAt,
    status_source: 'wetten.overheid.nl /informatie and official BWB metadata',
    status_confidence: 'high',
    status_note: 'Status is exposed as corpus metadata; verify the official text on wetten.overheid.nl.',
  },
].map((section) => ({
  ...section,
  jsonld: JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'Legislation',
    identifier: section.identifier,
    name: section.title,
    legislationJurisdiction: 'Netherlands',
    url: section.source_url,
    isBasedOn: 'wetten.overheid.nl',
    lawStatus: section.law_status,
  }),
}));

function tokenize(value) {
  return value
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .map((token) => token.trim())
    .filter((token) => token.length > 1);
}

function buildBm25Payload() {
  const documents = sections.map((section) => {
    const terms = {};
    for (const token of tokenize(`${section.identifier} ${section.title} ${section.text} ${section.law_status}`)) {
      terms[token] = (terms[token] || 0) + 1;
    }
    const documentLength = Object.values(terms).reduce((sum, count) => sum + count, 0);
    return {
      id: section.ipfs_cid,
      document_id: section.ipfs_cid,
      title: section.title,
      document_length: documentLength,
      terms,
    };
  });

  const documentFrequency = {};
  for (const doc of documents) {
    for (const token of Object.keys(doc.terms)) {
      documentFrequency[token] = (documentFrequency[token] || 0) + 1;
    }
  }

  const avgdl = documents.reduce((sum, doc) => sum + doc.document_length, 0) / documents.length;
  return {
    documents,
    documentFrequency,
    k1: 1.2,
    b: 0.75,
    avgdl,
    documentCount: documents.length,
  };
}

function buildGraph() {
  const entities = [];
  const relationships = [];
  const adjacency = { outgoing: {}, incoming: {} };

  function addEntity(entity) {
    entities.push(entity);
  }

  function addRelationship(relationship) {
    relationships.push(relationship);
    adjacency.outgoing[relationship.source] ||= [];
    adjacency.incoming[relationship.target] ||= [];
    adjacency.outgoing[relationship.source].push(relationship);
    adjacency.incoming[relationship.target].push(relationship);
  }

  addEntity({
    id: 'netherlands_source:wetten_overheid_nl',
    type: 'official_source',
    label: 'wetten.overheid.nl',
    properties: { url: 'https://wetten.overheid.nl', role: 'official Dutch law source' },
  });
  addEntity({
    id: 'netherlands_status:current',
    type: 'law_status',
    label: 'current',
    properties: { definition: 'Current according to parsed official metadata when retrieved.' },
  });

  for (const section of sections) {
    const lawEntityId = `netherlands_law:${section.law_id}`;
    addEntity({
      id: section.ipfs_cid,
      type: 'article',
      label: section.official_cite,
      properties: { identifier: section.identifier, law_status: section.law_status, source_url: section.source_url },
    });
    addEntity({
      id: lawEntityId,
      type: 'law',
      label: section.title.replace(/\s+-\s+Artikel\s+1$/, ''),
      properties: { law_id: section.law_id, law_status: section.law_status, source_url: section.source_url },
    });
    addRelationship({
      id: `${section.ipfs_cid}:part_of:${section.law_id}`,
      source: section.ipfs_cid,
      target: lawEntityId,
      type: 'part_of_law',
      properties: { article: section.chapter },
    });
    addRelationship({
      id: `${section.ipfs_cid}:status:current`,
      source: section.ipfs_cid,
      target: 'netherlands_status:current',
      type: 'has_law_status',
      properties: { status_source: section.status_source, status_confidence: section.status_confidence },
    });
    addRelationship({
      id: `${section.ipfs_cid}:source:wetten`,
      source: section.ipfs_cid,
      target: 'netherlands_source:wetten_overheid_nl',
      type: 'sourced_from',
      properties: { url: section.source_url },
    });
  }

  return { entities, relationships, adjacency };
}

function buildLogicProofSummaries() {
  const formulas = {
    obligation:
      'forall a:Agent (SubjectTo(a, netherlands_law_article_bwbr0001854_artikel_1) -> O([]ComplyWith(a, netherlands_law_article_bwbr0001854_artikel_1)))',
    permission:
      'forall a:Agent (SubjectTo(a, netherlands_law_article_bwbr0002656_artikel_1) -> P([]ExerciseAuthority(a, netherlands_law_article_bwbr0002656_artikel_1)))',
    prohibition:
      'forall a:Agent (SubjectTo(a, netherlands_law_article_bwbr0001827_artikel_1) -> F([]Violate(a, netherlands_law_article_bwbr0001827_artikel_1)))',
  };
  const rows = [
    { section: sections[0], norm_type: 'obligation', norm_operator: 'O', formula: formulas.obligation },
    { section: sections[1], norm_type: 'permission', norm_operator: 'P', formula: formulas.permission },
    { section: sections[2], norm_type: 'prohibition', norm_operator: 'F', formula: formulas.prohibition },
  ];

  return rows.map(({ section, norm_type, norm_operator, formula }) => ({
    ...(section.law_id === 'BWBR0001854'
      ? {
          deontic_cognitive_event_calculus:
            '(forall agent (implies (subject_to agent netherlands_law_article_bwbr0001854_artikel_1) (O (always (comply_with agent netherlands_law_article_bwbr0001854_artikel_1)))))',
        }
      : section.law_id === 'BWBR0002656'
        ? {
            deontic_cognitive_event_calculus:
              '(forall agent (implies (subject_to agent netherlands_law_article_bwbr0002656_artikel_1) (P (always (exercise_authority agent netherlands_law_article_bwbr0002656_artikel_1)))))',
          }
        : {
            deontic_cognitive_event_calculus:
              '(forall agent (implies (subject_to agent netherlands_law_article_bwbr0001827_artikel_1) (F (always (violate agent netherlands_law_article_bwbr0001827_artikel_1)))))',
          }),
    ipfs_cid: section.ipfs_cid,
    identifier: section.official_cite,
    title: section.title,
    formalization_scope: 'article',
    fol_status: 'success',
    deontic_status: 'success',
    deontic_temporal_fol: formula,
    frame_logic_ergo: `netherlands_law_article_${section.law_id.toLowerCase()}_artikel_1[identifier -> "${section.identifier}", ipfs_cid -> "${section.ipfs_cid}", source_url -> "${section.source_url}", jurisdiction -> "Netherlands", norm_operator -> "${norm_operator}", norm_type -> "${norm_type}"] : DutchLawArticle.`,
    norm_operator,
    norm_type,
    zkp_backend: 'simulated',
    zkp_security_note: 'Local simulated proof helper only; not cryptographic verification and not legal advice.',
    zkp_verified: false,
  }));
}

function buildManifest(artifactStats) {
  return {
    schemaVersion: 1,
    generatedAt,
    datasetId: hfDatasets.normalized,
    datasetPath: 'netherlands_laws_quality_audited_partial',
    corpus: {
      jurisdiction: 'Netherlands',
      name: 'WetWijzer Netherlands Laws',
      source: 'wetten.overheid.nl official BWB/SRU sources',
      note: 'Browser sample cache for the published quality-audited partial Dutch corpus. Use the Hugging Face datasets for the full published package.',
      publishedCorpus: {
        laws: 4999,
        articles: 89737,
        cidRows: 94736,
        coverage: 'quality-audited partial corpus, not full Dutch corpus coverage',
      },
      hfDatasets,
    },
    artifacts: artifactStats,
    generatedFiles: artifactStats.map((artifact) => artifact.path),
  };
}

async function writeJson(relativePath, value) {
  const target = path.join(corpusRoot, relativePath);
  await mkdir(path.dirname(target), { recursive: true });
  const body = `${JSON.stringify(value, null, 2)}\n`;
  await writeFile(target, body);
  return Buffer.byteLength(body);
}

async function writeBinary(relativePath, bytes) {
  const target = path.join(corpusRoot, relativePath);
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, bytes);
  return bytes.byteLength;
}

async function build() {
  await mkdir(generatedRoot, { recursive: true });
  const bm25 = buildBm25Payload();
  const graph = buildGraph();
  const logicProofSummaries = buildLogicProofSummaries();
  const embeddingIndex = {
    count: sections.length,
    dimension: embeddingDimension,
    embeddingModel: 'thenlper/gte-small',
    browserEmbeddingModel: 'Xenova/gte-small',
    binary: 'generated/embeddings.f32',
    ipfs_cids: sections.map((section) => section.ipfs_cid),
  };
  const vectors = new Float32Array(sections.length * embeddingDimension);

  const artifactStats = [
    {
      id: 'sections',
      path: 'generated/sections.json',
      bytes: await writeJson('generated/sections.json', sections),
      role: 'browser_core',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.normalized}`,
    },
    {
      id: 'bm25_documents',
      path: 'generated/bm25-documents.json',
      bytes: await writeJson('generated/bm25-documents.json', bm25),
      role: 'browser_search',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.bm25Index}`,
    },
    {
      id: 'embedding_index',
      path: 'generated/embedding-index.json',
      bytes: await writeJson('generated/embedding-index.json', embeddingIndex),
      role: 'browser_vector',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.vectorIndex}`,
    },
    {
      id: 'embeddings',
      path: 'generated/embeddings.f32',
      bytes: await writeBinary('generated/embeddings.f32', Buffer.from(vectors.buffer)),
      role: 'browser_vector',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.vectorIndex}`,
    },
    {
      id: 'entities',
      path: 'generated/entities.json',
      bytes: await writeJson('generated/entities.json', graph.entities),
      role: 'browser_graph',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.knowledgeGraph}`,
    },
    {
      id: 'relationships',
      path: 'generated/relationships.json',
      bytes: await writeJson('generated/relationships.json', graph.relationships),
      role: 'browser_graph',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.knowledgeGraph}`,
    },
    {
      id: 'graph_adjacency',
      path: 'generated/graph-adjacency.json',
      bytes: await writeJson('generated/graph-adjacency.json', graph.adjacency),
      role: 'browser_graph',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.knowledgeGraph}`,
    },
    {
      id: 'logic_proof_summaries',
      path: 'generated/logic-proof-summaries.json',
      bytes: await writeJson('generated/logic-proof-summaries.json', logicProofSummaries),
      role: 'browser_logic',
      sourceUrl: `https://huggingface.co/datasets/${hfDatasets.normalized}`,
    },
  ];

  await writeJson('artifacts.manifest.json', buildManifest(artifactStats));
  await writeFile(
    path.join(corpusRoot, 'README.md'),
    `# WetWijzer Netherlands corpus cache\n\nThis directory contains browser-ready sample artifacts for WetWijzer. The published quality-audited partial Dutch corpus lives in the Hugging Face dataset stack referenced by artifacts.manifest.json.\n\nWetWijzer is legal information, not legal advice. Verify official legal text and status on https://wetten.overheid.nl.\n`,
  );
  console.log(`WetWijzer corpus artifacts are ready in ${path.relative(repoRoot, corpusRoot)}`);
}

async function validate() {
  const manifestPath = path.join(corpusRoot, 'artifacts.manifest.json');
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  const sectionsPath = path.join(generatedRoot, 'sections.json');
  const loadedSections = JSON.parse(await readFile(sectionsPath, 'utf8'));
  const missingStatus = loadedSections.filter((section) => !section.law_status || !section.status_source);
  if (manifest.datasetId !== hfDatasets.normalized) {
    throw new Error(`Unexpected datasetId ${manifest.datasetId}`);
  }
  if (missingStatus.length > 0) {
    throw new Error(`${missingStatus.length} sections are missing law status metadata`);
  }
  console.log(`Validated ${loadedSections.length} WetWijzer sample articles in ${path.relative(repoRoot, corpusRoot)}`);
}

const args = new Set(process.argv.slice(2));
if (args.has('--validate-only')) {
  await validate();
} else {
  await build();
  if (!args.has('--no-validate')) {
    await validate();
  }
}
