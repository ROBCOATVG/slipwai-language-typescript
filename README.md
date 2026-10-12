# slipwai-language-typescript
slipwai 2.0 language addon: slipwai-language-typescript

## The npm workspace: this package's side

A TypeScript service is an npm package, so it shares the project's one npm workspace with slipwai's `react-vite`
browser app. slipwai's core owns the browser app and the workspace's root (its `package.json`, its build script, the
`frontend-only` lock of a project with no TypeScript service); this package joins the workspace by answering the
family-level protocol member `npm_workspace` with an `NpmWorkspace` (`slipwai_language_typescript/typescript_workspace.py`):

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

The CI keel, reusable workflow and unpublished AWS/Azure target sources are pinned together to
`ROBCOATVG/slipwai_v2_Fork@75c053a86817bd12676948f0344f94c451145b62`. Source siblings are declared explicitly and
validated before normal conformance; this proves their checkout topology without pretending they are
published chandlery packages. Both conformance/matrix/tag builds and the native state-contract job use
that same source commit, while the TypeScript checkout remains the package under test.
