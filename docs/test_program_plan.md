# ArcticCodex Comprehensive Test Program

Phases
- Unit: codecs/hash/canonicalization; chunking/token budgeting; cache keys; schema validation; sandbox policies.
- Integration: vault ingest→index→retrieve; memory proposals→approval; teacher protocols with mocks; context builder + retriever + orchestrator.
- End-to-end: CLI/Studio→Core→Vault→student→teachers; project build; forget/recovery; malicious KB; credit-burn fallback; index rebuild under load.
- Fuzz/adversarial/chaos: corrupt frames, bit-rot, crash mid-write, prompt injection corpus, sandbox escapes, power-loss simulations.
- Performance/load: latency SLOs; ingest throughput; reindex time; cache hit rates; capacity targets; concurrency.
- Regression gates: golden queries/citations/memory behavior; ForgeNumerics golden frames; determinism checks (same inputs + seed → same outputs).

Quality Gates
- Integrity: vault hashes/manifests consistent; crash safety.
- Safety: sandbox denies forbidden IO/exec/network; redaction and secret handling.
- Grounding: citations or explicit assumptions for claims.
- Determinism: fixed seed/time/vault → stable retrieval and prompts.
- Budgets: teacher cost caps enforced; no runaway spend.
- Forget/privacy: tombstoned/forgotten content never retrieved or cached.

Deterministic Test Mode
- Env: ACX_TEST_MODE=1, ACX_SEED=<int>, ACX_FAKE_TIME=<ts>
- Tie-breaks deterministic (retrieval sorted by score, path, chunk_id).
- Fixed chunking/tokenization and hashing.

Harness (see testkit/README.md)
- Fixtures: corpora, conversations, policies, tools, forge frames.
- Generators: random text/docs/frames/plans for fuzz.
- Harness: local server, vault harness, model/teacher/tool harnesses, chaos harness.
- Oracles: invariants, metamorphic, citation, memory, sandbox, cost.
- Reporters: JUnit, HTML, trace exporter.

Execution Cadence
- Per-commit: unit + schema + small property tests.
- Nightly: fuzz, chaos (crash/bit-rot), performance/load smoke.
- Weekly: capacity + long end-to-end project build scenario.
- Artifacts: JUnit, trace bundles, small vault snapshot for repro.
