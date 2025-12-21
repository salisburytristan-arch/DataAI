# Curriculum & Corpus

## What exists

ForgeNumerics includes generated corpora under:
- `ForgeNumerics_Language/out_curriculum/`

The documentation describes:
- a 1000-example curriculum
- train/valid/test splits
- a validation pipeline (parse success, round-trip fidelity, schema conformance)

## Regenerate curriculum (reference)

From the production guide, a typical command is:

```powershell
cd "D:\ArcticCodex - AGI"
python -m src.cli generate-curriculum --size 1000 --json
```

Note: If you run this from the repository root, you may need to `cd` into `ForgeNumerics_Language/` first:

```powershell
cd "D:\ArcticCodex - AGI\ForgeNumerics_Language"
python -m src.cli generate-curriculum --size 1000 --json
```

## Validate corpus

```powershell
cd "D:\ArcticCodex - AGI\ForgeNumerics_Language"
python -m src.cli verify-corpus --file out_curriculum/forge_curriculum_full.json
```

## Export splits

```powershell
cd "D:\ArcticCodex - AGI\ForgeNumerics_Language"
python -m src.cli export-splits --file out_curriculum/forge_curriculum_full.json --out-dir out_curriculum/splits --train 0.8 --valid 0.1 --test 0.1 --seed 42
```

## Buyer note

If a buyer wants to use the corpus for training a model, keep:
- the serialized frames
- the schema/meta-layer frames
- the generator + validator so new data stays consistent
