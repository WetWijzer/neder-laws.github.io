import type { CorpusEntity, CorpusRelationship, CorpusSection } from './netherlandsCorpus';
import type { LogicProofSummary } from './netherlandsLogic';

export const DEFAULT_CHAT_PROMPTS = [
  'What does this article require?',
  'Who is affected by this article?',
  'What evidence supports this answer?',
  'What exceptions or conditions matter here?',
  'How does this article connect to related legal provisions?',
  'What logic rule or theorem best describes this article?',
];

export function buildChatPromptStarters(
  section: CorpusSection,
  proof: LogicProofSummary | null,
  relatedEntities: CorpusEntity[],
  relatedRelationships: CorpusRelationship[],
) {
  const prompts: string[] = [];
  const identifier = section.bluebook_citation || section.official_cite || section.identifier;
  const sectionLabel = identifier || section.title;
  const topEntities = relatedEntities
    .filter((entity) => entity.id !== section.ipfs_cid)
    .slice(0, 4);
  const topRelationships = relatedRelationships.slice(0, 4);
  const actorEntity = topEntities.find((entity) => /actor|subject/i.test(entity.type));
  const obligationEntity = topEntities.find((entity) => /requirement|permit|license|notice|appeal|violation/i.test(entity.label));

  const addPrompt = (prompt: string) => {
    const normalized = prompt.trim();
    if (!normalized || prompts.includes(normalized)) {
      return;
    }
    prompts.push(normalized);
  };

  DEFAULT_CHAT_PROMPTS.forEach(addPrompt);
  addPrompt(`What does ${sectionLabel} require in plain language?`);
  addPrompt(`What deadlines, notice rules, or triggering conditions appear in ${sectionLabel}?`);
  addPrompt(`What exceptions, defenses, or carve-outs limit ${sectionLabel}?`);

  if (actorEntity) {
    addPrompt(`What duties does ${sectionLabel} impose on ${entityPromptLabel(actorEntity)}?`);
    addPrompt(`How would ${entityPromptLabel(actorEntity)} need to comply with ${sectionLabel}?`);
  }

  if (obligationEntity) {
    addPrompt(`How does ${sectionLabel} treat ${entityPromptLabel(obligationEntity)}?`);
  }

  topRelationships.forEach((relationship) => {
    addPrompt(
      `What evidence shows how ${formatGraphNodeLabel(relationship.source)} ${formatGraphTypeLabel(relationship.type).toLowerCase()} ${formatGraphNodeLabel(relationship.target)}?`,
    );
  });

  topEntities.forEach((entity) => {
    addPrompt(`How is ${sectionLabel} connected to ${entityPromptLabel(entity)} in the knowledge graph?`);
  });

  if (proof) {
    const normLabel = proof.norm_type !== 'unknown' ? proof.norm_type : 'rule';
    const operatorLabel = proof.norm_operator !== 'unknown' ? proof.norm_operator : 'logic';
    addPrompt(`What ${normLabel} does the theorem for ${sectionLabel} formalize?`);
    addPrompt(`Explain the ${operatorLabel}-based theorem for ${sectionLabel} in plain language.`);
    if (proof.deontic_temporal_fol) {
      addPrompt(`How does the temporal theorem for ${sectionLabel} map back to the legal text?`);
    }
    if (proof.deontic_cognitive_event_calculus) {
      addPrompt(`What event sequence or enforcement logic is captured for ${sectionLabel}?`);
    }
    if (proof.zkp_verified) {
      addPrompt(`What proof-backed conclusions about ${sectionLabel} are certificate-verified?`);
    }
  }

  addPrompt(`Which related articles should I compare with ${sectionLabel}?`);
  addPrompt(`What facts from the knowledge graph would help interpret ${sectionLabel}?`);

  return prompts.slice(0, 22);
}

function entityPromptLabel(entity: CorpusEntity) {
  return entity.label?.trim() || formatGraphNodeLabel(entity.id);
}

function formatGraphTypeLabel(type: string) {
  const withoutTechnicalSuffix = type.replace(/_cid$/i, '');
  return withoutTechnicalSuffix
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatGraphNodeLabel(nodeId: string) {
  if (nodeId.startsWith('bafk')) return 'This article';
  const [prefix, value] = nodeId.split(':');
  if (!value) return nodeId;
  if (prefix === 'netherlands_law') return formatGraphValueLabel(value);
  if (prefix === 'netherlands_law_title') return formatGraphValueLabel(value);
  if (prefix === 'netherlands_law_chapter') return formatGraphValueLabel(value);
  if (prefix === 'netherlands_law_section') return `Article ${value.replace(/_/g, '.')}`;
  if (prefix === 'netherlands_article') return `Article ${value.replace(/_/g, '.')}`;
  if (prefix === 'netherlands_status') return `Status ${value}`;
  if (prefix === 'netherlands_source') return formatGraphValueLabel(value);
  if (prefix === 'legal_actor') return formatGraphValueLabel(value);
  if (prefix === 'legal_subject') return formatGraphValueLabel(value);
  if (prefix === 'legal_instrument') return `Instrument ${value}`;
  if (prefix === 'jurisdiction') return value;
  return formatGraphValueLabel(value);
}

function formatGraphValueLabel(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
