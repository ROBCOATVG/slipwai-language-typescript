import type { Repository, State, VersionedState } from '../../application/ports/repository.js';
import { assertWrite, NO_STATE } from '../../application/ports/repository.js';

/** The memory fake proves CAS semantics; real competing database writers are tested on Postgres. */
export function createInMemoryRepository<T extends State = State>(): Repository<T> {
  const rows = new Map<string, VersionedState<T>>();
  return {
    load: async (id) => {
      const row = rows.get(id);
      return row === undefined ? null : structuredClone(row);
    },
    save: async (id, expectedVersion, state) => {
      assertWrite(id, expectedVersion, state);
      const actualVersion = rows.get(id)?.version ?? NO_STATE;
      if (actualVersion !== expectedVersion) return { outcome: 'version-conflict', actualVersion };
      const version = actualVersion + 1;
      rows.set(id, { id, version, state: structuredClone(state) });
      return { outcome: 'saved', version };
    },
    head: async () => rows.size,
  };
}
