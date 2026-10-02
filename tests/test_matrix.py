"""This package's own generated-variant matrix, against the slipwai it is tested with (FR-036, D100).

Every native-gate variant of each backend this package owns is generated and held to its own `make verify`, and its
production image built and started where Docker is here. That takes minutes and every toolchain, so the case skips
unless `SLIPWAI_MATRIX=1`; `python -m slipwai.matrix <language-dir> typescript` runs the same cases. The language
directory is the one this package sits in, so the root suite's shims run it against the checkout's pins.

The rows only TypeScript has are here: the npm workspace it shares with the `react-vite` frontend pins one committed
lockfile per frontend answer, so each is generated with every axis answered.
"""
from __future__ import annotations

from pathlib import Path

from slipwai import matrix


class Matrix(matrix.MatrixCase):
    language_dir = Path(__file__).resolve().parents[2]
    package = "typescript"

    def test_every_frontend_with_every_axis_answered_passes_its_own_gate(self) -> None:
        """With every axis answered the gate must still pass on a machine with no Docker at all — that is the whole
        point of the in-memory adapter the port's contract runs against. Both frontends, because each pins a
        different committed lockfile and `npm ci` refuses a lockfile that disagrees with its manifest."""
        self.require("typescript")
        for frontend in ("none", "react-vite"):
            with self.subTest(frontend=frontend):
                repo = self.generate(f"verify-services-{frontend}", "event-modelling", "typescript", frontend,
                                     event_store="postgres", http="fastify", auth="keycloak", users="keycloak")
                self.verify(repo)
