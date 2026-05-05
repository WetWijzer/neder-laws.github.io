export const DcecDeonticOperator = {
  OBLIGATION: 'O',
  OBLIGATORY: 'O',
  PERMISSION: 'P',
  PROHIBITION: 'F',
  SUPEREROGATION: 'S',
  RIGHT: 'R',
  LIBERTY: 'L',
  POWER: 'POW',
  IMMUNITY: 'IMM',
} as const;

export const DcecCognitiveOperator = {
  BELIEF: 'B',
  BELIEVES: 'B',
  KNOWLEDGE: 'K',
  KNOWS: 'K',
  INTENTION: 'I',
  DESIRE: 'D',
  GOAL: 'G',
  PERCEPTION: 'P',
} as const;

export const DcecLogicalConnective = {
  AND: 'and',
  OR: 'or',
  NOT: 'not',
  IMPLIES: 'implies',
  BICONDITIONAL: 'iff',
  IFF: 'iff',
  EXISTS: 'exists',
  FORALL: 'forAll',
} as const;

export const DcecTemporalOperator = {
  ALWAYS: 'always',
  EVENTUALLY: 'eventually',
  NEXT: 'next',
  UNTIL: 'until',
  SINCE: 'since',
} as const;

export type DcecDeonticOperatorValue =
  (typeof DcecDeonticOperator)[keyof typeof DcecDeonticOperator];
export type DcecCognitiveOperatorValue =
  (typeof DcecCognitiveOperator)[keyof typeof DcecCognitiveOperator];
export type DcecLogicalConnectiveValue =
  (typeof DcecLogicalConnective)[keyof typeof DcecLogicalConnective];
export type DcecTemporalOperatorValue =
  (typeof DcecTemporalOperator)[keyof typeof DcecTemporalOperator];

export interface DcecSortJson {
  readonly kind: 'sort';
  readonly name: string;
  readonly parent?: string;
}

export interface DcecVariableJson {
  readonly kind: 'variable';
  readonly name: string;
  readonly sort: string;
}

export interface DcecFunctionSymbolJson {
  readonly kind: 'function';
  readonly name: string;
  readonly argumentSorts: string[];
  readonly returnSort: string;
}

export interface DcecPredicateSymbolJson {
  readonly kind: 'predicate';
  readonly name: string;
  readonly argumentSorts: string[];
}

export type DcecSymbolJson =
  | DcecSortJson
  | DcecVariableJson
  | DcecFunctionSymbolJson
  | DcecPredicateSymbolJson;

export interface DcecSymbolContainerJson {
  readonly sorts: DcecSortJson[];
  readonly variables: DcecVariableJson[];
  readonly functions: DcecFunctionSymbolJson[];
  readonly predicates: DcecPredicateSymbolJson[];
}

export interface DcecSymbolContainerInput {
  readonly sorts?: Iterable<DcecSort>;
  readonly variables?: Iterable<DcecVariable>;
  readonly functions?: Iterable<DcecFunctionSymbol>;
  readonly predicates?: Iterable<DcecPredicateSymbol>;
}

export class DcecSort {
  readonly name: string;
  readonly parent?: DcecSort;

  constructor(name: string, parent?: DcecSort) {
    this.name = name;
    this.parent = parent;
  }

  isSubtypeOf(other: DcecSort): boolean {
    if (this.name === other.name) return true;
    return this.parent?.isSubtypeOf(other) ?? false;
  }

  toString(): string {
    return this.name;
  }
}

export class DcecVariable {
  readonly name: string;
  readonly sort: DcecSort;

  constructor(name: string, sort: DcecSort) {
    this.name = name;
    this.sort = sort;
  }

  toString(): string {
    return `${this.name}:${this.sort.name}`;
  }
}

export class DcecFunctionSymbol {
  readonly name: string;
  readonly argumentSorts: DcecSort[];
  readonly returnSort: DcecSort;

  constructor(name: string, argumentSorts: DcecSort[], returnSort: DcecSort) {
    this.name = name;
    this.argumentSorts = [...argumentSorts];
    this.returnSort = returnSort;
  }

  arity(): number {
    return this.argumentSorts.length;
  }

  toString(): string {
    return `${this.name}(${this.argumentSorts.map((sort) => sort.name).join(', ')}) -> ${this.returnSort.name}`;
  }
}

export class DcecPredicateSymbol {
  readonly name: string;
  readonly argumentSorts: DcecSort[];

  constructor(name: string, argumentSorts: DcecSort[]) {
    this.name = name;
    this.argumentSorts = [...argumentSorts];
  }

  arity(): number {
    return this.argumentSorts.length;
  }

  toString(): string {
    return `${this.name}(${this.argumentSorts.map((sort) => sort.name).join(', ')})`;
  }
}

export const isDcecSort = (value: unknown): value is DcecSort => value instanceof DcecSort;
export const isDcecVariable = (value: unknown): value is DcecVariable =>
  value instanceof DcecVariable;
export const isDcecFunctionSymbol = (value: unknown): value is DcecFunctionSymbol =>
  value instanceof DcecFunctionSymbol;
export const isDcecPredicateSymbol = (value: unknown): value is DcecPredicateSymbol =>
  value instanceof DcecPredicateSymbol;

export function isDcecSymbolJson(value: unknown): value is DcecSymbolJson {
  if (!isRecord(value) || typeof value.kind !== 'string' || typeof value.name !== 'string') {
    return false;
  }

  if (value.kind === 'sort') {
    return value.parent === undefined || typeof value.parent === 'string';
  }
  if (value.kind === 'variable') {
    return typeof value.sort === 'string';
  }
  if (value.kind === 'function') {
    return (
      Array.isArray(value.argumentSorts) &&
      value.argumentSorts.every((sort) => typeof sort === 'string') &&
      typeof value.returnSort === 'string'
    );
  }
  if (value.kind === 'predicate') {
    return (
      Array.isArray(value.argumentSorts) &&
      value.argumentSorts.every((sort) => typeof sort === 'string')
    );
  }
  return false;
}

export function serializeDcecSort(sort: DcecSort): DcecSortJson {
  const json: { kind: 'sort'; name: string; parent?: string } = {
    kind: 'sort',
    name: sort.name,
  };
  if (sort.parent !== undefined) json.parent = sort.parent.name;
  return json;
}

export function serializeDcecVariable(variable: DcecVariable): DcecVariableJson {
  return {
    kind: 'variable',
    name: variable.name,
    sort: variable.sort.name,
  };
}

export function serializeDcecFunctionSymbol(symbol: DcecFunctionSymbol): DcecFunctionSymbolJson {
  return {
    kind: 'function',
    name: symbol.name,
    argumentSorts: symbol.argumentSorts.map((sort) => sort.name),
    returnSort: symbol.returnSort.name,
  };
}

export function serializeDcecPredicateSymbol(symbol: DcecPredicateSymbol): DcecPredicateSymbolJson {
  return {
    kind: 'predicate',
    name: symbol.name,
    argumentSorts: symbol.argumentSorts.map((sort) => sort.name),
  };
}

export function serializeDcecSymbolContainer(
  container: DcecSymbolContainerInput,
): DcecSymbolContainerJson {
  return {
    sorts: [...(container.sorts ?? [])].map(serializeDcecSort),
    variables: [...(container.variables ?? [])].map(serializeDcecVariable),
    functions: [...(container.functions ?? [])].map(serializeDcecFunctionSymbol),
    predicates: [...(container.predicates ?? [])].map(serializeDcecPredicateSymbol),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}
