"""The TypeScript family's `npm_workspace` answer names only files this package has.

Core reads every lock, Biome's configuration and the pins through the answer and never by path, so a lock the
answer can name and the package does not carry is a project that fails to generate. Every dependency set the
selection can produce is asked for here, for a service on its own and beside each browser-app dependency set.
"""
from __future__ import annotations

import itertools
import unittest

import checkout_languages

from slipwai.project.biome import biome_version
from slipwai.project.frontend import WEB_LOCK_FEATURES, web_lock_suffix
from slipwai.registry import NPM_WORKSPACE, registry
from slipwai.selection import Selection

ROOT = checkout_languages.package_roots()[0].parent / "typescript"
AXES = {"fastify": ("http", "fastify"), "postgres": ("event-store", "postgres")}


def selections() -> list[Selection]:
    workspace = checkout_languages.package("typescript").typescript_workspace
    chosen = [dict(AXES[feature] for feature in subset)
              for size in range(len(workspace.LOCK_FEATURES) + 1)
              for subset in itertools.combinations(workspace.LOCK_FEATURES, size)]
    return [Selection(axes) for axes in chosen]


class WorkspaceAnswerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.answer = registry().family_answer("typescript", NPM_WORKSPACE)

    def test_every_lock_the_answer_can_name_is_in_this_package(self) -> None:
        web = [set(subset) for size in range(len(WEB_LOCK_FEATURES) + 1)
               for subset in itertools.combinations(WEB_LOCK_FEATURES, size)]
        for selection in selections():
            self.assertTrue(self.answer.member_lock(selection).is_file(), selection.choices)
            self.assertTrue(self.answer.member_lock(selection).is_relative_to(ROOT))
            for features in web:
                lock = self.answer.workspace_lock(selection, web_lock_suffix(features))
                self.assertTrue(lock.is_file(), lock.name)
                self.assertTrue(lock.is_relative_to(ROOT))

    def test_biome_is_here_and_pins_the_version_the_browser_app_does(self) -> None:
        self.assertTrue((self.answer.biome / "biome.jsonc").is_file())
        self.assertTrue((self.answer.biome / "domain-purity.grit").is_file())
        self.assertTrue(all(pin.is_relative_to(ROOT) for pin in self.answer.biome_pins))
        self.assertRegex(biome_version(self.answer), r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
