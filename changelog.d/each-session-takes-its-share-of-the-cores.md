PATCH

**The service's test suite runs on its share of the machine's cores when slipwai's captain started the session.** Vitest starts a worker per core whatever else is running, so three slices testing at once on one machine asked for three machines: hr-test-2 at three berths on eighteen cores sat at a load of eighty, and a 20-second `make unit-service` took 280. `vitest.config.ts` now reads `SLIPWAI_TEST_WORKERS`, which the captain sets for every session it starts, into `maxWorkers`. Unset, as in a person's own run, vitest's default stands.
