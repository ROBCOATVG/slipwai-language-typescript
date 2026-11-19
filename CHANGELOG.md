# Changelog

No releases yet. Release notes are recorded here newest first, one entry per released version; the entry being
written is `changelog.d/`.

## 1.2.2 — PATCH

**CI proves this package against slipwai itself.** Its workflow installed the keel, called the shared release workflow and took the cloud target sources from `ROBCOATVG/slipwai`, a fork archived on 2026-10-17 and 244 commits behind `ROBCOATVG/slipwai`. All of them now come from `ROBCOATVG/slipwai`; where a commit is pinned, it is the same commit, which both repositories hold. Nothing the package does in a project changes.

## 1.2.1 — PATCH

**Every committed lock passes `npm audit`, so a generated project's gate does again.** `vitest` moves to 4.1.12,
`fastify` to 5.12.7 and the browser app's `vite` to 8.3.5, each past this week's advisories, and the typed
client's `openapi-typescript` to 7.13.0 — 6 reached `braces`, every version of which now has an advisory, and 7
does not depend on it. The generator calls the TypeScript compiler's JavaScript API, which the workspace's
TypeScript 7 does not have, so `packages/api-client` carries a TypeScript 5 of its own, nested beside it.
`scripts/regenerate-locks.py`, which the locks' comments always named, now exists: it moves every lock to the
pins and refuses to write one an audit still finds fault with.

**A browser app beside a service with no API passes its own gate.** With `--http none` the marked region took
the app's only route, leaving `Route` imported and unused and `Routes` empty, a blank line the formatter
refused in its test, and `vite.config.ts` using a `workers` it had cut the declaration of — so `make verify`
failed on lint, then format, then the type check. The shell now always has a catch-all route, the test's blank
line sits inside the region, and `workers` is declared outside it.

**Catch-up:** `slipwai language upgrade typescript`, then `slipwai migrate`; a project's locks and manifests
take the new pins, and `npm ci` installs them.

## 1.2.0 — MINOR

**A slice's story may be given its inputs, through the service's own seed door.** A service on the durable
store gains `scripts/seed.ts`, run by `make seed-<service> FILE=<json>`: it appends the events a slice's
`try-it.json` *gives* — the ones an unbuilt upstream slice would have written — through the event-store port,
at the stream's current version, as a system actor, with an identity hashed from stream, type and data so a
replay records nothing twice. With no `DATABASE_URL` it says so and exits 2. Never an HTTP route: the door
is a process with the store's credentials. slipwai's Try it runs it before a story's first step, and the
Demo rung's seed check runs it in the berth.

**Catch-up:** `slipwai language upgrade typescript`, then `slipwai migrate`; the service gains the script,
the `seed` npm script and the Makefile target. Until then a story's `given` is validated by `check-try` and
not applied, and Try it says *no seed door yet*.

**The service's test suite runs on its share of the machine's cores when slipwai's captain started the session.** Vitest starts a worker per core whatever else is running, so three slices testing at once on one machine asked for three machines: hr-test-2 at three berths on eighteen cores sat at a load of eighty, and a 20-second `make unit-service` took 280. `vitest.config.ts` now reads `SLIPWAI_TEST_WORKERS`, which the captain sets for every session it starts, into `maxWorkers`. Unset, as in a person's own run, vitest's default stands.

**The `react-vite` browser app ships in this package, because slipwai's keel no longer carries one.** Its files
moved from the keel's `assets/frontends/react-vite/` to this package's, beside the locks that already resolved
them, and `language.json` declares it in a `frontends` block — its label, capabilities, what each feature adds,
owns and depends on, the files carrying a marked region, and its styled baseline — which slipwai reads, and a
generated project's pruner reads too. Each variant tree is laid out like the app and every file carries the
same tokens, so a second frontend is a different tree rather than a change to the keel. A project generated
with it is byte for byte the project the keel generated before, apart from the pruner's own tables. CI also runs
conformance every night against the keel's `main`, so a keel change that breaks this package shows here first.

**Catch-up:** `slipwai language upgrade typescript` beside a keel with phase 17, then `slipwai migrate`; a
project's browser app is unchanged, and its `scripts/backing-services.py` gains the frontend's rows.

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

