import { createInMemoryRepository } from '../../src/adapters/driven/repository-memory.js';
import { repositoryContract } from './repository-contract.js';

repositoryContract('memory', async () => createInMemoryRepository());
