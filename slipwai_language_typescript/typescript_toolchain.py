"""TypeScript's toolchain: how a service in this language installs, starts, checks and formats itself.

These are the language's answers to the toolchain members of the backend protocol (`src/slipwai/registry.py`,
whose shapes are fixed in `specs/001-slipwai-2-language-addons/contracts/backend-protocol.md`). `BACKEND` is
what the `typescript` backend answers and `FAMILY` what the family does. `typescript.py`'s `LANGUAGE` takes
both in. A command spells a service's path `APP`, which `tooling.for_app` stamps per service.
"""
from __future__ import annotations

from typing import Any

from ... import registry as protocol
from ...backends import APP, NODE_MAJOR, Tooling
from ...tooling import for_app
from ..shared_packages import PACKAGES

TOOLING: Tooling = {
    # The answer is owed and is this, but no recipe runs it: a target of this family's takes the npm
    # dependency target as a prerequisite instead (`project/shared_packages.npm_dependency`).
    "install": "npm ci",
    "migrate": f"npm --workspace {APP} run migrate",
    "integration": f"npm --workspace {APP} run test:integration",
    "ci_image": f"node:{NODE_MAJOR}-bookworm",
    "ci_install": "npm ci",
    "container_setup": "",
    "container_environment": {},
}

# The eight targets every service answers (`native_commands.TARGETS`), in that order.
NATIVE_COMMANDS = {
    "install": "npm ci",
    "typecheck": f"npm --workspace {APP} run typecheck",
    "lint": f"npm --workspace {APP} run lint",
    "test": f"npm --workspace {APP} test",
    "integration": f"npm --workspace {APP} exec -- vitest run --passWithNoTests tests/integration",
    "adversarial": f"npm --workspace {APP} exec -- vitest run --passWithNoTests -t adversarial",
    "audit": "npm audit --audit-level=critical",
    "mutation": "@echo 'Configure the repository-selected Stryker mutator, then run its checked-in configuration.'; exit 2",
}


def native_commands(path: str, verify: str) -> dict[str, str]:
    """One service's eight commands, spelled for its own directory."""
    return {target: for_app(command, path, verify) for target, command in NATIVE_COMMANDS.items()}


def dev_command(qualifier: str, path: str, verify: str) -> str:
    """How one service starts in the foreground. `LOG_FORMAT=pretty` is set in the workspace's `dev` script."""
    return f"npm --workspace {path} run dev"


def event_store_directory(path: str) -> str:
    """Where one service's driven adapters live, for prose that has to point at them."""
    return f"{path}/src/adapters/driven/"


# Biome's configuration names `apps/**` and `packages/**`, and `biome format --write .` honours that glob
# from the root. `packages/` is also where a Go module lives (the `go` family's `shared_code`), and Biome
# formats JSON: a digest over raw bytes then changes because a formatter ran, while `make lint` never
# saw the files — it is `biome check` inside each npm workspace. The loop is the same test
# `build-packages` already uses: a directory with a `package.json` is an npm package, and nothing else
# is. `biome.jsonc` stays as the one set of rules; this recipe is what stops it walking a tree it does
# not own. No install of its own: `format` takes the npm dependency target as a prerequisite
# (`project/shared_packages.consumers`).
BIOME_FORMAT = (
    f"@for dir in apps/*/ {PACKAGES}/*/; do \\\n"
    '\t\t[ -f "$$dir/package.json" ] || continue; \\\n'
    '\t\tnpm exec -- biome format --write "$${dir%/}"; \\\n'
    "\tdone"
)

BACKEND: dict[protocol.Member[Any], object] = {
    protocol.TOOLING: TOOLING,
    protocol.FEATURE_TOOLING: {},
    protocol.EXECUTABLES: frozenset(),
    protocol.DEV_COMMAND: dev_command,
    protocol.COMPOSE_CACHES: (
        "/workspace/node_modules",
        f"/workspace/{APP}/node_modules",
        f"/workspace/{APP}/.build",
    ),
    protocol.EVENT_STORE_DIRECTORY: event_store_directory,
    protocol.NATIVE_COMMANDS: native_commands,
}
FAMILY: dict[protocol.Member[Any], object] = {protocol.FORMATTER: BIOME_FORMAT}
