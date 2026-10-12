import { describe, expect, it } from 'vitest';
import type { EventContext } from '../../src/application/ports/event-context.js';
import {
  createCorrelationId,
  createEventContext,
  delegatedContext,
  raise,
} from '../../src/application/ports/event-context.js';

const context = createEventContext({
  actor_id: 'systems/cron',
  occurred_at: '2024-01-01T00:00:00.000Z',
  correlation_id: createCorrelationId('00000000-0000-0000-0000-000000000001'),
  causation_id: null,
});
const fact = {
  type: 'HoldExpired',
  schemaVersion: 1 as const,
  streamId: 'hold-1',
  payload: { holdId: 'hold-1' },
};
describe('typed event context', () => {
  it('keeps attribution separate from payload ownership', () => {
    expect(raise(context, fact)).toEqual({ ...fact, context });
    expect(raise(context, fact).payload).not.toHaveProperty('actor_id');
  });
  it('rejects impossible calendar instants before a fact can be raised', () => {
    for (const occurred_at of [
      '2026-02-30T12:00:00Z',
      '2025-02-29T12:00:00Z',
      '2026-01-01T24:00:00Z',
      '0000-01-01T00:00:00Z',
    ]) {
      expect(() => raise({ ...context, occurred_at }, fact)).toThrow('ISO instant');
    }
    expect(
      raise({ ...context, occurred_at: '2024-02-29T12:00:00+05:30' }, fact).context.occurred_at,
    ).toBe('2024-02-29T12:00:00+05:30');
  });
  it('records delegated identity explicitly', () => {
    expect(delegatedContext({ ...context, on_behalf_of: 'customer-1' }).on_behalf_of).toBe(
      'customer-1',
    );
  });
  it('refuses missing context or causal fields at runtime too', () => {
    expect(() => raise(undefined as unknown as EventContext, fact)).toThrow('actor_id');
    expect(() =>
      createEventContext({ ...context, causation_id: undefined } as unknown as EventContext),
    ).toThrow('causation_id');
  });
});
// Compile-only checks: the raise boundary and a delegated actor cannot accept a bare payload.
const compileOnly = () => {
  // @ts-expect-error a fact without its context cannot be raised
  raise(fact);
  // @ts-expect-error delegation names the subject it acts for
  delegatedContext(context);
};
void compileOnly;
