"""The TypeScript backend's answers about production: how a service becomes an image, and what it is told there.

Beside `typescript.py` rather than inside it only because that module is at the line budget; its `LANGUAGE`
merges these in, and they are its answers like any other. The recipe vocabulary (`__APP__`, `__IMAGE__`,
`$(PLATFORM)`) and the pins are core's, in `images.py`.
"""
from __future__ import annotations

from typing import Any

from ... import registry as protocol
from ...backends import APP
from ...images import NODE_VERSION, PACK

BACKEND: dict[protocol.Member[Any], object] = {
    protocol.IMAGE_BUILDER: {
        "tool": "pack",
        # Compiled first, by the same `build` script `make dev` runs, and only then packed. The buildpacks
        # cannot do the compiling: Paketo's npm-install copies every npm workspace package into its module
        # layers and leaves a symlink at `apps/<service>` before any `BP_NODE_RUN_SCRIPTS` script runs, so
        # what such a script writes there afterwards lands in the build-time copy and is missing from the
        # image — the container then dies with "Cannot find module …/.build/src/main.js". Compiled up front,
        # `.build/` is part of the workspace when the copy is made. The whole workspace is packed, because
        # the lockfile is the repository's; `BP_LAUNCHPOINT` names this service's compiled entry point, which
        # exists by the time node-start looks for it. `BP_NODE_RUN_SCRIPTS=` (empty) because the run-script
        # buildpack otherwise runs `build` again inside the image — its default — into the copy that is
        # thrown away. And the machine's `node_modules` stays out of the upload (`project.toml`,
        # `images.WORKSPACE_DESCRIPTOR`): uploaded, npm-install would `npm rebuild` it for the image instead
        # of installing from the lockfile, and a compiler for the image's platform is not in a laptop's.
        # No install step: `build-<service>` takes the npm dependency target as a prerequisite like every
        # other target that runs this project's own npm code (`project/shared_packages`), so the workspace
        # is installed by the time this recipe runs and installed once however many targets asked.
        "build": (
            f"npm --workspace {APP} run build\n\t"
            f"{PACK} --path . --env BP_NODE_VERSION={NODE_VERSION} --env BP_NODE_RUN_SCRIPTS= "
            f"--env BP_LAUNCHPOINT={APP}/.build/src/main.js $(PACK_FLAGS)"
        ),
        "packs_workspace": True,
    },
    protocol.MIGRATIONS_IN_PRODUCTION: {"command": ["npm", "--workspace", APP, "run", "migrate"]},
    # node-postgres reads `require` as *verify*, against a CA store RDS's private root is not in.
    # Per managed-database kind; `images.py`, above `POSTGRES_SSLMODE_KINDS`, says how each was measured.
    protocol.POSTGRES_SSLMODE: {"rds": "no-verify", "flexible-server": "no-verify"},
}
