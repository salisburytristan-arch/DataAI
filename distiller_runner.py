#!/usr/bin/env python3
"""
Synthetic Data Distiller: Quick Start Guide

Convert local .txt files → Expert Models

Usage:
    python distiller_runner.py --input medical_protocol.txt --domain medical
    
    Or programmatically:
    
    from packages.core.src.synthetic_data_distiller import SyntheticDataDistiller
    from packages.core.src.teacher_client import DeepSeekClient
    from packages.core.src.llm_providers import AnthropicClient
    
    distiller = SyntheticDataDistiller(deepseek, anthropic)
    results = distiller.distill_document(
        file_path="your_document.txt",
        questions_per_chunk=5
    )
    
    # Output: Golden dataset ready for fine-tuning!
"""

import os
import sys
from pathlib import Path


def run_distillation_example(txt_file: str, domain: str = "general"):
    """
    Example: Distill a .txt file into training data
    """
    from packages.core.src.synthetic_data_distiller import SyntheticDataDistiller
    from packages.core.src.teacher_client import DeepSeekClient
    from packages.core.src.llm_providers import AnthropicClient
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Check API keys
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not deepseek_key or not anthropic_key:
        print("ERROR: Missing API keys")
        print("Set DEEPSEEK_API_KEY and ANTHROPIC_API_KEY in .env")
        return
    
    # Check input file
    if not os.path.exists(txt_file):
        print(f"ERROR: File not found: {txt_file}")
        return
    
    # Initialize clients
    print("Initializing API clients...")
    deepseek = DeepSeekClient(api_key=deepseek_key)
    anthropic = AnthropicClient(api_key=anthropic_key)
    
    # Create distiller
    output_dir = f"./distilled_{Path(txt_file).stem}"
    distiller = SyntheticDataDistiller(
        teacher_client=deepseek,
        validator_client=anthropic,
        output_dir=output_dir
    )
    
    # Run pipeline
    results = distiller.distill_document(
        file_path=txt_file,
        questions_per_chunk=5,
        generation_budget=10.0,
        validation_budget=5.0
    )
    
    return results


def demonstrate_workflow():
    """
    Show the workflow for text-to-model distillation
    """
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║              SYNTHETIC DATA DISTILLATION WORKFLOW                      ║
║         Convert Your .txt Into A Fine-Tuned Expert Model              ║
╚════════════════════════════════════════════════════════════════════════╝

THE PROBLEM WITH RAG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    You have a medical manual (5MB of perfect knowledge)
    ↓
    You use RAG: Model searches the manual on every query
    ↓
    Result: Slow, shallow understanding, expensive (per-query tokens)

THE SOLUTION: DISTILLATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    You have a medical manual (5MB)
    ↓
    Step 1: Generate Q&A pairs from manual (DeepSeek-R1, $10)
    ↓
    Step 2: Validate Q&A pairs (Claude, $5)
    ↓
    Step 3: Fine-tune local 7B model (Vast.ai, $10)
    ↓
    Result: Model MEMORIZED the manual, instant answers, cheap to run!

THE MATH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Generation:  1,000-2,000 Q&A pairs  @  $10
    Validation:  500-1,000 pairs        @  $5
    Fine-Tune:   4090 GPU rental        @  $10/hour (30-60 min)
    ───────────────────────────────────────────
    TOTAL:       Expert Model           @  $25-30

THE WORKFLOW (4 Steps):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: LOAD & CHUNK YOUR TEXT FILE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:    your_manual.txt (5MB, static knowledge)                       │
│ Process:  Split into semantic chunks (800 chars each)                   │
│ Output:   400 chunks, ready for Q&A generation                          │
│ Cost:     FREE                                                          │
│ Time:     <1 second                                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: GENERATE Q&A PAIRS (DeepSeek-R1, ~$10)                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:    400 chunks                                                    │
│ Teacher:  "Read this section. Generate 5 realistic Q&A pairs."         │
│ Output:   2,000 Q&A pairs with reasoning chains                         │
│ Quality:  Raw but reasoning-heavy (Q=question, A=answer, R=reasoning)  │
│ Cost:     ~$10 ($0.005/pair)                                            │
│ Time:     10-15 minutes                                                 │
│                                                                          │
│ Example Output:                                                         │
│   Q: "Patient has symptom X, what protocol applies?"                   │
│   A: "Protocol 4.1 describes management of X..."                       │
│   R: "This matches Section 4.1 which specifically addresses X."         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: VALIDATE Q&A PAIRS (Claude 3.5 Sonnet, ~$5)                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:    2,000 Q&A pairs                                               │
│ Validator: "Is this answer grounded in the manual? Any hallucination?" │
│ Output:    1,000 approved pairs (50% sample validated)                  │
│ Quality:   Golden standard (approved by Claude)                         │
│ Cost:      ~$5 (validate ~50% of pairs)                                 │
│ Time:      5-10 minutes                                                 │
│                                                                          │
│ Approval Rate: Typical 80-90% (good data quality)                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: EXPORT & FINE-TUNE (Ready for Model Training)                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Input:    1,000 validated golden pairs                                  │
│ Export:   JSONL format (instruction/output pairs)                       │
│ Next:     Fine-tune local 7B model on Vast.ai (4090 GPU, ~$10)         │
│ Result:   Specialist model that understands YOUR manual                 │
│ Cost:     $10 for 60-min fine-tune on 4090                              │
│ Time:     60-90 minutes                                                 │
└─────────────────────────────────────────────────────────────────────────┘

