"""The TypeScript backend: each service's package, the npm workspace above them, and the committed lockfiles."""
from __future__ import annotations

import json
from pathlib import Path

from slipwai import registry as protocol
from slipwai.assets import asset_tree
from slipwai.project.backing_services import backing_service_service_files
from slipwai.project.composition import wire_store
from slipwai.project.flag_route import wire_entry
from slipwai.project.flags import flag_reader
from slipwai.project.openapi import published_document
from slipwai.project.shared_packages import WORKSPACE, workspace_manifest, workspace_scripts
from slipwai.selection import Selection
from slipwai.services import App
from slipwai.tooling import package_name

from . import typescript_deploy, typescript_layout, typescript_project, typescript_prune_rows, typescript_toolchain
from .typescript_workspace import WORKSPACE_ANSWER, service_lock

# This package's own assets, laid out as core's: `languages/typescript/…` and `backing-services/typescript/…`.
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def service_files(event: bool, selection: Selection, target: str = "none") -> dict[str, str]:
    """What this backend puts in a service's directory, keyed relative to it."""
    files = asset_tree(ASSETS / "languages/typescript/app")
    files.update({
        "package-lock.json": service_lock(selection).read_text(),
        # The two the selection decides the contents of, so they are written rather than copied.
        "tsconfig.json": typescript_config(selection),
        "vitest.config.ts": vitest_config(selection),
    })
    files.update(backing_service_service_files(selection, "typescript"))
    # The flag reader, only where there is somewhere to deploy: a flag is what makes a merge and a release
    # two decisions, and `--target none` has neither the mechanism nor the unsafe push. See `flags.py`.
    files.update(flag_reader(target, "typescript"))
    # And the entry point's half of it: the source is handed to `buildApp`, which is what puts `/api/flags`
    # in front of the browser app. Removed, not left unresolved, where there is no reader. See `flag_route`.
    wire_entry(files, target, "typescript")
    # And the store's half: which adapter this project opens, and what `/ready` is handed. See
    # `composition.py` — the entry point is the only place that may name the answer.
    wire_store(files, selection, "typescript")
    # The published contract, committed beside the service: which of the two shapes it takes is the same
    # condition that decides whether `/api/flags` is a route at all.
    files.update(published_document(selection, target, "typescript"))
    files["package.json"] = service_package_json(files["package.json"], selection)
    return files


# What a transport's dependencies force the compiler to overlook, keyed by feature and emitted inside that
# feature's marked region. Not a general loosening: `skipLibCheck` appears only with Fastify, because
# Fastify's logger reaches pino -> thread-stream, whose published types reference `TransferListItem` from
# `worker_threads` — a type @types/node has since removed. Nothing in a generated project can fix a
# dependency's own `.d.ts`, so the choice is between not typechecking types this project does not own and
# not offering the transport at all. Scoped to the selection that needs it and pruned with it.
COMPILER_ESCAPES = {
    "fastify": """    // backing-service:fastify:begin
    // Not a general loosening: see the note in the factory. Delete this line the day
    // thread-stream's types compile against @types/node again, and keep the strictness above.
    "skipLibCheck": true,
    // backing-service:fastify:end
""",
}


def typescript_config(selection: Selection) -> str:
    """The compiler settings, strict by default and loosened only where `COMPILER_ESCAPES` says a transport
    needs it — inside that transport's marked region, so a project that drops it gets its strictness back."""
    escape = COMPILER_ESCAPES.get(selection.feature_of("http") or "", "")
    return f"""{{
  "compilerOptions": {{
    "target": "ES2023",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noUnusedLocals": true,
    "noEmit": true,
{escape}    "types": ["node", "vitest/globals"]
  }},
  "include": ["src/**/*.ts", "tests/**/*.ts"]
}}
"""


def vitest_config(selection: Selection) -> str:
    """The default suite. Excluding `tests/integration/` is what keeps `make verify` free of Docker; the
    db-backed suite has its own config, which `make test-integration` names explicitly."""
    # Whichever answer brings a suite the Docker-free gate cannot run — the feature declares that in
    # `catalog.json`, and the excluded directory is the same one whatever service it needs.
    integration = selection.integration_feature
    exclusion = ""
    if integration is not None:
        exclusion = f"""    // backing-service:{integration}:begin
    // The db-backed suite lives in vitest.integration.config.ts and runs only from
    // `make test-integration`. Excluded here so `make verify` needs no Docker.
    exclude: ['**/node_modules/**', 'tests/integration/**'],
    // backing-service:{integration}:end
"""
    return f"""import {{ defineConfig }} from 'vitest/config';

export default defineConfig({{
  test: {{
    include: ['tests/**/*.test.ts'],
{exclusion}  }},
}});
"""


