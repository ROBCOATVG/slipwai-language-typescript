"""The TypeScript backend's answers about the project around its services: what git ignores, what an agent may
run, what the gate is called, where the event model's code lives, and what `make mutation` uses.

Moved here from core's per-backend tables (S05), keyed by the protocol's member constants. `typescript.py` is at
its line budget, which is why these sit beside it."""
from __future__ import annotations

from typing import Any

from ... import registry as protocol
from ..renovate import RenovateRules

# `.nvmrc`, Renovate's npm group and the Node manager follow the npm workspace, which a browser app has too, so they
# are core's (`pins.py`, `renovate.py`) and this family asks for nothing of its own.
FAMILY_ANSWERS: dict[protocol.Member[Any], object] = {
    protocol.PIN_FILES: {},
    protocol.MAKEFILE_VARIABLES: None,
    protocol.RENOVATE_RULES: RenovateRules((), None, None),
}
ANSWERS: dict[protocol.Member[Any], object] = {
    protocol.PROCFILE: None,
    # The reader re-reads AppConfig (AWS) and App Configuration (Azure) live: the one backend with a reader for
    # either cloud's opt-in transport (`flag_route.flag_transports`).
    protocol.OPT_IN_FLAG_TRANSPORTS: frozenset({"aws", "azure"}),
    protocol.GITIGNORE: "node_modules/\ncoverage/\n.build/\n",
    protocol.AGENT_PERMISSIONS: ["npm ci", "npm run verify", "npm test *"],
    protocol.GATE_DESCRIPTION: (
        "Biome — lint, formatting and import order in one pass — TypeScript (`tsc`), and Vitest"
    ),
    protocol.EVENT_MODEL_PATHS: lambda project_name, service: {
        "events": f"{service}/src/domain/<context>/events.ts",
        "domain": f"{service}/src/domain/<context>/decider.ts",
        "usecase": f"{service}/src/application/<context>/<use-case>.ts",
        "test": f"{service}/tests/<slice>.test.ts (Vitest)",
    },
    protocol.MUTATION_TOOL: "Stryker",
}
