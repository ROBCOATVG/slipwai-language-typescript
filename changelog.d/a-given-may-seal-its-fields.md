MINOR

**A story's given may seal its fields, so a product that encrypts personal data can be seeded.** A product
that seals personal fields under a per-workspace key (the crypto-shredding pattern) could not be given those
events at all: a given is plain JSON, and the folds refuse a plain email where a sealed one belongs, so the
screens behind such an event were proven only by tests and never walked from seeded state. A given may now
say `"seal": { "key": "<whose key>", "fields": ["email"] }` with those fields in plain text. The seed door
hands them to the project's own `scripts/seed-seal.ts`, which exports `seal(request, pool)`: it finds or
mints the key named and returns each field sealed the way the product seals it. This package does not know
the project's cryptography, so the hook is the project's. A given that seals with no hook is refused, and so
is a hook that hands back a field unchanged or leaves it out. Nothing is appended in plain text. A sealed
given is still recorded once, however often it is replayed: its identity is the hash of the given as
written, carried as the event's `causation_id`, because sealing the same text twice gives different
ciphertext. The door's logic moved to `scripts/seed-door.ts`, with a suite on the in-memory store in
`tests/seed/seed-door.test.ts`. Plain givens work as before.

**Catch-up:** `slipwai language upgrade typescript`, then `slipwai migrate`. The service gains
`scripts/seed-door.ts` and its test, and `scripts/seed.ts` is replaced. A project that seals fields writes
`scripts/seed-seal.ts` against `SealHook` from `scripts/seed-door.ts`, for example by calling its own key
store and field cipher.
