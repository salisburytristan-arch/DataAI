#!/usr/bin/env python3
"""
Cascade Pipeline Executor

Usage:
    python cascade_runner.py
    
    Or programmatically:
    
    from packages.core.src.cascade_pipeline import CascadePipeline
    from packages.core.src.llm_providers import DeepSeekClient, OpenAIClient, AnthropicClient
    import os
    
    # Initialize providers
    deepseek = DeepSeekClient(api_key=os.getenv("DEEPSEEK_API_KEY"))
    openai = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    anthropic = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Run cascade
    cascade = CascadePipeline(deepseek, openai, anthropic)
    results = cascade.run_full_cascade(num_samples=10000, domain="medical")
    
    # Results:
    # - 10,000 formatted training pairs
    # - 1,000 golden standard test set (10% validated)
    # - Full budget accounting
"""

import os
import json
from pathlib import Path


def run_cascade_example():
    """
    Example: Run the cascade pipeline with mock clients.
    In production, use real API credentials from .env
    """
    from packages.core.src.cascade_pipeline import CascadePipeline
    from packages.core.src.llm_providers import (
        DeepSeekClient, 
        OpenAIClient, 
        AnthropicClient
    )
    
    # Load API keys from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not all([deepseek_key, openai_key, anthropic_key]):
        print("ERROR: Missing API keys. Set DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY in .env")
        return
    
    # Initialize clients
    print("Initializing API clients...")
    deepseek = DeepSeekClient(api_key=deepseek_key)
    openai = OpenAIClient(api_key=openai_key)
    anthropic = AnthropicClient(api_key=anthropic_key)
    
    # Create pipeline
    output_dir = "./cascade_output"
    cascade = CascadePipeline(
        deepseek_client=deepseek,
        openai_client=openai,
        anthropic_client=anthropic,
        output_dir=output_dir
    )
    
    # Run full cascade
    results = cascade.run_full_cascade(
        num_samples=10000,
        domain="medical"  # Can be: medical, legal, scientific, financial
    )
    
    # Print detailed results
    print(f"\n{'='*70}")
    print("FINAL RESULTS")
    print(f"{'='*70}")
    print(json.dumps(results, indent=2))
    
    # Load and inspect golden set
    golden_file = Path(output_dir) / "golden_test_set.jsonl"
    if golden_file.exists():
        print(f"\n{'='*70}")
        print("SAMPLE FROM GOLDEN SET (first example)")
        print(f"{'='*70}")
        with open(golden_file) as f:
            first_line = f.readline()
            golden_sample = json.loads(first_line)
            print(json.dumps(golden_sample, indent=2))


def export_to_huggingface(output_dir: str = "./cascade_output"):
    """
    Optional: Export golden set + training data to HuggingFace format
    for community sharing or further fine-tuning.
    """
    from pathlib import Path
    import pandas as pd
    
    output_path = Path(output_dir)
    
    # Load golden test set
    golden_samples = []
    with open(output_path / "golden_test_set.jsonl") as f:
        for line in f:
            golden_samples.append(json.loads(line))
    
    # Load all training samples
    training_samples = []
    with open(output_path / "stage_b_formatted_pairs.jsonl") as f:
        for line in f:
            training_samples.append(json.loads(line))
    
    # Create DataFrame
    df_golden = pd.DataFrame(golden_samples)
    df_training = pd.DataFrame(training_samples)
    
    # Save as CSV for HuggingFace
    df_golden.to_csv(output_path / "golden_test_set.csv", index=False)
    df_training.to_csv(output_path / "training_data.csv", index=False)
    
    print(f"Exported to HuggingFace format:")
    print(f"  - {output_path / 'golden_test_set.csv'}")
    print(f"  - {output_path / 'training_data.csv'}")
    
    # Create dataset card
    dataset_card = f"""---
license: cc-by-4.0
task_categories:
- question-answering
- text-generation
language:
- en
---

# ArcticCodex Training Dataset

Generated via Cascade Pipeline with 3-stage validation.

## Dataset Summary

- **Training samples**: {len(df_training)}
- **Golden test set**: {len(df_golden)} (10% validated by Claude 3.5 Sonnet)
- **Generation cost**: ~$100 using DeepSeek-R1, GPT-4o-mini, Claude 3.5
- **Quality**: Trinary-logic verified reasoning chains

## Generation Pipeline

### Stage A: Raw Generation (DeepSeek-R1, $25)
- Complex reasoning chains
- 10,000 diverse examples
- Cross-domain problem scenarios

### Stage B: Formatting (GPT-4o-mini, $25)
- Clean JSON conversion
- ForgeNumerics structure
- Logical validation

### Stage C: Golden Standard (Claude 3.5 Sonnet, $25)
- 10% sample validation
- Supreme court approval
- Trustworthy test set

## Usage

```python
from datasets import load_dataset

# Load training data
ds = load_dataset('csv', data_files='training_data.csv')

# Load golden test set
golden = load_dataset('csv', data_files='golden_test_set.csv')
```

## Citation

```bibtex
@dataset{{arcticcodex_cascade_2025,
  title={{ArcticCodex Cascade-Generated Training Dataset}},
  year={{2025}},
  month={{December}},
  doi={{TBD}}
}}
```
"""
    
    with open(output_path / "README.md", "w") as f:
        f.write(dataset_card)
    
    print(f"Dataset card created: {output_path / 'README.md'}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run ArcticCodex Cascade Pipeline"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10000,
        help="Number of training samples to generate (default: 10000)"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="medical",
        choices=["medical", "legal", "scientific", "financial"],
        help="Problem domain (default: medical)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./cascade_output",
        help="Output directory (default: ./cascade_output)"
    )
    parser.add_argument(
        "--export-hf",
        action="store_true",
        help="Export to HuggingFace format after completion"
    )
    
    args = parser.parse_args()
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    CASCADE PIPELINE EXECUTOR                         ║
    ║                  Turn $100 Into Proprietary Training Data            ║
    ║                                                                      ║
    ║  Stage A: Generate 10,000 raw reasoning chains (DeepSeek-R1, $25)  ║
    ║  Stage B: Format into JSON (GPT-4o-mini, $25)                      ║
    ║  Stage C: Validate 1,000 golden examples (Claude 3.5, $25)         ║
    ║  Reserve: $25 contingency                                          ║
    ║                                                                      ║
    ║  Output: 10,000 training pairs + 1,000 golden test set             ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run cascade
    run_cascade_example()
    
    # Optional: Export to HuggingFace
    if args.export_hf:
        print("\nExporting to HuggingFace format...")
        export_to_huggingface(args.output_dir)


if __name__ == "__main__":
    main()