# What each feature adds to the service manifest, keyed by feature and applied in this order — the scripts
# object keeps its insertion order, so the order here is the order a generated package.json reads in.
#
# One table rather than a branch per feature, and kept in step with `package_edits` in the family's
# `typescript_prune_rows.py`, which the pruner reads to remove exactly these again; the
# factory's test suite asserts the two agree.
PACKAGE_ADDITIONS: dict[str, dict[str, dict[str, str]]] = {
    "postgres": {
        # `node-pg-migrate` is a runtime dependency rather than a development one because `make migrate`
        # is also what the production image runs as a one-off task, and a buildpack prunes devDependencies
        # from the image it launches.
        "dependencies": {"node-pg-migrate": "9.0.0", "pg": "8.23.0"},
        "devDependencies": {"@types/pg": "8.21.0"},
        "scripts": {
            "migrate": "node-pg-migrate up -m migrations",
            "migrate:down": "node-pg-migrate down -m migrations",
            "test:integration": "vitest run --config vitest.integration.config.ts",
        },
    },
    "fastify": {
        # The transport, and the schema library its routes, its responses, its published document and its
        # environment are all declared with. One library rather than four decisions: TypeBox is what
        # Fastify's own type provider reads, so a schema produces the validator, the serialiser, the
        # OpenAPI document and the handler's types from one declaration and none of them can disagree.
        # Beside them, the telemetry the transport is the only thing that can produce: one span per
        # request, continuing whatever `traceparent` arrived. The API and the SDK are separate packages
        # by OpenTelemetry's own design — the API is what code calls, the SDK what a process installs —
        # and the OTLP exporter is a third, because `src/tracing.ts` only constructs one when an endpoint
        # was named. None of them are optional here: a transport with no trace id has nothing to tie a
        # log line, an incoming header and an event's correlation id together.
        "dependencies": {
            # The two the edge is exposed through rather than by: what a browser is allowed to ask for
            # (CORS) and what it is told to enforce (helmet). Both are specifications with edge cases —
            # a preflight, a `Vary: Origin` — and a hand-written pair is a second implementation of one.
            "@fastify/cors": "11.3.0",
            "@fastify/env": "7.0.0",
            "@fastify/helmet": "13.1.1",
            "@fastify/otel": "0.21.0",
            "@fastify/swagger": "9.8.1",
            "@fastify/type-provider-typebox": "6.1.0",
            "@opentelemetry/api": "1.9.1",
            "@opentelemetry/exporter-trace-otlp-http": "0.222.0",
            "@opentelemetry/resources": "2.11.0",
            "@opentelemetry/sdk-trace-node": "2.11.0",
            "@opentelemetry/semantic-conventions": "1.43.0",
            "@sinclair/typebox": "0.34.52",
            "fastify": "5.7.1",
        },
        "devDependencies": {},
        # `--noEmit false --rootDir .` overrides the typecheck-only tsconfig for this one command: TypeScript
        # 7 refuses to emit without an explicit rootDir, and the project's own `src` + `tests` inputs make
        # the repository root the only correct one. Compiling before running means `make dev` cannot start a
        # service that does not typecheck, which is a cheaper way to learn it than a stack trace.
        # `build` and `start` are the same two halves, apart: `make build` runs `build` once before packing
        # the image, and `start` is what the compiled entry point is — so the image and `make dev` cannot
        # disagree about how this service starts.
        # `openapi` compiles the same way `build` does and then runs the exporter, so the document is
        # written by the very code the process runs rather than by a second description of it.
        "scripts": {
            "dev": (
                "tsc --noEmit false --outDir .build --rootDir . && "
                "LOG_FORMAT=pretty node .build/src/main.js"
            ),
            "build": "tsc --noEmit false --outDir .build --rootDir .",
            "start": "node .build/src/main.js",
            "openapi": "tsc --noEmit false --outDir .build --rootDir . && node .build/src/openapi.js",
        },
    },
}


def service_package_json(source: str, selection: Selection) -> str:
    """Add only the dependencies and scripts the selection actually needs, from `PACKAGE_ADDITIONS`."""
    package = json.loads(source)
    dependencies = dict(package.get("dependencies", {}))
    development = dict(package["devDependencies"])
    scripts = dict(package["scripts"])
    for feature, additions in PACKAGE_ADDITIONS.items():
        if not selection.has(feature):
            continue
        dependencies.update(additions["dependencies"])
        development.update(additions["devDependencies"])
        scripts.update(additions["scripts"])
    if dependencies:
        package["dependencies"] = dict(sorted(dependencies.items()))
    package["devDependencies"] = dict(sorted(development.items()))
    package["scripts"] = scripts
    return json.dumps(package, indent=2) + "\n"


