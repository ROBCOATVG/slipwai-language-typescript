"""The browser apps the TypeScript family ships: its `browser_apps` answer.

A browser app is an npm package in the project's one workspace, and this family already commits the locks that
resolve it beside a TypeScript service and pins the Biome it is linted with, so the app's own material is here too,
under `assets/frontends/<name>/` — beside `assets/languages/typescript/`, which is the services' — rather than in
slipwai's keel, which ships no frontend. What a frontend is offered as and what each feature does to it (the files
it adds, the paths it owns, the npm dependencies it brings) is data, in `language.json`'s `frontends` block, because
the pruner inside a generated project reads it too; this answers where each one's files are.

The layout under each root is the one slipwai reads by name (`docs/frontend-protocol.md` in its repository):
`app/` the skeleton, `app-flags-local/` and `app-flags-target/` the two flag readers, `app-route-client/` and
`app-route-plain/` the one route, `api-client/` the typed client, `features/<feature>/` what a feature adds, and
`locks/frontend-only*.json` the workspace lock of a project whose services are in no npm language.
"""
from __future__ import annotations

from pathlib import Path

from slipwai.npm_workspace import FRONTENDS_DIRECTORY, BrowserApp

ROOT = Path(__file__).resolve().parents[1]

BROWSER_APPS: dict[str, BrowserApp] = {
    "react-vite": BrowserApp("react-vite", ROOT / FRONTENDS_DIRECTORY / "react-vite"),
}
