import {
  DcecParseToken,
  classifyDcecParseForm,
  createDcecAtom,
  createDcecConnective,
  createDcecDeonticForm,
  createDcecModalForm,
  createDcecQuantifier,
  prefixDcecEmdas,
  prefixDcecLogicalFunctions,
  replaceDcecSynonyms,
} from './dcecParsing';

describe('DCEC parsing utilities', () => {
  it('creates Python-compatible parse token expressions and measurements', () => {
    const token = new DcecParseToken('and', [
      'a',
      new DcecParseToken('not', ['b']),
      new DcecParseToken('or', ['c', 'd']),
    ]);

    expect(token.depthOf()).toBe(2);
    expect(token.widthOf()).toBe(4);
    expect(token.createSExpression()).toBe('(and a (not b) (or c d))');
    expect(token.createFExpression()).toBe('and(a,not(b),or(c,d))');
    expect(String(token)).toBe('and(a,not(b),or(c,d))');
  });

  it('replaces common DCEC spelling variants and synonyms', () => {
    const nested = new DcecParseToken('wrapper', ['forall', 'Time', 'ifAndOnlyIf']);
    const result = replaceDcecSynonyms(['ForAll', 'Exists', nested]);

    expect(result[0]).toBe('forAll');
    expect(result[1]).toBe('exists');
    expect(result[2]).toBeInstanceOf(DcecParseToken);
    expect((result[2] as DcecParseToken).args).toEqual(['forAll', 'Moment', 'iff']);
  });

  it('prefixes unary and infix logical functions in Python rule order', () => {
    const atomics: Record<string, string[]> = {};
    const unary = prefixDcecLogicalFunctions(['not', 'p'], { atomics });
    const infix = prefixDcecLogicalFunctions(['a', 'and', 'b', 'implies', 'c'], { atomics });

    expect((unary[0] as DcecParseToken).createSExpression()).toBe('(not p)');
    expect((infix[0] as DcecParseToken).createSExpression()).toBe('(implies (and a b) c)');
    expect(atomics).toEqual({
      p: ['Boolean'],
      a: ['Boolean'],
      b: ['Boolean'],
      c: ['Boolean'],
    });
  });

  it('leaves non-infix logical argument lists unchanged', () => {
    expect(prefixDcecLogicalFunctions(['and', 'a', 'b'])).toEqual(['and', 'a', 'b']);
    expect(prefixDcecLogicalFunctions(['a', 'b'])).toEqual(['a', 'b']);
  });

  it('prefixes unary and infix arithmetic functions with numeric sort tracking', () => {
    const atomics: Record<string, string[]> = {};
    const unary = prefixDcecEmdas(['negate', 'x'], { atomics });
    const infix = prefixDcecEmdas(['x', 'add', 'y', 'divide', 'z'], { atomics });

    expect((unary[0] as DcecParseToken).createFExpression()).toBe('negate(x)');
    expect((infix[0] as DcecParseToken).createFExpression()).toBe('add(x,divide(y,z))');
    expect(atomics).toEqual({
      x: ['Numeric', 'Numeric'],
      y: ['Numeric'],
      z: ['Numeric'],
    });
  });

  it('builds and classifies DCEC atom and connective parser forms', () => {
    const atom = createDcecAtom('happens', ['PayRent', 't1']);
    const connective = createDcecConnective('ifAndOnlyIf', [
      atom,
      createDcecConnective('not', [createDcecAtom('breach')]),
    ]);

    expect(atom.createSExpression()).toBe('(happens PayRent t1)');
    expect(classifyDcecParseForm(atom)).toMatchObject({
      kind: 'atom',
      predicate: 'happens',
      arguments: ['PayRent', 't1'],
    });
    expect(connective.createFExpression()).toBe('iff(happens(PayRent,t1),not(breach()))');
    expect(classifyDcecParseForm(connective)).toMatchObject({
      kind: 'connective',
      operator: 'iff',
    });
  });

  it('builds and classifies DCEC quantifier forms with default and explicit sorts', () => {
    const defaultSort = createDcecQuantifier('forall', 'x', createDcecAtom('tenant', ['x']));
    const explicitSort = createDcecQuantifier(
      'exists',
      'm',
      createDcecAtom('moment', ['m']),
      'Moment',
    );

    expect(defaultSort.createSExpression()).toBe('(forAll x Entity (tenant x))');
    expect(classifyDcecParseForm(defaultSort)).toMatchObject({
      kind: 'quantifier',
      operator: 'forAll',
      variable: 'x',
      sort: 'Entity',
    });
    expect(explicitSort.createFExpression()).toBe('exists(m,Moment,moment(m))');
    expect(classifyDcecParseForm(explicitSort).body).toBeInstanceOf(DcecParseToken);
  });

  it('builds and classifies modal and deontic parser forms', () => {
    const obligation = createDcecDeonticForm('obligation', createDcecAtom('payRent', ['tenant']));
    const permission = createDcecDeonticForm('permission', createDcecAtom('inspect'), 'landlord');
    const knowledge = createDcecModalForm('knows', 'judge', obligation);

    expect(obligation.createFExpression()).toBe('O(payRent(tenant))');
    expect(permission.createSExpression()).toBe('(P landlord (inspect))');
    expect(knowledge.createFExpression()).toBe('K(judge,O(payRent(tenant)))');
    expect(classifyDcecParseForm(obligation)).toMatchObject({ kind: 'deontic', operator: 'O' });
    expect(classifyDcecParseForm(permission).body).toBeInstanceOf(DcecParseToken);
    expect(classifyDcecParseForm(knowledge)).toMatchObject({ kind: 'modal', operator: 'K' });
  });
});
