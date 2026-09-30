"""TypeScript's service-layout answers: which committed asset lands where under a service, per feature.

The other half of `typescript.py`'s `LANGUAGE`, apart for the reason the tables it came from were apart from
`backing_services.py`: most of the bytes and none of the behaviour, and `typescript.py` has no room left under the line
budget. `ANSWERS` is this backend's, keyed by the member constants, and `LANGUAGE` takes it whole.

Sources are relative to `assets/backing-services/typescript/`, and a `../` reaches the material shared between
backends. Core merges the two sides feature by feature (`backing_services.service_layout`).
"""
from __future__ import annotations

from typing import Any

from ... import registry as protocol
from ..entry_stores import EntryStore, marked
from ..flag_route import EntryWiring
from ..flags import FlagReader

# The write side: the event port, the adapters behind it, their contract suites and the migrations, and each
# transport's and identity provider's own files.
WRITE_SIDE: dict[str, dict[str, str]] = {
    "memory": {
        "src/application/ports/events.ts": "events.ts",
        "src/adapters/driven/event-store-memory.ts": "event-store-memory.ts",
        "tests/contract/event-store-contract.ts": "tests/event-store-contract.ts",
        "tests/contract/event-store-memory.test.ts": "tests/event-store-memory.test.ts",
    },
    "sqlite": {
        "src/adapters/driven/event-store-sqlite.ts": "event-store-sqlite.ts",
        "tests/contract/event-store-sqlite.test.ts": "tests/event-store-sqlite.test.ts",
    },
    "postgres": {
        "src/adapters/driven/event-store-postgres/index.ts": "event-store-postgres.ts",
        "tests/integration/event-store-postgres.test.ts": "tests/event-store-postgres.test.ts",
        "vitest.integration.config.ts": "vitest.integration.config.ts",
        "migrations/001_events.js": "migrations/001_events.js",
        "migrations/002_events_append_only.js": "migrations/002_events_append_only.js",
    },
    "fastify": {
        "src/adapters/driving/http/app.ts": "http-app.ts",
        # The environment's one schema. Under the transport rather than beside the store because
        # `@fastify/env` is what checks it and the app is what carries the result: a project with
        # `--http none` has no process of its own to configure.
        "src/config.ts": "config.ts",
        # The SDK's wiring, under the transport for the same reason: a span per request is the one
        # thing only a transport can produce, and a project with `--http none` has no request to
        # open one for.
        "src/tracing.ts": "tracing.ts",
        "src/main.ts": "main.ts",
        # The published document, written from the app rather than beside it. A second entry point,
        # because it builds the app exactly as `main.ts` does and then binds nothing at all.
        "src/openapi.ts": "openapi-export.ts",
        "tests/edge/http-app.test.ts": "tests/http-app.test.ts",
        "tests/edge/tracing.test.ts": "tests/tracing.test.ts",
    },
    "keycloak": {
        "src/adapters/driving/http/auth/oidc-keycloak.ts": "oidc-keycloak.ts",
        "tests/auth/oidc-keycloak.test.ts": "tests/oidc-keycloak.test.ts",
    },
    "users-keycloak": {
        "src/adapters/driving/http/users/oidc-keycloak.ts": "users-oidc-keycloak.ts",
        "tests/users/oidc-keycloak.test.ts": "tests/users-oidc-keycloak.test.ts",
    },
}

