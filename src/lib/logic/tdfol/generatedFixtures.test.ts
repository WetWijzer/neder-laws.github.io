import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import { parseTdfolFormula } from './parser';

interface GeneratedLogicProofSummary {
  identifier: string;
  norm_type: string;
  deontic_temporal_fol: string;
}

const fixturePath = resolve(
  process.cwd(),
  'public/corpus/netherlands/current/generated/logic-proof-summaries.json',
);

function loadGeneratedSummaries(): GeneratedLogicProofSummary[] {
  return JSON.parse(readFileSync(fixturePath, 'utf8')) as GeneratedLogicProofSummary[];
}

describe('TDFOL generated WetWijzer fixtures', () => {
  it('parses representative generated norm formulas', () => {
    const summaries = loadGeneratedSummaries();
    const samples = ['obligation', 'permission', 'prohibition'].map((normType) => {
      const summary = summaries.find((row) => row.norm_type === normType);
      if (!summary) {
        throw new Error(`Missing generated ${normType} fixture`);
      }
      return summary;
    });

    expect(samples.map((sample) => sample.identifier)).toEqual([
      'Wetboek van Strafrecht, Artikel 1',
      'Burgerlijk Wetboek Boek 1, Artikel 1',
      'Wetboek van Burgerlijke Rechtsvordering, Artikel 1',
    ]);

    for (const sample of samples) {
      const formula = parseTdfolFormula(sample.deontic_temporal_fol);
      const formatted = formatTdfolFormula(formula);

      expect(containsFormulaKind(formula, 'quantified')).toBe(true);
      expect(containsFormulaKind(formula, 'deontic')).toBe(true);
      if (sample.norm_type === 'permission') {
        expect(formatted).toContain('ExerciseAuthority');
      } else if (sample.norm_type === 'prohibition') {
        expect(formatted).toContain('Violate');
      } else {
        expect(formatted).toContain('ComplyWith');
      }
    }
  });

  it('parses at least 95 percent of generated TDFOL formulas', () => {
    const summaries = loadGeneratedSummaries();
    const failures: Array<{ identifier: string; error: string }> = [];

    for (const summary of summaries) {
      try {
        parseTdfolFormula(summary.deontic_temporal_fol);
      } catch (error) {
        failures.push({
          identifier: summary.identifier,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    const successRate = (summaries.length - failures.length) / summaries.length;
    expect(successRate).toBeGreaterThanOrEqual(0.95);
  });
});

function containsFormulaKind(formula: TdfolFormula, kind: TdfolFormula['kind']): boolean {
  if (formula.kind === kind) return true;
  if (formula.kind === 'binary') return containsFormulaKind(formula.left, kind) || containsFormulaKind(formula.right, kind);
  if (formula.kind === 'unary' || formula.kind === 'deontic' || formula.kind === 'temporal' || formula.kind === 'quantified') {
    return containsFormulaKind(formula.formula, kind);
  }
  return false;
}
