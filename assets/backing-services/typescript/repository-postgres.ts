import type { Pool } from 'pg';
import type { Repository, State } from '../../../application/ports/repository.js';
import { assertWrite, NO_STATE } from '../../../application/ports/repository.js';

type Row<T extends State> = { id: string; version: number; state: T };

/** One SQL compare-and-swap; the memory fake and this adapter satisfy the same contract. */
export function createPostgresRepository<T extends State = State>(pool: Pool): Repository<T> {
  return {
    load: async (id) =>
      (await pool.query<Row<T>>('SELECT id, version, state FROM states WHERE id = $1', [id]))
        .rows[0] ?? null,
    save: async (id, expectedVersion, state) => {
      assertWrite(id, expectedVersion, state);
      const changed =
        expectedVersion === NO_STATE
          ? await pool.query<{ version: number }>(
              'INSERT INTO states (id, version, state) VALUES ($1, 0, $2::jsonb) ON CONFLICT DO NOTHING RETURNING version',
              [id, JSON.stringify(state)],
            )
          : await pool.query<{ version: number }>(
              'UPDATE states SET state = $3::jsonb, version = version + 1 WHERE id = $1 AND version = $2 RETURNING version',
              [id, expectedVersion, JSON.stringify(state)],
            );
      const saved = changed.rows[0];
      if (saved !== undefined) return { outcome: 'saved', version: saved.version };
      const actual = await pool.query<{ version: number }>(
        'SELECT version FROM states WHERE id = $1',
        [id],
      );
      return { outcome: 'version-conflict', actualVersion: actual.rows[0]?.version ?? NO_STATE };
    },
    head: async () =>
      Number(
        (await pool.query<{ count: string }>('SELECT count(*) AS count FROM states')).rows[0]
          ?.count ?? 0,
      ),
  };
}
