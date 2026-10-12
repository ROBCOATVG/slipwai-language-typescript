import { DatabaseSync } from 'node:sqlite';
import type { Repository, State } from '../../application/ports/repository.js';
import { assertWrite, NO_STATE } from '../../application/ports/repository.js';

/** SQLite serialises writes; shared CAS semantics still hold. Genuine contention is proved on Postgres. */
export function openSqliteRepository<T extends State = State>(
  path: string,
): Repository<T> & { close(): void } {
  const database = new DatabaseSync(path);
  database.exec(
    'CREATE TABLE IF NOT EXISTS states (id TEXT PRIMARY KEY, version INTEGER NOT NULL CHECK (version >= 0), state TEXT NOT NULL)',
  );
  return {
    load: async (id) => {
      const row = database.prepare('SELECT id, version, state FROM states WHERE id = ?').get(id);
      return row === undefined
        ? null
        : {
            id: String(row.id),
            version: Number(row.version),
            state: JSON.parse(String(row.state)) as T,
          };
    },
    save: async (id, expectedVersion, state) => {
      assertWrite(id, expectedVersion, state);
      const changed =
        expectedVersion === NO_STATE
          ? database
              .prepare(
                'INSERT INTO states (id, version, state) VALUES (?, 0, ?) ON CONFLICT DO NOTHING RETURNING version',
              )
              .get(id, JSON.stringify(state))
          : database
              .prepare(
                'UPDATE states SET state = ?, version = version + 1 WHERE id = ? AND version = ? RETURNING version',
              )
              .get(JSON.stringify(state), id, expectedVersion);
      if (changed !== undefined) return { outcome: 'saved', version: Number(changed.version) };
      const actual = database.prepare('SELECT version FROM states WHERE id = ?').get(id);
      return {
        outcome: 'version-conflict',
        actualVersion: actual === undefined ? NO_STATE : Number(actual.version),
      };
    },
    head: async () =>
      Number(database.prepare('SELECT count(*) AS count FROM states').get()?.count ?? 0),
    close: () => database.close(),
  };
}
