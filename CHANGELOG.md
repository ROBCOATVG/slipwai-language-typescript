# Changelog

No releases yet. Release notes are recorded here newest first, one entry per released version; the entry being
written is `changelog.d/`.

## 1.1.0 — MINOR

**A state-stored TypeScript service is generated whole.** A service on the `state` rung (`write-model: state`)
used to get only `health.ts`: its Fastify server, its OpenAPI export, its configuration and tracing, and the
repository behind it were declared for the event-sourced rung only, while the Makefile it was generated with still
ran `check-openapi` against a `src/openapi.ts` that was never written — so `make verify` failed from the first
commit. The state rung now has its own rows: a versioned repository port with memory, SQLite and PostgreSQL
adapters, `save-state`, the shared optimistic-concurrency contract (proved against real PostgreSQL pools, exactly
one winner), the PostgreSQL migration, and the Fastify transport, OpenAPI export and identity wiring the event rung
already had. Non-JSON state and impossible calendar instants are refused before anything is written.

**Event context is mandatory.** On the event rung, raising an event and both append boundaries now require the
event's context; store metadata is preserved, and existing SQL attribution is read without new history.

**Fastify is pinned to 5.12.5 and source-map-js to 1.2.2**, both security fixes.

**Catch-up.** A state-stored TypeScript project generated with 1.0.0 is missing its service files, and
`slipwai replay` keeps only the features whose files are on disk — so a replay alone prunes its PostgreSQL blocks
as removed. Put one PostgreSQL file in place first (`apps/<service>/migrations/001_states.js` from this package's
`assets/backing-services/typescript/migrations/`), replay, remove it, then merge the replay. On the event rung, code
the project wrote that raises an event without its context stops compiling until it passes one. Requires a core
with the service write-model protocol (slipwai 2.x from the per-service rung onward).

## 1.0.0

**TypeScript is now a language package of its own.** The TypeScript backend that was built into slipwai — its
service skeleton on Node, npm workspaces, Biome, `tsc` and Vitest, its event-store adapters, its Fastify transport,
identity wiring, mutation gate and committed package locks — lives here, with the history it had there, and slipwai
loads it from its language directory (`$SLIPWAI_LANGUAGES`, or `~/.slipwai/languages`). The projects it generates
are byte for byte those slipwai generated with TypeScript built in. It answers `npm_workspace`, so its services
share the project's one npm workspace with core's browser app: this package carries their committed locks, the
workspace locks for a TypeScript service beside a browser app, and the Biome configuration the workspace runs. It
declares the catalog schema it loads on, `core >=9.0,<10`, in `language.json`.

