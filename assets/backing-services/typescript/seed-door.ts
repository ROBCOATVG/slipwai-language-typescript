/**
 * What the seed door does with a list of givens, apart from the process that opens the database.
 *
 * `scripts/seed.ts` is the process: it reads the file, opens the durable store and, where a given seals
 * fields, loads the project's sealing hook. This is the rest, written against the event-store port so the
 * unit suite can drive it on the in-memory store.
 *
 * **A sealed field.** A product that seals personal fields under a per-workspace key — the usual
 * crypto-shredding pattern for erasure — cannot be given them as plain JSON: the folds read ciphertext, and a
 * plain email where `{ ciphertext, iv, authTag }` belongs is refused on read. So a given may say which of
 * its fields to seal and under whose key, `"seal": { "key": "<whose key>", "fields": ["email"] }`, with
 * those fields in plain text in its `data`. This package cannot know the project's cryptography, so the
 * sealing is the project's: `scripts/seed-seal.ts` exports `seal(request, pool)`, which finds the key for
 * `request.key` — minting it the first time, the way the product does when it creates the workspace — and
 * returns each named field sealed. A given that seals and a service with no hook is refused, never appended
 * in plain text.
 *
 * **A replay records nothing twice, sealed or not.** A plain event's identity is the hash of its stream, its
 * type and its data, and one already on the stream with the same hash is skipped. A sealed one cannot be
 * matched that way, because sealing the same text twice gives different ciphertext; its identity is the
 * hash of the given as written, seal and all, carried as the event's `causation_id` — the given is what
 * caused it — and a stream already holding an event with that cause skips it.
 */
import { createHash } from 'node:crypto';
import type { Pool } from 'pg';
import type { DomainEvent, EventStore } from '../src/application/ports/events.js';
import { createEventContext } from '../src/application/ports/events.js';

export type Seal = Readonly<{ key: string; fields: readonly string[] }>;

export type Given = Readonly<{
  stream: string;
  event: string;
  data: Record<string, unknown>;
  seal?: Seal;
  slice?: string;
}>;

/** What the seed door asks the project's hook to seal: each named field's plain text, and whose key. */
export type SealRequest = Readonly<{
  key: string;
  stream: string;
  event: string;
  fields: Readonly<Record<string, string>>;
}>;

/** Each requested field, sealed, in whatever shape the product's events hold a sealed value. */
export type Sealed = Readonly<Record<string, unknown>>;

/** The seed door's own view of the hook: the pool is bound by `scripts/seed.ts`. */
export type Sealer = (request: SealRequest) => Promise<Sealed>;

/** What `scripts/seed-seal.ts` exports as `seal`: the pool is the durable store's, where the keys live. */
export type SealHook = (request: SealRequest, pool: Pool) => Promise<Sealed>;

const canonical = (value: unknown): string =>
  JSON.stringify(value, (_key, held: unknown) =>
    held !== null && typeof held === 'object' && !Array.isArray(held)
      ? Object.fromEntries(
          Object.entries(held as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b)),
        )
      : held,
  );

export const identity = (stream: string, type: string, data: unknown): string =>
  createHash('sha256')
    .update(`${stream}\u0000${type}\u0000${canonical(data)}`)
    .digest('hex');

