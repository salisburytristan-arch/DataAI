# Testkit Scaffold (ArcticCodex)

Structure (planned):
- fixtures/: corpora, conversations, policies, tools, forge samples
- generators/: random text/docs/frames/plans
- harness/: local server, vault harness, model/teacher/tool harnesses, chaos harness
- oracles/: invariants, metamorphic, citation, memory, sandbox, cost
- reporters/: junit, html, trace exporter

Initial implemented tests live under tests/:
- Deterministic retrieval, index build, fake-time hooks, context cache, orchestrator determinism.
- Distillation IO writes, hash embeddings, cache invalidation, frames roundtrip, basic meta-frame builds.
- Frame parse error cases, BLOB-T roundtrip, attach-embeddings missing sidecar.

Deterministic mode assumptions:
- Env flags: ACX_TEST_MODE=1, ACX_SEED, ACX_FAKE_TIME
- Retrieval tie-break stable (score, path, chunk_id)
- Chunking/hashing deterministic inputs

Next steps:
- Add __init__.py, fixtures, and harness stubs
- Wire deterministic clock/seeds in components
- Add pytest collection config
