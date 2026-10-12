/** Event attribution and causal time, separate from the business payload and store metadata.
 * actor_id identifies who acted, never who owns a resource. Payloads reference PII by id.
 */
export type CorrelationId = string & { readonly __brand: 'CorrelationId' };
export type CausationId = string & { readonly __brand: 'CausationId' };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function uuid(raw: string, kind: string): string {
  if (!UUID.test(raw)) throw new Error(`a ${kind} must be a UUID`);
  return raw.toLowerCase();
}

export const createCorrelationId = (raw: string): CorrelationId =>
  uuid(raw, 'correlation id') as CorrelationId; // checked before branding
export const createCausationId = (raw: string): CausationId =>
  uuid(raw, 'causation id') as CausationId; // checked before branding

export type EventContext = Readonly<{
  actor_id: string;
  on_behalf_of?: string;
  occurred_at: string;
  correlation_id: CorrelationId;
  /** Explicit null for the first event; absence is not a causal decision. */
  causation_id: CausationId | null;
}>;

/** Reject calendar rollover before memory or SQL accepts a fact. Offsets stay within ISO's range. */
function isIsoInstant(raw: string): boolean {
  const match =
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|([+-])(\d{2}):(\d{2}))$/.exec(
      raw,
    );
  if (match === null) return false;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > (days[month - 1] ?? 0)) return false;
  if (Number(match[4]) > 23 || Number(match[5]) > 59 || Number(match[6]) > 59) return false;
  if (match[7] !== undefined) {
    const hours = Number(match[8]);
    const minutes = Number(match[9]);
    if (hours > 14 || minutes > 59 || (hours === 14 && minutes !== 0)) return false;
  }
  return Number.isFinite(Date.parse(raw));
}

export function assertEventContext(context: EventContext): void {
  if (
    context === undefined ||
    context === null ||
    typeof context.actor_id !== 'string' ||
    context.actor_id.trim() === ''
  )
    throw new Error('event context requires actor_id');
  if (typeof context.occurred_at !== 'string' || !isIsoInstant(context.occurred_at)) {
    throw new Error('event context requires occurred_at as an ISO instant');
  }
  if (typeof context.correlation_id !== 'string' || !UUID.test(context.correlation_id)) {
    throw new Error('event context requires correlation_id as a UUID');
  }
  if (
    context.causation_id !== null &&
    (typeof context.causation_id !== 'string' || !UUID.test(context.causation_id))
  ) {
    throw new Error('event context requires causation_id as a UUID or explicit null');
  }
  if (
    context.on_behalf_of !== undefined &&
    (typeof context.on_behalf_of !== 'string' || context.on_behalf_of.trim() === '')
  ) {
    throw new Error('delegated event context requires on_behalf_of');
  }
}

export function createEventContext(input: EventContext): EventContext {
  assertEventContext(input);
  return Object.freeze({
    ...input,
    correlation_id: createCorrelationId(input.correlation_id),
    causation_id: input.causation_id === null ? null : createCausationId(input.causation_id),
  });
}

/** A delegated caller cannot omit whom it acts for. System work uses e.g. systems/cron. */
export function delegatedContext(input: EventContext & { on_behalf_of: string }): EventContext {
  return createEventContext(input);
}

export type EventBody = Readonly<{
  type: string;
  schemaVersion: 1;
  streamId: string;
  payload: Readonly<Record<string, unknown>>;
}>;
export type RaisedEvent = EventBody & Readonly<{ context: EventContext }>;

/** The state rung raises facts from now on; this constructs an envelope, never historical events. */
export function raise(context: EventContext, body: EventBody): RaisedEvent {
  return Object.freeze({
    ...body,
    payload: Object.freeze({ ...body.payload }),
    context: createEventContext(context),
  });
}

/** Keep the existing SQL actor column readable by old store readers, including optional delegation. */
export function storedActor(context: EventContext): Readonly<Record<string, string>> {
  return {
    kind: context.actor_id.startsWith('systems/') ? 'system' : 'subject',
    id: context.actor_id,
    ...(context.on_behalf_of === undefined ? {} : { on_behalf_of: context.on_behalf_of }),
  };
}

/** Existing rows already recorded every causal field; derive context from those facts, not new history. */
export function storedContext(
  actor: unknown,
  occurred_at: string,
  correlation_id: string,
  causation_id: string | null,
): EventContext {
  if (
    typeof actor !== 'object' ||
    actor === null ||
    !('id' in actor) ||
    typeof actor.id !== 'string'
  ) {
    throw new Error('stored event has no usable actor_id');
  }
  const delegated = 'on_behalf_of' in actor ? actor.on_behalf_of : undefined;
  if (delegated !== undefined && typeof delegated !== 'string')
    throw new Error('stored delegation is invalid');
  return createEventContext({
    actor_id: actor.id,
    occurred_at,
    correlation_id: createCorrelationId(correlation_id),
    causation_id: causation_id === null ? null : createCausationId(causation_id),
    ...(delegated === undefined ? {} : { on_behalf_of: delegated }),
  });
}
