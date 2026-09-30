"""The TypeScript family's rows for the generated pruning script (`prune_rows`, S06).

Written into a project's `scripts/backing-services.py` when it has a TypeScript service, and read by the
factory's own pruner. The shape is fixed in `specs/001-slipwai-2-language-addons/contracts/backend-protocol.md`.
"""
from __future__ import annotations

PRUNE_ROWS = {
    # The environment's one schema holds each backing service's variables inside that service's region, and the
    # entry point is the composition root, the one file that names the store this project answered with.
    "marked_files": ("vitest.config.ts", "tsconfig.json", "src/config.ts", "src/main.ts"),
    "owned_files": {
        "sqlite": (
            "src/adapters/driven/event-store-sqlite.ts",
            "src/adapters/driven/checkpoint-store-sqlite.ts",
            "tests/contract/event-store-sqlite.test.ts",
            "tests/contract/checkpoint-store-sqlite.test.ts",
        ),
        "postgres": (
            "src/adapters/driven/event-store-postgres/index.ts",
            "src/adapters/driven/event-store-postgres/checkpoint-store-postgres.ts",
            "migrations/001_events.js",
            "migrations/002_events_append_only.js",
            "migrations/003_projection_checkpoints.js",
            "migrations/004_event_tags.js",
            "tests/integration/event-store-postgres.test.ts",
            "tests/integration/checkpoint-store-postgres.test.ts",
            "vitest.integration.config.ts",
        ),
        "fastify": (
            "src/adapters/driving/http/app.ts",
            "src/config.ts",
            "src/tracing.ts",
            "src/main.ts",
            "src/openapi.ts",
            "openapi.json",
            "tests/edge/http-app.test.ts",
            "tests/edge/tracing.test.ts",
        ),
        "keycloak": ("src/adapters/driving/http/auth/oidc-keycloak.ts", "tests/auth/oidc-keycloak.test.ts"),
        "users-keycloak": ("src/adapters/driving/http/users/oidc-keycloak.ts", "tests/users/oidc-keycloak.test.ts"),
    },
    # Removed with `npm uninstall` rather than by editing package.json, because package.json and
    # package-lock.json have to move together: a hand-edited manifest leaves `npm ci` refusing to install.
    "package_edits": {
        "postgres": {
            "packages": ("pg", "@types/pg", "node-pg-migrate"),
            "scripts": ("migrate", "migrate:down", "test:integration"),
        },
        # The transport and the schema library it declares its routes and its environment with: they arrive
        # together and they go together, because nothing else in the service imports either.
        "fastify": {
            "packages": (
                "@fastify/cors",
                "@fastify/env",
                "@fastify/helmet",
                "@fastify/otel",
                "@fastify/swagger",
                "@fastify/type-provider-typebox",
                "@opentelemetry/api",
                "@opentelemetry/exporter-trace-otlp-http",
                "@opentelemetry/resources",
                "@opentelemetry/sdk-trace-node",
                "@opentelemetry/semantic-conventions",
                "@sinclair/typebox",
                "fastify",
            ),
            "scripts": ("dev", "build", "start", "openapi"),
        },
    },
    "manifest": "package.json",
}