KEY ADVANTAGE OVER RAG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature              │ RAG (Standard)        │ Distillation (Your Way)
─────────────────────┼──────────────────────┼──────────────────────────
Speed                │ Slow (search+read)    │ Instant (memorized)
Understanding        │ Shallow (lookup)      │ Deep (reasoning)
Inference Cost       │ Per-token each query  │ One-time training cost
Reasoning            │ Limited               │ Full reasoning chains
Edge Cases           │ Must retrieve exact   │ Model understands combos
Final Output         │ Parroted text         │ Original reasoning

WHEN TO USE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ USE DISTILLATION FOR:
  • Static knowledge (medical guidelines, law, safety manuals)
  • Specialized domains (cardiology, tax code, company policies)
  • Frequent queries (high inference load)
  • Complex reasoning (multi-document combinations)
  • Cost optimization (pay once, use forever)

✗ DON'T USE DISTILLATION FOR:
  • Frequently changing data (stock prices, today's weather)
  • One-off queries (low query volume)
  • Massive documents (>10MB, too expensive to distill)

EXECUTION (YOUR $100 BUDGET):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Budget: $100

Option 1: Single Document (Deep Distillation)
  • 1 document (5-10MB)
  • 2,000-3,000 Q&A pairs
  • High validation
  • Cost: $25-30
  • Remaining: $70-75 for other projects

Option 2: Multiple Documents (Breadth)
  • 3-4 documents (2-3MB each)
  • 800-1,000 Q&A per document
  • Standard validation
  • Cost: $20-25 per document
  • Build specialist model on multiple domains

Option 3: Full Pipeline (Test → Validate → Train)
  • 1-2 documents
  • Full generation + validation + fine-tuning
  • Actual model training on Vast.ai
  • Cost: $35-50 (generation $10 + validation $5 + training $20-35)
  • Result: Usable specialist model

YOUR IMMEDIATE NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Prepare a .txt file:
   • Choose something valuable & static
   • Good examples: "Medical_Protocol_2025.txt", "Company_Safety_Manual.txt"
   • Size: 1-10MB optimal

2. Set API keys in .env:
   DEEPSEEK_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-...

3. Run distillation:
   python distiller_runner.py --input your_file.txt

4. Get golden dataset:
   distilled_your_file/golden_dataset.jsonl

5. Fine-tune model (optional):
   Upload to Vast.ai 4090 instance, train for 1 hour
    """)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Synthetic Data Distiller: Text → Training Data → Expert Model"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to .txt file to distill"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="general",
        help="Domain (medical, legal, technical, etc.)"
    )
    parser.add_argument(
        "--show-workflow",
        action="store_true",
        help="Show full workflow documentation"
    )
    
    args = parser.parse_args()
    
    if args.show_workflow:
        demonstrate_workflow()
        return
    
    if not args.input:
        print("Usage: python distiller_runner.py --input document.txt")
        print("       python distiller_runner.py --show-workflow")
        return
    
    print(f"\n{'='*70}")
    print("SYNTHETIC DATA DISTILLER")
    print(f"{'='*70}")
    
    results = run_distillation_example(args.input, args.domain)
    
    if results:
        print(f"\n{'='*70}")
        print("SUCCESS!")
        print(f"{'='*70}")
        print(f"\nGolden Dataset: {results['golden_dataset_file']}")
        print(f"Ready for fine-tuning!")


if __name__ == "__main__":
    main()
