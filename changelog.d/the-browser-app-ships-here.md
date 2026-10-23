MINOR

**The `react-vite` browser app ships in this package, because slipwai's keel no longer carries one.** Its files
moved from the keel's `assets/frontends/react-vite/` to this package's, beside the locks that already resolved
them, and `language.json` declares it in a `frontends` block — its label, capabilities, what each feature adds,
owns and depends on, the files carrying a marked region, and its styled baseline — which slipwai reads, and a
generated project's pruner reads too. Each variant tree is laid out like the app and every file carries the
same tokens, so a second frontend is a different tree rather than a change to the keel. A project generated
with it is byte for byte the project the keel generated before, apart from the pruner's own tables. CI also runs
conformance every night against the keel's `main`, so a keel change that breaks this package shows here first.

**Catch-up:** `slipwai language upgrade typescript` beside a keel with phase 17, then `slipwai migrate`; a
project's browser app is unchanged, and its `scripts/backing-services.py` gains the frontend's rows.
