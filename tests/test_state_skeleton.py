"""Generate through the keel, then hold both rungs to native gates and the actual database contract.

Generation is fast. Native gates opt in with SLIPWAI_STATE_NATIVE=1 and DATABASE_URL, and run in the
package's state-contract CI job on every PR. No installed npm toolchain is required for conformance.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from slipwai.matrix.rows import Row
from slipwai.matrix.run import generate

PACKAGE_PARENT = Path(__file__).resolve().parents[2]


class StateSkeletonTest(unittest.TestCase):
    def generated(self, rung: str, persistence: str, profile: str = "event-modelling", http: str = "none") -> Path:
        parent = Path(tempfile.mkdtemp(prefix="slipwai-ts-state-"))
        self.addCleanup(shutil.rmtree, parent, True)
        answers = (("target", "none"), ("write-model", rung))
        if profile == "event-modelling":
            answers += (("persistence", persistence), ("http", http), ("auth", "none"), ("users", "none"))
        repo, said = generate(PACKAGE_PARENT, parent, Row("proof", profile, "typescript", "none", answers))
        self.assertIsNotNone(repo, said)
        assert repo is not None
        return repo

    def test_state_selects_repository_and_no_event_history_for_every_adapter(self) -> None:
        for persistence in ("memory", "sqlite", "postgres"):
            with self.subTest(persistence=persistence):
                service = self.generated("state", persistence) / "apps/service"
                self.assertTrue((service / "src/application/ports/repository.ts").is_file())
                self.assertTrue((service / "src/application/ports/event-context.ts").is_file())
                self.assertTrue((service / "tests/contract/repository-memory.test.ts").is_file())
                self.assertFalse((service / "src/application/ports/events.ts").exists())
                self.assertFalse((service / "src/domain/decider.ts").exists())
                if persistence == "postgres":
                    self.assertTrue((service / "migrations/001_states.js").is_file())
                    self.assertFalse((service / "migrations/001_events.js").exists())

    def test_standard_has_a_memory_state_baseline(self) -> None:
        service = self.generated("state", "memory", "standard") / "apps/service"
        self.assertTrue((service / "src/application/ports/repository.ts").is_file())
        self.assertFalse((service / "src/application/ports/events.ts").exists())

    def test_events_keep_history_and_gain_mandatory_context(self) -> None:
        service = self.generated("events", "postgres") / "apps/service"
        self.assertTrue((service / "src/application/ports/events.ts").is_file())
        self.assertTrue((service / "src/application/ports/event-context.ts").is_file())
        self.assertTrue((service / "migrations/001_events.js").is_file())
        self.assertFalse((service / "src/application/ports/repository.ts").exists())

    @unittest.skipUnless(os.environ.get("SLIPWAI_STATE_NATIVE") == "1", "native rung proof runs in state-contract CI")
    def test_both_rungs_pass_real_gates_and_postgres_contract(self) -> None:
        self.assertTrue(os.environ.get("DATABASE_URL"), "DATABASE_URL is required for the PostgreSQL contract")
        npm = shutil.which("npm")
        self.assertIsNotNone(npm, "install Node and npm before the native proof")
        for rung in ("state", "events"):
            for persistence in ("memory", "sqlite", "postgres"):
                with self.subTest(rung=rung, persistence=persistence):
                    http = "fastify" if persistence == "postgres" or rung == "state" else "none"
                    repo = self.generated(rung, persistence, http=http)
                    self.run_gate([str(npm), "ci"], repo)
                    self.run_gate([str(npm), "audit", "--audit-level=high"], repo)
                    if os.name == "nt":
                        # Windows has no make; the native compiler/linter/contracts still run.
                        self.run_gate([str(npm), "run", "-w", "apps/service", "verify"], repo)
                    else:
                        self.run_gate(["make", "verify"], repo)
                    if persistence == "postgres":
                        self.run_gate([str(npm), "run", "-w", "apps/service", "migrate", "--",
                                       "--migrations-table", f"proof_{rung}"], repo)
                        self.run_gate([str(npm), "run", "-w", "apps/service", "test:integration"], repo)
                        if rung == "state":
                            self.run_gate([sys.executable, "scripts/backing-services.py",
                                           "--persistence", "memory"], repo)
                            adapter = repo / "apps/service/src/adapters/driven/repository-postgres/index.ts"
                            self.assertFalse(adapter.exists())
                            self.assertFalse((repo / "apps/service/migrations/001_states.js").exists())
                            self.run_gate([str(npm), "ci"], repo)
                            if os.name == "nt":
                                self.run_gate([str(npm), "run", "-w", "apps/service", "verify"], repo)
                            else:
                                self.run_gate(["make", "verify"], repo)

    def run_gate(self, command: list[str], repo: Path) -> None:
        done = subprocess.run(command, cwd=repo, text=True, capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0, done.stdout[-12000:] + done.stderr[-6000:])
        for line in done.stdout.splitlines():
            if line.strip().startswith(("Test Files", "Tests ", "found 0 vulnerabilities")):
                print(f"{repo}: {line.strip()}", flush=True)