# The read side: the checkpoint port and its adapters, the catch-up runner, and the migrations that create the
# checkpoint table and the tag index. Every backend covers the same ground (`docs/backend-obligations.md` §3).
READ_SIDE: dict[str, dict[str, str]] = {
    "memory": {
        # The timer that drives an async projection: a Fastify plugin, so the framework starts it
        # and `onClose` stops it. Beside the read side rather than under `adapters/driving/`, and
        # its host typed structurally rather than imported, for one reason: this ships with the
        # event store, and a project can have a store and no HTTP adapter at all — where an
        # import of `fastify` would not compile and everything under `adapters/driving/` is gone
        # with the transport that owned it.
        "src/projections-plugin.ts": "projections-plugin.ts",
        "tests/contract/projections-plugin.test.ts": "tests/projections-plugin.test.ts",
        "src/application/ports/read-models.ts": "read-models.ts",
        "src/projections.ts": "projections.ts",
        "src/adapters/driven/checkpoint-store-memory.ts": "checkpoint-store-memory.ts",
        "tests/contract/checkpoint-store-contract.ts": "tests/checkpoint-store-contract.ts",
        "tests/contract/checkpoint-store-memory.test.ts": "tests/checkpoint-store-memory.test.ts",
        # The runner has no I/O of its own, so its suite runs whatever the store is — which is why
        # it is here under the feature every project has rather than beside an adapter.
        "tests/contract/projections.test.ts": "tests/projections.test.ts",
    },
    "sqlite": {
        "src/adapters/driven/checkpoint-store-sqlite.ts": "checkpoint-store-sqlite.ts",
        "tests/contract/checkpoint-store-sqlite.test.ts": "tests/checkpoint-store-sqlite.test.ts",
    },
    "postgres": {
        # Beside the event store's own `index.ts`, because it is built from it and pruned with it.
        "src/adapters/driven/event-store-postgres/checkpoint-store-postgres.ts": "checkpoint-store-postgres.ts",
        "tests/integration/checkpoint-store-postgres.test.ts": "tests/checkpoint-store-postgres.test.ts",
        "migrations/003_projection_checkpoints.js": "migrations/003_projection_checkpoints.js",
        "migrations/004_event_tags.js": "migrations/004_event_tags.js",
    },
}

# Where this backend's feature-flag reader is committed, where it lands in a service, and how a slice asks
# it. Emitted only under a managed target (`flags.flag_reader`).
READER = FlagReader(
    tree="typescript/flags",
    source="src/flags.ts",
    tests="tests/flags.test.ts",
    call="flagEnabled('checkout-v2')",
)

# How the flag source is wired into this backend's entry point, keyed by the HTTP option whose app takes it
# (`flag_route.wire_entry`). No `flag_resource`: this backend's transports are handed the source, and
# discover no route.
WIRING = {
    "fastify": EntryWiring(
        entry="src/main.ts",
        line="import { defaultSource } from './flags.js';",
        argument=", defaultSource()",
    ),
}

# What this backend's entry point writes for each event-store answer: `entry_stores.py` says what the fields
# mean, and `composition.wire_store`, which reads it, the three rules every string here follows.
TYPESCRIPT_MEMORY_IMPORT = (
    "import { createInMemoryEventStore } from './adapters/driven/event-store-memory.js';\n"
)
# Beside the store imports because Biome sorts the whole block, and its path falls between adapter and port.
TYPESCRIPT_APP_IMPORT = "import { buildApp, readiness } from './adapters/driving/http/app.js';\n"
TYPESCRIPT_PORT_IMPORT = (
    "import type { EventStore } from './application/ports/events.js';\nimport type { Config } from './config.js';\n"
)
TYPESCRIPT_OPEN_HEAD = """// The event store this project answered the event-store question with, opened once and handed to
// whatever needs it. Nothing else in this service constructs one.
//
// It takes the checked environment rather than reading `process.env`: `@fastify/env` populates
// `app.config` while the app boots, so `readiness` calls this once from inside `after`, which is where
// that exists — and `src/config.ts` stays the one place this service's variables are checked.
//
// The marked block is the answer; delete it — which is what `./init --event-store memory` does — and the
// in-memory store below is what is left. Both states are valid at once, which is what a prune needs,
// because pruning only ever subtracts.
function openEventStore(config: Config): EventStore {
  let store: EventStore | undefined;
"""
TYPESCRIPT_OR_MEMORY = """  store ??= createInMemoryEventStore();
  return store;
}
"""