/** A sealed given's identity as a UUID, so it can be the event's `causation_id`. */
export function sealedCause(given: Given): string {
  const hex = identity(given.stream, given.event, { data: given.data, seal: given.seal });
  const variant = ((Number.parseInt(hex.slice(16, 17), 16) & 0x3) | 0x8).toString(16);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-5${hex.slice(13, 16)}-${variant}${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

function readSeal(held: unknown, index: number, data: Record<string, unknown>): Seal {
  const said = `given ${index + 1}'s seal`;
  if (held === null || typeof held !== 'object' || Array.isArray(held))
    throw new Error(`${said} is { "key": "<whose key>", "fields": ["<field>", ...] }`);
  const { key, fields } = held as Record<string, unknown>;
  if (typeof key !== 'string' || key.trim() === '') throw new Error(`${said} names no key`);
  if (
    !Array.isArray(fields) ||
    fields.length === 0 ||
    !fields.every((one) => typeof one === 'string')
  )
    throw new Error(`${said} names no fields`);
  for (const field of fields as string[]) {
    if (typeof data[field] !== 'string')
      throw new Error(`${said} names ${field}, which its data does not give as plain text`);
  }
  return { key, fields: fields as string[] };
}

export function parse(parsed: unknown, where: string): readonly Given[] {
  if (!Array.isArray(parsed)) throw new Error(`${where} is a list of { stream, event, data }`);
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
    const data = held.data as Record<string, unknown>;
    const given: Given = {
      stream: held.stream,
      event: held.event,
      data,
      ...(held.seal === undefined ? {} : { seal: readSeal(held.seal, index, data) }),
      ...(typeof held.slice === 'string' ? { slice: held.slice } : {}),
    };
    return given;
  });
}

async function sealed(
  given: Given,
  seal: Seal,
  sealer: Sealer | undefined,
): Promise<Record<string, unknown>> {
  if (sealer === undefined)
    throw new Error(
      `${given.event} on ${given.stream} seals ${seal.fields.join(', ')}, and this service has no sealing ` +
        'hook: write scripts/seed-seal.ts exporting `seal(request, pool)`, which seals each field under ' +
        'the key it names the way the product does. Nothing is appended in plain text.',
    );
  const fields = Object.fromEntries(seal.fields.map((field) => [field, String(given.data[field])]));
  const answer = await sealer({ key: seal.key, stream: given.stream, event: given.event, fields });
  for (const field of seal.fields) {
    if (!(field in answer) || answer[field] === undefined)
      throw new Error(
        `the sealing hook returned no ${field} for ${given.event} on ${given.stream}`,
      );
    if (canonical(answer[field]) === canonical(fields[field]))
      throw new Error(
        `the sealing hook returned ${field} for ${given.event} on ${given.stream} unchanged: a plain value ` +
          'where the product holds a sealed one',
      );
  }
  return {
    ...given.data,
    ...Object.fromEntries(seal.fields.map((field) => [field, answer[field]])),
  };
}

export type Seeded = Readonly<{ appended: number; skipped: number }>;

/**
 * Append each given at its stream's current version, skipping one already there. Throws, naming the given,
 * on a stream that moved while this ran, a seal with no hook, or a hook that sealed nothing.
 */
export async function seedGiven(
  store: EventStore,
  given: readonly Given[],
  correlation: string,
  sealer?: Sealer,
): Promise<Seeded> {
  let appended = 0;
  let skipped = 0;
  for (const one of given) {
    const existing = await store.read(one.stream);
    const cause = one.seal === undefined ? null : sealedCause(one);
    const seen =
      cause === null
        ? existing.some(
            (event) =>
              identity(event.streamId, event.type, event.payload) ===
              identity(one.stream, one.event, one.data),
          )
        : existing.some((event) => event.context.causation_id === cause);
    if (seen) {
      skipped += 1;
      continue;
    }
    const payload = one.seal === undefined ? one.data : await sealed(one, one.seal, sealer);
    const event: DomainEvent = {
      type: one.event,
      schemaVersion: 1,
      streamId: one.stream,
      payload,
      context: createEventContext({
        actor_id: 'systems/seed-door',
        occurred_at: new Date().toISOString(),
        correlation_id: correlation as never,
        causation_id: cause as never,
      }),
    };
    const version = existing.length === 0 ? -1 : (existing[existing.length - 1]?.version ?? -1);
    const result = await store.append(one.stream, version, [event]);
    if (result.outcome !== 'appended')
      throw new Error(
        `${one.event} on ${one.stream} was not appended: the stream moved to version ` +
          `${result.actualVersion} while this ran. Run it again.`,
      );
    appended += 1;
  }
  return { appended, skipped };
}
