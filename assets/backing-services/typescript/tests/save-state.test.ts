import { describe, expect, it } from 'vitest';
import { createInMemoryRepository } from '../../src/adapters/driven/repository-memory.js';
import type { RaisedEvent } from '../../src/application/ports/event-context.js';
import {
  createCorrelationId,
  createEventContext,
} from '../../src/application/ports/event-context.js';
import { NO_STATE } from '../../src/application/ports/repository.js';
import { saveAndRaise } from '../../src/application/save-state.js';

describe('the state use case', () => {
  it('raises only after its version wins, with caller context mandatory', async () => {
    const repository = createInMemoryRepository();
    const published: RaisedEvent[] = [];
    const publish = async (event: RaisedEvent) => {
      published.push(event);
    };
    const context = createEventContext({
      actor_id: 'customer-1',
      occurred_at: '2024-01-01T00:00:00.000Z',
      correlation_id: createCorrelationId('00000000-0000-0000-0000-000000000001'),
      causation_id: null,
    });
    const fact = {
      type: 'OrderConfirmed',
      schemaVersion: 1 as const,
      streamId: 'order-1',
      payload: { orderId: 'order-1' },
    };
    expect(
      (
        await saveAndRaise(
          repository,
          'order-1',
          NO_STATE,
          { status: 'confirmed' },
          context,
          fact,
          publish,
        )
      ).outcome,
    ).toBe('saved');
    expect(
      (
        await saveAndRaise(
          repository,
          'order-1',
          NO_STATE,
          { status: 'cancelled' },
          context,
          fact,
          publish,
        )
      ).outcome,
    ).toBe('version-conflict');
    expect(published).toEqual([{ ...fact, context }]);
  });
});
