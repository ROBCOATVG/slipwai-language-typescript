/**
 * The seed door: append the events a slice's `try-it.json` *gives*, through this service's own store port.
 *
 * `make seed-<service> FILE=<json>` runs this. The file is a list of `{ "stream", "event", "data" }`, the
 * events a story needs that the slice which would have written them has not been built yet — a view seeded
 * to a state so a person can judge it before its producers exist. They go in the way every event goes in:
 * through the event-store port, at the stream's current version, each with the context a system actor
 * writes. Never through an HTTP route — this is a process with the store's credentials, and the app serves
 * no door.
 *
 * **A replay records nothing twice**, and **a given may seal fields** under a key of the product's own
 * through the project's `scripts/seed-seal.ts`: `scripts/seed-door.ts` says how both work. **It needs the
 * durable store**: with no `DATABASE_URL` there is no log to append to, and this says so and exits 2 rather
 * than seeding an in-memory store the next process would never see.
 */
import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';
import { createPostgresEventStore } from '../src/adapters/driven/event-store-postgres/index.js';
import { type Given, parse, type Sealer, type SealHook, seedGiven } from './seed-door.js';

/** The project's sealing hook, compiled beside this file; `undefined` where the project has none. */
async function hook(pool: Pool): Promise<Sealer | undefined> {
  const where = new URL('./seed-seal.js', import.meta.url);
  if (!existsSync(fileURLToPath(where))) return undefined;
  const loaded = (await import(where.href)) as { seal?: unknown };
  if (typeof loaded.seal !== 'function')
    throw new Error('scripts/seed-seal.ts exports no `seal(request, pool)`');
  const seal = loaded.seal as SealHook;
  return (request) => seal(request, pool);
}

async function main(): Promise<number> {
  const path = process.argv[2];
  if (path === undefined) {
    process.stderr.write(
      'seed: give the file of events to append — make seed-<service> FILE=<json>\n',
    );
    return 1;
  }
  const connectionString = process.env.DATABASE_URL;
  if (connectionString === undefined || connectionString === '') {
    process.stderr.write(
      'seed: DATABASE_URL is unset, so there is no durable store to append to. The seed door needs the ' +
        'database `make services-up` starts; an in-memory store would be gone before the app read it.\n',
    );
    return 2;
  }
  const given: readonly Given[] = parse(JSON.parse(readFileSync(path, 'utf8')), path);
  const pool = new Pool({ connectionString });
  try {
    const sealer = given.some((one) => one.seal !== undefined) ? await hook(pool) : undefined;
    const store = createPostgresEventStore(pool);
    const { appended, skipped } = await seedGiven(store, given, randomUUID(), sealer);
    process.stdout.write(`seed: ${appended} event(s) appended, ${skipped} already there\n`);
    return 0;
  } finally {
    await pool.end();
  }
}

main().then(
  (code) => {
    process.exitCode = code;
  },
  (failure: unknown) => {
    process.stderr.write(`seed: ${failure instanceof Error ? failure.message : String(failure)}\n`);
    process.exitCode = 1;
  },
);
