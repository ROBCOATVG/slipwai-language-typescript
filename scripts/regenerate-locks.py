#!/usr/bin/env python3
"""Move every committed lock to new pins, and refuse to write one `npm audit` still finds fault with.

A lock is committed per dependency set — each service selection, each one beside a browser app's features, each
browser app alone — because `npm ci` refuses a lock that disagrees with its manifest, and generation copies these
locks into a project rather than resolving anything. So when a pin moves, every lock that pins it moves with it,
in one change, or a generated project's `npm ci` refuses the tree it was handed.

**Each lock is its own record of the manifests it was resolved from.** Its root record and each workspace record
(`apps/service`, `apps/web`, `packages/api-client`) carry the dependencies those manifests declared, so the
manifests are rebuilt from the lock, the pins in `PINS` applied to them, and npm asked to re-resolve the lock
alone (`--package-lock-only`, no install, no scripts). What npm does not have to move, it keeps. Then
`npm audit` runs over the result, `npm audit fix` (never `--force`) takes the transitive fixes inside the
declared ranges, and a lock with an advisory left is reported and not written.

The manifests the generator writes are the other half and are edited by hand to the same `PINS` and `ADDED`:
`assets/languages/typescript/app/package.json`, `PACKAGE_ADDITIONS` in `typescript.py`,
`assets/frontends/react-vite/app/package.json` and `assets/frontends/react-vite/api-client/package.json`. `tests/test_typescript_workspace.py` holds the two halves
together.

    python3 scripts/regenerate-locks.py            # every lock under assets/
    python3 scripts/regenerate-locks.py --check    # audit them as committed, write nothing
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: The pins every manifest moves to, where it declares the package at all. Exact versions: a range would make two
#: generations a week apart two different projects.
PINS = {
    "vitest": "4.1.12",
    "fastify": "5.12.7",
    "vite": "8.3.5",
    # 7 rather than 6: 6 reaches `braces` through `fast-glob`, and every `braces` there is has an advisory, so the
    # only fix is not depending on it. 7 does not, and declares a peer of TypeScript 5 (`ADDED`).
    "openapi-typescript": "7.13.0",
}
#: What a manifest gains that it did not declare, by the package's name. The typed client's generator calls the
#: TypeScript compiler's JavaScript API, which TypeScript 7 — the workspace's — does not have, so the client
#: carries a TypeScript 5 of its own; npm nests it, and the generator beside it, under `packages/api-client`.
ADDED = {
    "@packages/api-client": {"devDependencies": {"typescript": "5.9.3"}},
}
#: The fields of a workspace record that are the manifest's own.
MANIFEST_FIELDS = ("name", "version", "private", "workspaces", "dependencies", "devDependencies",
                   "optionalDependencies", "peerDependencies")
NPM = ["--ignore-scripts", "--no-fund", "--loglevel=error"]
#: The npm that re-resolves, named rather than taken from the PATH: npm 10's resolver dies on a lock rebuilt
#: this way (`Cannot read properties of null (reading 'edgesOut')`), and npm 11 is what Node 24 — the image a
#: generated project's CI runs in — carries, so the locks are resolved by the npm that will read them.
NPM_COMMAND = ["npx", "--yes", "npm@11"]


def locks() -> list[Path]:
    return sorted(path for path in (ROOT / "assets").rglob("*.json")
                  if path.parent.name in ("locks", "workspace-locks"))


def pinned(manifest: dict) -> dict:
    for field, more in ADDED.get(manifest.get("name", ""), {}).items():
        manifest[field] = {**manifest.get(field, {}), **more}
    for field in ("dependencies", "devDependencies"):
        for name, version in PINS.items():
            if name in manifest.get(field, {}):
                manifest[field][name] = version
    return manifest


def rebuilt(lock: dict, into: Path) -> None:
    """The manifests the lock was resolved from, with the pins applied, and the lock beside them."""
    for key, record in lock["packages"].items():
        if key.startswith("node_modules/") or "/node_modules/" in key:
            continue
        manifest = pinned({field: record[field] for field in MANIFEST_FIELDS if field in record})
        if key == "" and "name" not in manifest:
            manifest["name"] = lock.get("name", "workspace")
        where = into / key
        where.mkdir(parents=True, exist_ok=True)
        (where / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (into / "package-lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


def npm(into: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*NPM_COMMAND, *arguments, *NPM], cwd=into, capture_output=True, text=True, check=False)


def advisories(into: Path) -> dict:
    done = npm(into, "audit", "--package-lock-only", "--json")
    try:
        return json.loads(done.stdout).get("vulnerabilities", {})
    except ValueError:
        raise SystemExit(f"npm audit said nothing readable in {into}: {done.stderr.strip()}") from None


def regenerate(path: Path, check: bool) -> list[str]:
    """Move one lock, or with `check` only audit it; the advisories left, as lines."""
    lock = json.loads(path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="slipwai-lock-") as scratch:
        into = Path(scratch)
        if check:
            (into / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")
            (into / "package.json").write_text(json.dumps({"name": "audit"}), encoding="utf-8")
        else:
            rebuilt(lock, into)
            done = npm(into, "install", "--package-lock-only")
            if done.returncode != 0:
                return [f"npm install refused {path.name}: {done.stderr.strip()[-400:]}"]
            if advisories(into):
                npm(into, "audit", "fix", "--package-lock-only")
        left = advisories(into)
        if left:
            return [f"{path.relative_to(ROOT)}: {name} ({row.get('severity')})" for name, row in sorted(left.items())]
        if not check:
            shutil.copyfile(into / "package-lock.json", path)
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check", action="store_true", help="audit the committed locks and write nothing")
    parsed = parser.parse_args(argv)
    found: list[str] = []
    for path in locks():
        said = regenerate(path, parsed.check)
        print(f"{'FAULT' if said else 'ok   '} {path.relative_to(ROOT)}")
        found += said
    for line in found:
        print(f"  {line}", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
