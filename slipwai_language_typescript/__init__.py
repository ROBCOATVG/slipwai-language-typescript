"""The `typescript` language package: the TypeScript backend slipwai loads from its language directory.

`LANGUAGE` is the object core's loader reads: the `typescript` family and its one backend, answering the backend
protocol, and the family's `npm_workspace` answer, which is what makes a TypeScript service a member of the
project's npm workspace beside its browser apps. Everything else in this package is what those answers are made
of, and the files they read are the ones under `assets/` beside it.
"""
from __future__ import annotations

from .typescript import LANGUAGE

__all__ = ["LANGUAGE"]
