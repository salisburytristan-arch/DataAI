# ArcticCodex Testkit (skeleton)

This package will host shared fixtures, generators, harnesses, oracles, and reporters for the ArcticCodex QA program.

Planned layout (per roadmap):
- fixtures/: corpora, conversations, policies, tools, forge frames
- generators/: random text/docs/frames/plans
- harness/: local server, vault harness, model harness, teacher harness, tool harness, chaos harness
- oracles/: invariants, metamorphic checks, citation/memory/sandbox/cost oracles
- reporters/: JUnit, HTML, trace exporter

Future work: populate with actual utilities, deterministic hooks (ACX_TEST_MODE, ACX_FAKE_TIME, ACX_SEED), and CI wiring.
