MINOR

**TypeScript is now a language package of its own.** The TypeScript backend that was built into slipwai — its
service skeleton on Node, npm workspaces, Biome, `tsc` and Vitest, its event-store adapters, its Fastify transport,
identity wiring, mutation gate and committed package locks — lives here, with the history it had there, and slipwai
loads it from its language directory (`$SLIPWAI_LANGUAGES`, or `~/.slipwai/languages`). The projects it generates
are byte for byte those slipwai generated with TypeScript built in. It answers `npm_workspace`, so its services
share the project's one npm workspace with core's browser app: this package carries their committed locks, the
workspace locks for a TypeScript service beside a browser app, and the Biome configuration the workspace runs. It
declares the catalog schema it loads on, `core >=9.0,<10`, in `language.json`.
