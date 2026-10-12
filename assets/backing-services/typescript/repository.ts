/** A state service keeps one current row, not a log. The version guards the decision the caller made. */
export const NO_STATE = -1;
export type State = Readonly<Record<string, unknown>>;
export type VersionedState<T extends State = State> = Readonly<{
  id: string;
  version: number;
  state: T;
}>;
export type SaveResult =
  | Readonly<{ outcome: 'saved'; version: number }>
  | Readonly<{ outcome: 'version-conflict'; actualVersion: number }>;

export interface Repository<T extends State = State> {
  load(id: string): Promise<VersionedState<T> | null>;
  save(id: string, expectedVersion: number, state: T): Promise<SaveResult>;
  /** The readiness boundary uses this count, not event-log history. */
  head(): Promise<number>;
}

export function assertWrite(id: string, expectedVersion: number, state: State): void {
  if (!id.trim()) throw new Error('state repository requires an id');
  if (!Number.isSafeInteger(expectedVersion) || expectedVersion < NO_STATE) {
    throw new Error('expectedVersion must be NO_STATE or a non-negative safe integer');
  }
  if (state === null || typeof state !== 'object' || Array.isArray(state)) {
    throw new Error('state repository requires a JSON object');
  }
  assertJson(state, new Set());
}

/** All adapters accept the same JSON values; memory must not retain values SQL would discard. */
function assertJson(value: unknown, seen: Set<object>): void {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
  if (typeof value === 'number' && Number.isFinite(value)) return;
  if (typeof value !== 'object' || value === null || seen.has(value)) {
    throw new Error('state repository requires finite, acyclic JSON values');
  }
  if (
    !Array.isArray(value) &&
    Object.getPrototypeOf(value) !== Object.prototype &&
    Object.getPrototypeOf(value) !== null
  )
    throw new Error('state repository requires plain JSON objects');
  if (Array.isArray(value)) {
    if (Object.keys(value).length !== value.length) {
      throw new Error('state repository requires dense JSON arrays without extra properties');
    }
    for (let index = 0; index < value.length; index += 1) {
      if (!Object.hasOwn(value, index))
        throw new Error('state repository requires dense JSON arrays');
    }
  }
  seen.add(value);
  for (const item of Object.values(value)) assertJson(item, seen);
  seen.delete(value);
}
