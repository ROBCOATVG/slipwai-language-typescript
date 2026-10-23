"""The TypeScript family's `npm_workspace` answer names only files this package has.

Core reads every lock, Biome's configuration and the pins through the answer and never by path, so a lock the
answer can name and the package does not carry is a project that fails to generate. Every dependency set the
selection can produce is asked for here, for a service on its own and beside each browser-app dependency set.
"""
from __future__ import annotations

import itertools
import unittest
from pathlib import Path

from slipwai.project.biome import biome_version
from slipwai.project.frontend import web_lock_features, web_lock_suffix
from slipwai.registry import NPM_WORKSPACE, registry
from slipwai.selection import Selection

ROOT = Path(__file__).resolve().parents[1]
AXES = {"fastify": ("http", "fastify"), "postgres": ("persistence", "postgres")}


def selections() -> list[Selection]:
    chosen = [dict(AXES[feature] for feature in subset)
              for size in range(len(AXES) + 1)
              for subset in itertools.combinations(AXES, size)]
    return [Selection(axes) for axes in chosen]


class WorkspaceAnswerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.answer = registry().family_answer("typescript", NPM_WORKSPACE)

    def test_every_lock_the_answer_can_name_is_in_this_package(self) -> None:
        features = web_lock_features("react-vite")
        web = [set(subset) for size in range(len(features) + 1)
               for subset in itertools.combinations(features, size)]
        for selection in selections():
            self.assertTrue(self.answer.member_lock(selection).is_file(), selection.choices)
            self.assertTrue(self.answer.member_lock(selection).is_relative_to(ROOT))
            for chosen in web:
                lock = self.answer.workspace_lock(selection, web_lock_suffix(chosen, "react-vite"))
                self.assertTrue(lock.is_file(), lock.name)
                self.assertTrue(lock.is_relative_to(ROOT))

    def test_biome_is_here_and_pins_the_version_the_browser_app_does(self) -> None:
        self.assertTrue((self.answer.biome / "biome.jsonc").is_file())
        self.assertTrue((self.answer.biome / "domain-purity.grit").is_file())
        self.assertTrue(all(pin.is_relative_to(ROOT) for pin in self.answer.biome_pins))
        self.assertRegex(biome_version(self.answer, "typescript"), r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()


class BrowserAppTest(unittest.TestCase):
    """The browser app this family ships, held to the layout slipwai reads by name."""

    def test_react_vite_is_offered_and_its_material_is_here(self) -> None:
        from slipwai.npm_workspace import frontend
        found = frontend("react-vite")
        self.assertEqual(found.family, "typescript")
        self.assertTrue(found.root.is_relative_to(ROOT / "assets/frontends"))
        for relative in ("app", "api-client", "app-flags-local", "app-flags-target", "app-route-plain",
                         "app-route-client"):
            with self.subTest(relative=relative):
                self.assertTrue(found.at(relative).is_dir())
        for lock in ("locks/frontend-only.json", "locks/frontend-only-users-keycloak.json"):
            self.assertTrue(found.at(lock).is_file(), lock)

    def test_every_feature_it_declares_has_its_files(self) -> None:
        from slipwai.npm_workspace import frontend
        from slipwai.services import web_features
        for feature, row in web_features("react-vite").items():
            with self.subTest(feature=feature):
                self.assertTrue(frontend("react-vite").at(row["files"]).is_dir())
