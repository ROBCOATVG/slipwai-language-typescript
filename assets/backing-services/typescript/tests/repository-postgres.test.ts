import { randomUUID } from 'node:crypto';
import { Pool } from 'pg';
import { afterAll, describe, expect, it } from 'vitest';
import { createPostgresRepository } from '../../src/adapters/driven/repository-postgres/index.js';
import { NO_STATE } from '../../src/application/ports/repository.js';
import { repositoryContract } from '../contract/repository-contract.js';

const connectionString = process.env.DATABASE_URL;
if (!connectionString)
  throw new Error('DATABASE_URL is required; run make services-up migrate test-integration');
const pool = new Pool({ connectionString });
afterAll(async () => {
  await pool.end();
});
repositoryContract('Postgres', async () => createPostgresRepository(pool));
describe('Postgres with two independent connections', () => {
  it('allows exactly one concurrent CAS update and one concurrent initial insert', async () => {
    const second = new Pool({ connectionString });
    try {
      const one = createPostgresRepository(pool);
      const two = createPostgresRepository(second);
      const id = randomUUID();
      const initial = await Promise.all([
        one.save(id, NO_STATE, { writer: 'one' }),
        two.save(id, NO_STATE, { writer: 'two' }),
      ]);
      expect(initial.filter((result) => result.outcome === 'saved')).toHaveLength(1);
      expect(initial.filter((result) => result.outcome === 'version-conflict')).toEqual([
        { outcome: 'version-conflict', actualVersion: 0 },
      ]);
      const update = await Promise.all([
        one.save(id, 0, { writer: 'one' }),
        two.save(id, 0, { writer: 'two' }),
      ]);
      expect(update.filter((result) => result.outcome === 'saved')).toHaveLength(1);
      expect(update.filter((result) => result.outcome === 'version-conflict')).toEqual([
        { outcome: 'version-conflict', actualVersion: 1 },
      ]);
      const winner = update[0]?.outcome === 'saved' ? 'one' : 'two';
      expect(await one.load(id)).toEqual({ id, version: 1, state: { writer: winner } });
    } finally {
      await second.end();
    }
  });
});
