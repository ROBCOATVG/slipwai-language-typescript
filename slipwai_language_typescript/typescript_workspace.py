"""What the TypeScript family tells core about the npm workspace: its `npm_workspace` answer.

A TypeScript service is an npm package, so it is a member of the project's one workspace beside every browser app.
Core's `react-vite` frontend owns the workspace's root and the browser app; this answers the rest
(`contracts/npm-workspace.md`): each service's committed lock, the workspace lock for a TypeScript service beside
browser apps, the image a browser app's dev server runs in, and Biome, the lint and format gate every package in
the workspace shares.
"""
from __future__ import annotations

from pathlib import Path

from ...assets import LANGUAGE_ROOT
from ...npm_workspace import NpmWorkspace
from ...selection import Selection
from .typescript_toolchain import TOOLING

# The only features that add an npm dependency to a service, and therefore the only ones that change its lockfile.
# A lockfile is committed per combination rather than patched after the fact, because `npm ci` refuses to
# install from a lockfile that disagrees with package.json — the pair has to move together.
# `scripts/regenerate-locks.py` builds every one of these from the same manifests the generator emits. The
# workspace lock beside a browser app is named for the service's and then the browser app's.
LOCK_FEATURES = ("fastify", "postgres")
ASSETS = LANGUAGE_ROOT / "typescript"


def lock_suffix(selection: Selection) -> str:
    """The lockfile name for this selection's dependency set: '' for the plain one, '-fastify-postgres' for
    both. Sorted by `LOCK_FEATURES` so one dependency set has exactly one name."""
    chosen = [feature for feature in LOCK_FEATURES if selection.has(feature)]
    return "".join(f"-{feature}" for feature in chosen)


def service_lock(selection: Selection) -> Path:
    """Which committed lockfile matches this selection's dependency set."""
    return ASSETS / f"locks/package-lock{lock_suffix(selection)}.json"


def workspace_lock(selection: Selection, web_suffix: str) -> Path:
    """The committed lock of a workspace whose first TypeScript service has this selection, beside browser apps
    whose part of the name is `web_suffix`: resolved with both, because their dependencies hoist together."""
    return ASSETS / f"workspace-locks/typescript-backend{lock_suffix(selection)}{web_suffix}.json"


WORKSPACE_ANSWER = NpmWorkspace(
    member_lock=service_lock,
    workspace_lock=workspace_lock,
    image=TOOLING["ci_image"],
    biome=ASSETS / "biome",
    biome_pins=(ASSETS / "app/package.json",),
)
