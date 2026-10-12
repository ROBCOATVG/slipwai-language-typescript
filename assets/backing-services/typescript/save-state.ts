import type { EventBody, EventContext, RaisedEvent } from './ports/event-context.js';
import { raise } from './ports/event-context.js';
import type { Repository, SaveResult, State } from './ports/repository.js';

/** A use case decides against a loaded version, saves it, then raises a fact only if that save won.
 * This is in-process delivery, not a durable outbox: a cross-service reader needs the project's publisher.
 */
export async function saveAndRaise<T extends State>(
  repository: Repository<T>,
  id: string,
  expectedVersion: number,
  state: T,
  context: EventContext,
  fact: EventBody,
  publish: (event: RaisedEvent) => Promise<void>,
): Promise<SaveResult> {
  // Validate attribution before writing; a malformed envelope must not leave an unrecordable state.
  const event = raise(context, fact);
  const result = await repository.save(id, expectedVersion, state);
  if (result.outcome === 'saved') await publish(event);
  return result;
}
