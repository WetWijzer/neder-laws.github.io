import {
  DOCUMENT_CONSISTENCY_CHECKER_METADATA,
  BrowserNativeDocumentConsistencyChecker,
  checkDocumentConsistency,
} from './documentConsistencyChecker';

describe('browser-native document consistency checker', () => {
  it('accepts supported fields and citations without Python or server runtime', () => {
    const result = checkDocumentConsistency({
      id: 'bwbr-0001854-artikel-1',
      text: 'BWBR0001854 Artikel 1 states the legaliteitsbeginsel. The official source shall be verified on wetten.overheid.nl.',
      citations: ['BWBR0001854 Artikel 1'],
      extractedFields: [
        {
          name: 'principle',
          value: 'legaliteitsbeginsel',
          evidence: 'legaliteitsbeginsel',
          required: true,
        },
        { name: 'source', value: 'wetten.overheid.nl', required: true },
      ],
    });

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      summary: { checkedFields: 2, matchedFields: 2, checkedCitations: 1, matchedCitations: 1 },
    });
    expect(result.metadata).toBe(DOCUMENT_CONSISTENCY_CHECKER_METADATA);
  });

  it('matches evidence snippets and normalized article citations deterministically', () => {
    const result = checkDocumentConsistency({
      id: 'bwbr-0002656-artikel-1',
      text: 'According to BWBR0002656 Artikel 1, burgerlijke rechten are addressed in the official legal text.',
      citations: ['BWBR0002656 Artikel 1'],
      extractedFields: [
        {
          name: 'subject',
          value: 'burgerlijke rechten',
          evidence: 'burgerlijke rechten',
          required: true,
        },
      ],
    });

    expect(result).toMatchObject({
      accepted: true,
      summary: {
        checkedFields: 1,
        matchedFields: 1,
        checkedCitations: 1,
        matchedCitations: 1,
      },
    });
    expect(result.issues).toEqual([]);
  });

  it('fails closed on missing evidence, missing citations, and contradictory terms', () => {
    const result = new BrowserNativeDocumentConsistencyChecker().check({
      id: 'permit-rule',
      text: 'The application is approved. The same application is denied. No permit required.',
      citations: ['BWBR0002656 Artikel 1'],
      extractedFields: [
        { name: 'permit_status', value: 'planning director approval', required: true },
      ],
    });

    expect(result.accepted).toBe(false);
    expect(result.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'field_evidence_missing',
          severity: 'error',
          field: 'permit_status',
        }),
        expect.objectContaining({
          code: 'citation_not_in_text',
          severity: 'error',
          citation: 'BWBR0002656 Artikel 1',
        }),
        expect.objectContaining({ code: 'contradictory_terms', severity: 'error' }),
      ]),
    );
    expect(result.summary).toMatchObject({
      checkedFields: 1,
      matchedFields: 0,
      checkedCitations: 1,
      matchedCitations: 0,
    });
  });
});
