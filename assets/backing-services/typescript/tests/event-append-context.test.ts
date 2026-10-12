import { describe, expect, it } from 'vitest';
import { createInMemoryEventStore } from '../../src/adapters/driven/event-store-memory.js';
import { NO_STREAM } from '../../src/application/ports/events.js';

const compileOnly = () => {
  const store = createInMemoryEventStore();
  const body = {
    type: 'OrderConfirmed',
    schemaVersion: 1 as const,
    streamId: 'order-1',
    payload: { orderId: 'order-1' },
  };
  // @ts-expect-error a bare payload/body has no mandatory context
  void store.append('order-1', NO_STREAM, [body]);
  // @ts-expect-error conditional append also requires caller context
  void store.appendIf({ query: { filters: [{ tags: ['order:order-1'] }] }, after: 0 }, [body]);
};
void compileOnly;

describe('mandatory append context', () => {
  it('rejects an untyped caller before changing the stream', async () => {
    const store = createInMemoryEventStore();
    const body = { type: 'OrderConfirmed', schemaVersion: 1, streamId: 'order-1', payload: {} };
    // @ts-expect-error deliberately model a caller bypassing the TypeScript boundary
    await expect(store.append('order-1', NO_STREAM, [body])).rejects.toThrow('actor_id');
    expect(await store.read('order-1')).toEqual([]);
  });
});
