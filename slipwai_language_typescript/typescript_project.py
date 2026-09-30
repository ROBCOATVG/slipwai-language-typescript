"""The TypeScript backend's answers about the project around its services: what git ignores, what an agent may
run, what the gate is called, where the event model's code lives, and what `make mutation` uses.

Moved here from core's per-backend tables (S05), keyed by the protocol's member constants. `typescript.py` is at
its line budget, which is why these sit beside it."""
from __future__ import annotations

from ... import registry as protocol

ANSWERS = {
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