STORE = EntryStore(
    entry="src/main.ts",
    imports={
        # No event-store axis, and the adapter import still has to land: without this row `tsc` saw
        # neither `buildApp` nor `readiness`.
        "none": TYPESCRIPT_APP_IMPORT,
        None: TYPESCRIPT_MEMORY_IMPORT + TYPESCRIPT_APP_IMPORT,
        "sqlite": TYPESCRIPT_MEMORY_IMPORT
        + marked(
            "import { openSqliteEventStore } from './adapters/driven/event-store-sqlite.js';",
        )
        + TYPESCRIPT_APP_IMPORT
        + TYPESCRIPT_PORT_IMPORT,
        "postgres": marked("import { Pool } from 'pg';")
        + TYPESCRIPT_MEMORY_IMPORT
        + marked(
            "import { createPostgresEventStore } from "
            "'./adapters/driven/event-store-postgres/index.js';",
        )
        + TYPESCRIPT_APP_IMPORT
        + TYPESCRIPT_PORT_IMPORT,
    },
    open={
        None: (
            "// The event store this project answered the event-store question with, opened once and\n"
            "// handed to whatever needs it. Nothing else in this service constructs one — and it is\n"
            "// `readiness` that calls this, once, as the app boots.\n"
            "function openEventStore() {\n"
            "  return createInMemoryEventStore();\n"
            "}\n"
        ),
        "sqlite": TYPESCRIPT_OPEN_HEAD
        + marked(
            "  store = openSqliteEventStore(config.EVENT_STORE_PATH);",
            indent="  ",
        )
        + TYPESCRIPT_OR_MEMORY,
        "postgres": TYPESCRIPT_OPEN_HEAD
        + marked(
            "  // `pg` connects lazily, so this opens no socket while the app is booting: an\n"
            "  // unreachable database shows up as `/ready` answering 503, which is what it is.\n"
            "  const pool = new Pool({ connectionString: config.DATABASE_URL });\n"
            "  // A pool emits `error` when an *idle* client's connection dies — the database\n"
            "  // restarted, a failover, somebody stopped the container. That is an EventEmitter\n"
            "  // error, so leaving it unhandled takes this process down with it, and a service that\n"
            "  // dies when its database blinks is one a platform crash-loops instead of taking out\n"
            "  // of the pool for a moment. The pool discards that client and opens another by\n"
            "  // itself; all this owes is somewhere to say so, and `/ready` reports the rest.\n"
            "  pool.on('error', (failure) => {\n"
            "    const line = { level: 50, msg: 'the event store connection failed', "
            "err: String(failure) };\n"
            "    process.stderr.write(`${JSON.stringify(line)}\\n`);\n"
            "  });\n"
            "  store = createPostgresEventStore(pool);",
            indent="  ",
        )
        + TYPESCRIPT_OR_MEMORY,
    },
    argument="openEventStore",
)


# What "code shared between services" is in this family, and what sharing it would ask of the build: the
# architecture page's paragraph. The family's answer rather than a backend's, because the unit of sharing is
# the build tool's rather than the framework's.
SHARED = (
    "an npm workspace package under `packages/<name>`, which the root `package.json` already lists in "
    "`workspaces`; a deployable depends on it by name like any other package, and one `npm ci` installs "
    "everything. A package that compiles — one that emits the declarations its consumers import — says so "
    "with a `build` script in its own `package.json`, and `make build-packages` then builds it. Nothing "
    "else has to be done for that: `build-packages` is already a prerequisite of every target that "
    "compiles or runs this project's TypeScript code, because a package's `dist/` is not committed "
    "and a target that forgot it would pass here and fail on a fresh checkout. Only that code: a "
    "native service's own targets run in CI inside an image with no node in it"
)

ANSWERS: dict[protocol.Member[Any], object] = {
    protocol.WRITE_SIDE_FILES: WRITE_SIDE,
    protocol.READ_SIDE_FILES: READ_SIDE,
    protocol.FLAG_READER: READER,
    protocol.ENTRY_WIRING: WIRING,
    protocol.FLAG_RESOURCE: {},
    protocol.ENTRY_STORE: STORE,
}

# The family's own: `shared_code` is read by family name (`guidance.architecture`).
FAMILY_ANSWERS: dict[protocol.Member[Any], object] = {protocol.SHARED_CODE: SHARED}
