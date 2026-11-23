import { describe, expect, it } from 'vitest';
import { type Given, parse, type Sealer, sealedCause, seedGiven } from '../../scripts/seed-door.js';
import { createInMemoryEventStore } from '../../src/adapters/driven/event-store-memory.js';

/**
 * The seed door against the in-memory store: a plain given as it always was, and a sealed one (slipwai#154).
 * A founder whose email the product seals under the workspace's key could not be given at all, so the
 * screens behind an accepted invite were proven by tests alone and never walked from seeded state.
 */
const CORRELATION = '00000000-0000-4000-8000-000000000001';

const accepted: Given = {
  stream: 'invite-1',
  event: 'InviteAccepted',
  data: { workspaceId: 'ws_1', email: 'founder@example.com' },
  seal: { key: 'ws_1', fields: ['email'] },
};

/** A stand-in for a project's hook: a key per workspace, minted on first use, and a fresh nonce per seal. */
function sealer(): { seal: Sealer; minted: string[] } {
  const minted: string[] = [];
  let nonce = 0;
  const seal: Sealer = async ({ key, fields }) => {
    if (!minted.includes(key)) minted.push(key);
    nonce += 1;
    return Object.fromEntries(
      Object.entries(fields).map(([name, plain]) => [
        name,
        { ciphertext: Buffer.from(`${key}:${plain}`).toString('base64'), iv: String(nonce) },
      ]),
    );
  };
  return { seal, minted };
}

describe('the seed door', () => {
  it('appends a plain given once, however often it is replayed', async () => {
    const store = createInMemoryEventStore();
    const plain: Given = {
      stream: 'ws-1',
      event: 'WorkspaceCreated',
      data: { workspaceId: 'ws_1' },
    };
    expect(await seedGiven(store, [plain], CORRELATION)).toEqual({ appended: 1, skipped: 0 });
    expect(await seedGiven(store, [plain], CORRELATION)).toEqual({ appended: 0, skipped: 1 });
    const [event] = await store.read('ws-1');
    expect(event?.payload).toEqual({ workspaceId: 'ws_1' });
    expect(event?.context.causation_id).toBeNull();
  });

  it('seals the fields a given names under the key it names, through the hook', async () => {
    const store = createInMemoryEventStore();
    const { seal, minted } = sealer();
    await seedGiven(store, [accepted], CORRELATION, seal);
    const [event] = await store.read('invite-1');
    expect(minted).toEqual(['ws_1']);
    expect(event?.payload).toEqual({
      workspaceId: 'ws_1',
      email: { ciphertext: Buffer.from('ws_1:founder@example.com').toString('base64'), iv: '1' },
    });
    expect(JSON.stringify(event?.payload)).not.toContain('founder@example.com');
    expect(event?.context.causation_id).toBe(sealedCause(accepted));
  });

  it('records a sealed given once although each seal differs', async () => {
    const store = createInMemoryEventStore();
    const { seal } = sealer();
    await seedGiven(store, [accepted], CORRELATION, seal);
    expect(await seedGiven(store, [accepted], CORRELATION, seal)).toEqual({
      appended: 0,
      skipped: 1,
    });
    expect(await store.read('invite-1')).toHaveLength(1);
  });

  it('refuses a sealed given with no hook rather than append it in plain text', async () => {
    const store = createInMemoryEventStore();
    await expect(seedGiven(store, [accepted], CORRELATION)).rejects.toThrow(
      /no sealing hook: write scripts\/seed-seal\.ts/,
    );
    expect(await store.read('invite-1')).toHaveLength(0);
  });

  it('refuses a hook that hands a field back unsealed', async () => {
    const store = createInMemoryEventStore();
    const leaky: Sealer = async ({ fields }) => fields;
    await expect(seedGiven(store, [accepted], CORRELATION, leaky)).rejects.toThrow(/unchanged/);
    await expect(seedGiven(store, [accepted], CORRELATION, async () => ({}))).rejects.toThrow(
      /returned no email/,
    );
    expect(await store.read('invite-1')).toHaveLength(0);
  });

  it('holds a seal to its shape and to plain text the data gives', () => {
    const one = (seal: unknown, data: object = { email: 'a@b.c' }) =>
      parse([{ stream: 's', event: 'E', data, seal }], 'file.json');
    expect(one({ key: 'ws_1', fields: ['email'] })[0]?.seal).toEqual({
      key: 'ws_1',
      fields: ['email'],
    });
    expect(() => one({ fields: ['email'] })).toThrow(/names no key/);
    expect(() => one({ key: 'ws_1', fields: [] })).toThrow(/names no fields/);
    expect(() => one({ key: 'ws_1', fields: ['name'] })).toThrow(/names name/);
    expect(() => one({ key: 'ws_1', fields: ['email'] }, { email: { ciphertext: 'x' } })).toThrow(
      /as plain text/,
    );
  });

  it('gives a sealed given a cause that is a UUID and the same each time', () => {
    expect(sealedCause(accepted)).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
    expect(sealedCause(accepted)).toBe(sealedCause({ ...accepted }));
    expect(sealedCause(accepted)).not.toBe(
      sealedCause({ ...accepted, seal: { key: 'ws_2', fields: ['email'] } }),
    );
  });
});
