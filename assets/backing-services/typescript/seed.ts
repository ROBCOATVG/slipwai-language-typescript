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
 * **A replay records nothing twice.** An event's identity here is the hash of its stream, its type and its
 * data; one already on the stream with the same hash is skipped, so `make try-update` seeding the same
 * stories into the same database adds nothing. **It needs the durable store**: with no `DATABASE_URL`
 * there is no log to append to, and this says so and exits 2 rather than seeding an in-memory store the
 * next process would never see.
 */
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { Pool } from 'pg';
import { createPostgresEventStore } from '../src/adapters/driven/event-store-postgres/index.js';
import type { DomainEvent } from '../src/application/ports/events.js';
import { createEventContext } from '../src/application/ports/events.js';

type Given = Readonly<{
  stream: string;
  event: string;
  data: Record<string, unknown>;
  slice?: string;
}>;

const canonical = (value: unknown): string =>
  JSON.stringify(value, (_key, held: unknown) =>
    held !== null && typeof held === 'object' && !Array.isArray(held)
      ? Object.fromEntries(
          Object.entries(held as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b)),
        )
      : held,
  );

const identity = (stream: string, type: string, data: unknown): string =>
  createHash('sha256')
    .update(`${stream}\u0000${type}\u0000${canonical(data)}`)
    .digest('hex');

function read(path: string): readonly Given[] {
  const parsed: unknown = JSON.parse(readFileSync(path, 'utf8'));
  if (!Array.isArray(parsed)) throw new Error(`${path} is a list of { stream, event, data }`);
  return parsed.map((one, index) => {
    if (one === null || typeof one !== 'object')
      throw new Error(`given ${index + 1} is not an object`);
    const held = one as Record<string, unknown>;
    if (typeof held.stream !== 'string' || held.stream.trim() === '')
      throw new Error(`given ${index + 1} names no stream`);
    if (typeof held.event !== 'string' || held.event.trim() === '')
      throw new Error(`given ${index + 1} names no event`);
    if (held.data === null || typeof held.data !== 'object' || Array.isArray(held.data))
      throw new Error(`given ${index + 1}'s data is an object in the model's shape`);
    const given: Given = {
      stream: held.stream,
      event: held.event,
      data: held.data as Record<string, unknown>,
      ...(typeof held.slice === 'string' ? { slice: held.slice } : {}),
    };
    return given;
  });
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
  const given = read(path);
  const pool = new Pool({ connectionString });
  const store = createPostgresEventStore(pool);
  const correlation = randomUUID();
  let appended = 0;
  let skipped = 0;
  try {
    for (const one of given) {
      const existing = await store.read(one.stream);
      const seen = new Set(
        existing.map((event) => identity(event.streamId, event.type, event.payload)),
      );
      if (seen.has(identity(one.stream, one.event, one.data))) {
        skipped += 1;
        continue;
      }
      const event: DomainEvent = {
        type: one.event,
        schemaVersion: 1,
        streamId: one.stream,
        payload: one.data,
        context: createEventContext({
          actor_id: 'systems/seed-door',
          occurred_at: new Date().toISOString(),
          correlation_id: correlation as never,
          causation_id: null,
        }),
      };
      const version = existing.length === 0 ? -1 : (existing[existing.length - 1]?.version ?? -1);
      const result = await store.append(one.stream, version, [event]);
      if (result.outcome !== 'appended') {
        process.stderr.write(
          `seed: ${one.event} on ${one.stream} was not appended: the stream moved to version ` +
            `${result.actualVersion} while this ran. Run it again.\n`,
        );
        return 1;
      }
      appended += 1;
    }
  } finally {
    await pool.end();
  }
  process.stdout.write(`seed: ${appended} event(s) appended, ${skipped} already there\n`);
  return 0;
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
