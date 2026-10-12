import { afterAll } from 'vitest';
import { openSqliteRepository } from '../../src/adapters/driven/repository-sqlite.js';
import { repositoryContract } from './repository-contract.js';

const close: (() => void)[] = [];
repositoryContract('SQLite', async () => {
  const repository = openSqliteRepository(':memory:');
  close.push(repository.close);
  return repository;
});
afterAll(() => {
  for (const release of close) release();
});
