export function normalizeWhitespace(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

export function normalizePredicateName(value: string): string {
  const normalized = value
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[^A-Za-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase();

  if (!normalized) {
    return 'unknown';
  }

  if (/^[0-9]/.test(normalized)) {
    return `p_${normalized}`;
  }

  return normalized;
}

export function normalizeWetWijzerIdentifier(value: string): string {
  const normalized = normalizeWhitespace(value)
    .replace(/^netherlands law\s+/i, 'Dutch legal corpus ')
    .replace(/^netherlands\s+code\s+/i, 'Dutch legal corpus ')
    .replace(/^netherlands\s+city\s+code\s+/i, 'Dutch legal corpus ')
    .replace(/\s+/g, ' ');

  const citation = normalized.match(/(\d+)\.(\d+)\.(\d+)/);
  if (!citation) {
    return normalized;
  }

  return `Dutch legal corpus ${citation[1]}.${citation[2]}.${citation[3]}`;
}

export function netherlandsIdentifierToObjectId(value: string): string {
  const identifier = normalizeWetWijzerIdentifier(value);
  const citation = identifier.match(/(\d+)\.(\d+)\.(\d+)/);
  if (!citation) {
    return normalizePredicateName(identifier);
  }
  return `netherlands_law_article_${citation[1]}_${citation[2]}_${citation[3]}`;
}

export function objectIdToWetWijzerIdentifier(value: string): string | null {
  const match = value.match(/netherlands_law_article_(\d+)_(\d+)_(\d+)/i);
  if (!match) {
    return null;
  }
  return `Dutch legal corpus ${match[1]}.${match[2]}.${match[3]}`;
}

