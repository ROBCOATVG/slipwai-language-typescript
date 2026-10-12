"""The state rung's source files and composition, selected by the actual service answer.

The protocol's EntryStore describes the existing event composition. A state service composes its own
repository here, without teaching the keel which TypeScript adapter that means.
"""
from __future__ import annotations

from pathlib import Path

from slipwai.assets import source_text
from slipwai.selection import Selection

ASSETS = Path(__file__).resolve().parents[1] / "assets"

BASE = {
    "src/application/ports/repository.ts": "repository.ts",
    "src/application/ports/event-context.ts": "event-context.ts",
    "src/application/save-state.ts": "save-state.ts",
    "src/adapters/driven/repository-memory.ts": "repository-memory.ts",
    "tests/contract/repository-contract.ts": "tests/repository-contract.ts",
    "tests/contract/repository-memory.test.ts": "tests/repository-memory.test.ts",
    "tests/contract/save-state.test.ts": "tests/save-state.test.ts",
    "tests/contract/event-context.test.ts": "tests/event-context.test.ts",
}

STATE_WRITE = {
    "memory": BASE,
    "sqlite": {
        "src/adapters/driven/repository-sqlite.ts": "repository-sqlite.ts",
        "tests/contract/repository-sqlite.test.ts": "tests/repository-sqlite.test.ts",
    },
    "postgres": {
        "src/adapters/driven/repository-postgres/index.ts": "repository-postgres.ts",
        "tests/integration/repository-postgres.test.ts": "tests/repository-postgres.test.ts",
        "vitest.integration.config.ts": "vitest.integration.config.ts",
        "migrations/001_states.js": "migrations/001_states.js",
    },
}

MEMORY_IMPORT = "import { createInMemoryRepository } from './adapters/driven/repository-memory.js';\n"
APP_IMPORT = "import { buildApp, readiness } from './adapters/driving/http/app.js';\n"
PORT_IMPORT = ("import type { Repository } from './application/ports/repository.js';\n"
               "import type { Config } from './config.js';\n")
STATE_IMPORT = {
    "memory": MEMORY_IMPORT + APP_IMPORT,
    "sqlite": MEMORY_IMPORT + "// backing-service:sqlite:begin\n"
        "import { openSqliteRepository } from './adapters/driven/repository-sqlite.js';\n"
        "// backing-service:sqlite:end\n" + APP_IMPORT + PORT_IMPORT,
    "postgres": "// backing-service:postgres:begin\nimport { Pool } from 'pg';\n"
        "// backing-service:postgres:end\n" + MEMORY_IMPORT
        + "// backing-service:postgres:begin\n"
        "import { createPostgresRepository } from './adapters/driven/repository-postgres/index.js';\n"
        "// backing-service:postgres:end\n" + APP_IMPORT + PORT_IMPORT,
}
STATE_OPEN = {
    "memory": "function openRepository() {\n  return createInMemoryRepository();\n}\n",
    "sqlite": "function openRepository(_config: Config): Repository {\n"
        "  // backing-service:sqlite:begin\n"
        "  if (_config.EVENT_STORE_PATH !== undefined) {\n"
        "    return openSqliteRepository(_config.EVENT_STORE_PATH);\n  }\n"
        "  // backing-service:sqlite:end\n  return createInMemoryRepository();\n}\n",
    "postgres": "function openRepository(_config: Config): Repository {\n"
        "  // backing-service:postgres:begin\n"
        "  if (_config.DATABASE_URL !== undefined) {\n"
        "    const pool = new Pool({ connectionString: _config.DATABASE_URL });\n"
        "    pool.on('error', (failure) => process.stderr.write(`${String(failure)}\\n`));\n"
        "    return createPostgresRepository(pool);\n  }\n"
        "  // backing-service:postgres:end\n  return createInMemoryRepository();\n}\n",
}



def state_files(files: dict[str, str], selection: Selection) -> None:
    """Always give standard/state a memory baseline; its profile never asks the persistence axis."""
    for destination, source in BASE.items():
        files[destination] = source_text(ASSETS, f"backing-services/typescript/{source}", ASSETS.parent)
    entry = "src/main.ts"
    if entry not in files:
        return
    store = selection.option("persistence")
    content = files[entry]
    content = content.replace("__STORE_IMPORT__\n", STATE_IMPORT[store])
    content = content.replace("__STORE_OPEN__\n", STATE_OPEN[store])
    content = content.replace("__STORE_ARGUMENT__", "openRepository")
    content = content.replace("event store", "state repository")
    files[entry] = content
