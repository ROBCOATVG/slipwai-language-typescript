import { randomUUID } from 'node:crypto';
import { beforeEach, describe, expect, it } from 'vitest';
import type { Repository } from '../../src/application/ports/repository.js';
import { NO_STATE } from '../../src/application/ports/repository.js';

/** One contract on memory, SQLite and Postgres; no adapter gets its own version of the business rule. */
export function repositoryContract(name: string, create: () => Promise<Repository>): void {
  describe(`${name} satisfies the repository port`, () => {
    let repository: Repository;
    let id: string;
    beforeEach(async () => {
      repository = await create();
      id = randomUUID();
    });
    it('reads an unknown row as absent', async () => {
      expect(await repository.load(id)).toBeNull();
    });
    it('creates at NO_STATE and updates only at the version it read', async () => {
      expect(await repository.save(id, NO_STATE, { status: 'draft' })).toEqual({
        outcome: 'saved',
        version: 0,
      });
      expect(await repository.save(id, 0, { status: 'confirmed' })).toEqual({
        outcome: 'saved',
        version: 1,
      });
      expect(await repository.load(id)).toEqual({ id, version: 1, state: { status: 'confirmed' } });
    });
    it('refuses a stale decision and leaves the winning state alone', async () => {
      await repository.save(id, NO_STATE, { status: 'draft' });
      await repository.save(id, 0, { status: 'confirmed' });
      expect(await repository.save(id, 0, { status: 'cancelled' })).toEqual({
        outcome: 'version-conflict',
        actualVersion: 1,
      });
      expect((await repository.load(id))?.state).toEqual({ status: 'confirmed' });
    });
    it('cannot manufacture a missing row from a noninitial expected version', async () => {
      expect(await repository.save(id, 0, { status: 'confirmed' })).toEqual({
        outcome: 'version-conflict',
        actualVersion: NO_STATE,
      });
      expect(await repository.load(id)).toBeNull();
    });
    it('gives exactly one of two same-version decisions the win', async () => {
      await repository.save(id, NO_STATE, { writer: 'original' });
      const results = await Promise.all([
        repository.save(id, 0, { writer: 'one' }),
        repository.save(id, 0, { writer: 'two' }),
      ]);
      expect(results.filter((result) => result.outcome === 'saved')).toHaveLength(1);
      expect(results.filter((result) => result.outcome === 'version-conflict')).toHaveLength(1);
      expect((await repository.load(id))?.version).toBe(1);
    });
    it('rejects values that would change when stored as JSON', async () => {
      for (const state of [
        { bad: undefined },
        { bad: Number.NaN },
        { bad: new Date() },
        { items: new Array(2) },
      ]) {
        await expect(repository.save(id, NO_STATE, state)).rejects.toThrow('JSON');
        expect(await repository.load(id)).toBeNull();
      }
    });
    it('does not share mutable objects with the caller', async () => {
      const state = { nested: { count: 1 } };
      await repository.save(id, NO_STATE, state);
      state.nested.count = 10;
      expect((await repository.load(id))?.state).toEqual({ nested: { count: 1 } });
    });
  });
}
