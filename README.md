# slipwai-language-typescript
slipwai 2.0 language addon: slipwai-language-typescript

## The npm workspace and the browser app: this package's side

A TypeScript service is an npm package, and so is a browser app, so both share the project's one npm workspace —
and this package ships both halves. slipwai's keel ships no frontend: the `react-vite` browser app lives here,
under `assets/frontends/react-vite/`, beside the services' `assets/languages/typescript/`, because this package
already commits the locks that resolve it and pins the Biome it is linted with. `language.json`'s `frontends`
block declares it — its label, capabilities, the files each feature adds, owns and depends on, its styled
baseline — and `slipwai_language_typescript/typescript_frontends.py` answers `browser_apps` with its directory.
The layout under it, and every field, are slipwai's `docs/frontend-protocol.md`.

The family joins the workspace by answering the family-level protocol member `npm_workspace` with an
`NpmWorkspace` (`slipwai_language_typescript/typescript_workspace.py`):

| Field | What this package promises |
|---|---|
| `member_lock` | each TypeScript service's committed `package-lock.json`, for its selection (`assets/languages/typescript/locks/`) |
| `workspace_lock` | the workspace lock for a first TypeScript service of that selection beside browser apps with that lock suffix (`assets/languages/typescript/workspace-locks/`) |
| `image` | the image a browser app's dev server runs in under Compose: this backend's CI image |
| `biome` | the directory holding `biome.jsonc` and `domain-purity.grit`, the workspace's one lint and format gate |
| `biome_pins` | this package's manifests that pin `@biomejs/biome`, which agree with the browser app's |

Because this family answers the member first in slipwai's order, a browser app is written in TypeScript: its
`shared_code` paragraph and its `formatter` line are this family's. slipwai's side of the same contract is
`contracts/npm-workspace.md` in its repository; `tests/test_typescript_workspace.py` holds this side to naming only
files this package has.

## Service write model and event context

This binding requires the keel's phase 15.6 service-write-model protocol (catalog schema 9). Existing
package and product version pins stay unchanged until release. `--write-model state` selects a
versioned repository and memory, SQLite or PostgreSQL adapter. A missing row is `NO_STATE`; `save`
returns a version conflict as a value. PostgreSQL updates compare and increment the version in one
statement. `--write-model events` retains the event store, projections and replay contract.

Both rungs require `EventContext` when raising or appending a fact: `actor_id`, `occurred_at`, branded
`correlation_id`, and branded `causation_id` or explicit `null` for the first cause. Delegation uses
`delegatedContext` and requires `on_behalf_of`. Attribution identifies who acted; it grants no resource
ownership. Business payloads refer to sensitive data by id. Store metadata stays separate.

Constructing an event with the former flat actor/time fields is intentionally rejected by the compiler.
The event-store API and committed version/position fields retain their shape; SQL reads derive context
from already recorded actor and causal fields, with no invented historical events. The state example's
`saveAndRaise` publishes new facts only after a successful save; it is an in-process example, not a
durable outbox. A publisher failure needs an application-specific recovery policy before production.

`SLIPWAI_STATE_NATIVE=1 DATABASE_URL=... python -m unittest discover -s tests -p test_state_skeleton.py -v`
generates both rungs with all three adapters, runs their real gates and the PostgreSQL contracts. The
`state-contract` PR job runs the same proof against PostgreSQL 17, including two independent pools
racing an insert and a same-version update. Ordinary conformance needs no database or Node toolchain.

The CI keel and the reusable workflow are pinned together to
`ROBCOATVG/slipwai@ac040489769deacd88a21fe33e996fd3ee100eef`, and the AWS and Azure targets are installed
beside the package from the chandlery, as a person would install them. The native state-contract job takes
the target sources from the keel's own submodules at that commit. A nightly `contract-main` job proves the
same package against the keel's `main`, so a change there is heard of without waiting for a release here.