# What the published API document calls this service, carried in `http-app.ts` as a token for the reason
# `__TRANSPORT__` and `__APP_SERVICES__` are: the file it sits in is TypeScript, and a document has to name
# the service rather than the template it came from. Resolved below, where the project's name is known.
SERVICE_NAME = "__SERVICE_NAME__"
HTTP_APP = "src/adapters/driving/http/app.ts"
CONFIG = "src/config.ts"
DOCUMENT = "openapi.json"


def name_service(project_name: str, service: App, files: dict[str, str]) -> dict[str, str]:
    """One service's package under this project's own name, and its API document under the same name."""
    manifest = f"{service.path}/package.json"
    package = json.loads(files[manifest])
    package["name"] = package_name(project_name, service)
    files[manifest] = json.dumps(package, indent=2) + "\n"
    # Only where there is a transport: a project answering `--http none` has no app to publish.
    # The document's title and the name this service's spans carry are the same fact, so the token is
    # resolved wherever it appears rather than in the one file that had it first.
    for relative in (HTTP_APP, CONFIG, DOCUMENT):
        path = f"{service.path}/{relative}"
        if path in files:
            files[path] = files[path].replace(SERVICE_NAME, package["name"])
    return files


def repository_files(
    project_name: str, files: dict[str, str], services: list[App], verify: str
) -> dict[str, str]:
    """The npm workspace above the Node services: its manifest, its lockfile, and this family's verify script.

    The committed lockfile is rewritten rather than regenerated: `npm ci` refuses a lock that disagrees
    with its manifest, and the one in `assets/` was resolved under the template's name. Each service
    contributes its own workspace record and link, and the hoisted dependency records its own lock has that
    the first's did not — every variant pins the same versions, so the union is the tree npm would hoist.
    The workspaces are named rather than globbed, because a service in another language under `apps/` is
    not an npm package and `apps/*` would send npm looking for a manifest it does not have.
    """
    lock: dict = {}
    records: dict[str, dict] = {}
    for service in services:
        service_lock = json.loads(files.pop(f"{service.path}/package-lock.json"))
        service_record = service_lock["packages"].pop("")
        service_record["name"] = package_name(project_name, service)
        records[service.path] = service_record
        service_lock["packages"][f"node_modules/{package_name(project_name, service)}"] = {
            "resolved": service.path,
            "link": True,
        }
        if not lock:
            lock = service_lock
        else:
            for key, value in service_lock["packages"].items():
                lock["packages"].setdefault(key, value)
    lock["name"] = project_name
    workspaces = [*(service.path for service in services), WORKSPACE]
    root_record = {
        "name": project_name,
        "version": "0.1.0",
        "workspaces": workspaces,
    }
    lock["packages"] = {
        "": root_record,
        **records,
        **dict(sorted(lock["packages"].items())),
    }
    files["package.json"] = workspace_manifest(project_name, workspaces, workspace_scripts(services))
    files["package-lock.json"] = json.dumps(lock, indent=2) + "\n"
    verify_lines = "".join(f"npm --workspace {service.path} run verify\n" for service in services)
    files[verify] = f"""#!/bin/sh
set -eu
if [ ! -d node_modules ]; then npm ci; fi
{verify_lines}"""
    return files


LANGUAGE = protocol.Language(
    (protocol.Family("typescript", typescript_toolchain.FAMILY | typescript_deploy.FAMILY | typescript_layout.FAMILY_ANSWERS | typescript_project.FAMILY_ANSWERS | {protocol.PRUNE_ROWS: typescript_prune_rows.PRUNE_ROWS, protocol.NPM_WORKSPACE: WORKSPACE_ANSWER}),),
    (protocol.Backend("typescript", "typescript", typescript_toolchain.BACKEND | typescript_deploy.BACKEND | {
        protocol.SERVICE_FILES: service_files,
        protocol.NAME_SERVICE: name_service,
        protocol.REPOSITORY_FILES: repository_files,
        protocol.READY_PATH: "/ready",
        protocol.HEALTH_BODY: '{"status":"ok"}',
        **typescript_layout.ANSWERS, **typescript_project.ANSWERS,
    }),))
