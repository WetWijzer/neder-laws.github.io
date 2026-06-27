import {
  normalizeWetWijzerIdentifier,
  normalizePredicateName,
  normalizeWhitespace,
  objectIdToWetWijzerIdentifier,
  netherlandsIdentifierToObjectId,
} from './normalization';

describe('logic normalization helpers', () => {
  it('normalizes whitespace', () => {
    expect(normalizeWhitespace('  Dutch   law\narticle  ')).toBe('Dutch law article');
  });

  it('normalizes predicate names for generated formulas', () => {
    expect(normalizePredicateName('ComplyWith')).toBe('comply_with');
    expect(normalizePredicateName('  has review-authority  ')).toBe('has_review_authority');
    expect(normalizePredicateName('1.01.010')).toBe('p_1_01_010');
    expect(normalizePredicateName(' *** ')).toBe('unknown');
  });

  it('normalizes WetWijzer identifiers and aliases', () => {
    expect(normalizeWetWijzerIdentifier('netherlands law 1.01.010')).toBe('Dutch legal corpus 1.01.010');
    expect(normalizeWetWijzerIdentifier('WetWijzer Article 9.01.050')).toBe('Dutch legal corpus 9.01.050');
    expect(normalizeWetWijzerIdentifier('Some Other Citation')).toBe('Some Other Citation');
  });

  it('converts WetWijzer identifiers to generated object IDs and back', () => {
    expect(netherlandsIdentifierToObjectId('Dutch legal corpus 1.01.010')).toBe(
      'netherlands_law_article_1_01_010',
    );
    expect(objectIdToWetWijzerIdentifier('netherlands_law_article_9_01_050')).toBe(
      'Dutch legal corpus 9.01.050',
    );
    expect(objectIdToWetWijzerIdentifier('not_a_netherlands_section')).toBeNull();
  });
});
