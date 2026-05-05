import {
  DCEC_INTEGRATION_METADATA,
  formulaToDcecToken,
  parseDcecExpressionToToken,
  parseDcecString,
  tokenToDcecFormula,
  validateDcecRoundTrip,
  validateDcecFormula,
} from './dcecIntegration';
import { DcecParseToken } from './dcecParsing';

describe('DCEC integration parser', () => {
  it('parses infix logical expressions into DCEC formula objects', () => {
    const token = parseDcecExpressionToToken('a implies b');
    const formula = token && tokenToDcecFormula(token);

    expect(token?.createSExpression()).toBe('(implies a b)');
    expect(String(formula)).toBe('(a() → b())');
  });

  it('parses function-style deontic, cognitive, and temporal expressions', () => {
    expect(String(parseDcecString('O(agent, t1, must_review)'))).toBe('O(must_review())');
    expect(String(parseDcecString('B(alice, filed)'))).toBe('B(alice:Agent, filed())');
    expect(String(parseDcecString('always(approved)'))).toBe('□(approved())');
    expect(String(parseDcecString('eventually(hearing)'))).toBe('◊(hearing())');
    expect(String(parseDcecString('next(not(denied))'))).toBe('X(¬(denied()))');
  });

  it('creates atomic formulas with object terms for unknown predicates', () => {
    const formula = parseDcecString('Happens(Appeal, t)');

    expect(String(formula)).toBe('Happens(Appeal(), t:Object)');
    expect([...formula!.getFreeVariables()].map(String)).toEqual(['t:Object']);
  });

  it('supports direct ParseToken to formula conversion', () => {
    const token = new DcecParseToken('and', [
      new DcecParseToken('not', ['p']),
      new DcecParseToken('or', ['q', 'r']),
    ]);

    expect(String(tokenToDcecFormula(token))).toBe('(¬(p()) ∧ (q() ∨ r()))');
  });

  it('exposes browser-native CEC bridge metadata for the Python integration module', () => {
    expect(DCEC_INTEGRATION_METADATA).toMatchObject({
      sourcePythonModule: 'logic/CEC/native/dcec_integration.py',
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
    });
    expect(DCEC_INTEGRATION_METADATA.supportedConversions).toContain('formula-to-token');
  });

  it('converts DCEC formulas back to tokens for round-trip validation', () => {
    const formula = parseDcecString('B(alice, filed)')!;
    const token = formulaToDcecToken(formula);

    expect(token.createSExpression()).toBe('(B alice (atomic filed))');
    expect(String(tokenToDcecFormula(token))).toBe('B(alice:Agent, filed())');
  });

  it('round-trips token, formula, and canonical metadata without Python runtime bridges', () => {
    const result = validateDcecRoundTrip('P(agent, t1, inspect)');

    expect(result).toMatchObject({
      ok: true,
      canonicalSExpression: '(P agent t1 inspect)',
      canonicalFormula: 'P(inspect())',
      roundTripSExpression: '(P (atomic inspect))',
      roundTripFormulaText: 'P(inspect())',
      metadata: {
        sourcePythonModule: 'logic/CEC/native/dcec_integration.py',
        pythonRuntime: false,
        serverRuntime: false,
      },
    });
  });

  it('normalizes comments, whitespace, and prefix not syntax in the string pipeline', () => {
    expect(String(parseDcecString('  not denied ; trailing comment'))).toBe('¬(denied())');
    expect(String(parseDcecString('  ((approved)) # trailing comment'))).toBe('approved()');
  });

  it('validates parsed formulas and reports malformed parentheses', () => {
    const formula = parseDcecString('P(agent, t, inspect)');

    expect(validateDcecFormula(formula!)).toEqual({ ok: true, errors: [] });
    expect(() => parseDcecExpressionToToken('(and a b')).toThrow('Unbalanced parentheses');
  });
});
