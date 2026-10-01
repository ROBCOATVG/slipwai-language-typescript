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
