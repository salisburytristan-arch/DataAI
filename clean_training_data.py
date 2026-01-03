#!/usr/bin/env python3
"""Clean and validate training data for remote fine-tuning."""

import json
import hashlib
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Set
import random

class DataCleaner:
    def __init__(self, min_length: int = 50, max_length: int = 2048, min_instruction_len: int = 10):
        self.min_length = min_length
        self.max_length = max_length
        self.min_instruction_len = min_instruction_len
        self.seen_hashes: Set[str] = set()
        self.stats = defaultdict(int)
    
    def hash_example(self, example: Dict) -> str:
        """Create content hash for deduplication."""
        content = f"{example.get('instruction', '')}{example.get('input', '')}{example.get('output', '')}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_garbage(self, text: str) -> bool:
        """Detect low-quality content."""
        if not text or len(text.strip()) < 10:
            return True
        
        # Navigation/UI text
        garbage_patterns = [
            r'^(menu|navigation|click here|home|back|next|previous|copyright|all rights reserved)$',
            r'^\s*\d+\s*$',  # Just numbers
            r'^[^\w\s]+$',  # Just punctuation
        ]
        
        text_lower = text.lower().strip()
        for pattern in garbage_patterns:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Too many non-alphabetic chars
        alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
        if alpha_ratio < 0.4:
            return True
        
        return False
    
    def clean_text(self, text: str) -> str:
        """Normalize text formatting."""
        if not text:
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'([.!?]){3,}', r'\1\1', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def validate_example(self, example: Dict) -> tuple[bool, str]:
        """Validate single training example."""
        
        # Required fields
        if 'instruction' not in example or 'output' not in example:
            return False, "missing_fields"
        
        instruction = self.clean_text(example['instruction'])
        output = self.clean_text(example['output'])
        input_text = self.clean_text(example.get('input', ''))
        
        # Length checks
        if len(instruction) < self.min_instruction_len:
            return False, "instruction_too_short"
        
        if len(output) < self.min_length:
            return False, "output_too_short"
        
        total_len = len(instruction) + len(input_text) + len(output)
        if total_len > self.max_length:
            return False, "too_long"
        
        # Garbage checks
        if self.is_garbage(instruction) or self.is_garbage(output):
            return False, "garbage_content"
        
        # Deduplication
        content_hash = self.hash_example({
            'instruction': instruction,
            'input': input_text,
            'output': output
        })
        
        if content_hash in self.seen_hashes:
            return False, "duplicate"
        
        self.seen_hashes.add(content_hash)
        
        # Update cleaned example
        example['instruction'] = instruction
        example['output'] = output
        if input_text:
            example['input'] = input_text
        elif 'input' in example:
            del example['input']
        
        return True, "valid"
    
    def clean_dataset(self, input_file: Path, output_dir: Path, train_split: float = 0.95):
        """Clean dataset and split into train/val."""
        
        print(f"📂 Loading dataset: {input_file}")
        
        all_examples = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_examples.append(json.loads(line))
        
        print(f"   Total examples: {len(all_examples):,}\n")
        
        print(f"🧹 Cleaning and validating...")
        
        valid_examples = []
        rejection_reasons = Counter()
        
        for i, example in enumerate(all_examples):
            is_valid, reason = self.validate_example(example)
            
            if is_valid:
                valid_examples.append(example)
            else:
                rejection_reasons[reason] += 1
            
            if (i + 1) % 5000 == 0:
                print(f"   Processed {i+1:,}/{len(all_examples):,} ({len(valid_examples):,} valid)")
        
        print(f"\n✅ Validation complete:")
        print(f"   Valid: {len(valid_examples):,}")
        print(f"   Rejected: {len(all_examples) - len(valid_examples):,}")
        
        if rejection_reasons:
            print(f"\n📊 Rejection reasons:")
            for reason, count in rejection_reasons.most_common():
                print(f"   {reason}: {count:,}")
        
        # Shuffle
        random.shuffle(valid_examples)
        
        # Split train/val
        split_idx = int(len(valid_examples) * train_split)
        train_examples = valid_examples[:split_idx]
        val_examples = valid_examples[split_idx:]
        
        print(f"\n📦 Splitting dataset:")
        print(f"   Train: {len(train_examples):,} ({train_split*100:.0f}%)")
        print(f"   Val: {len(val_examples):,} ({(1-train_split)*100:.0f}%)")
        
        # Save
        output_dir.mkdir(parents=True, exist_ok=True)
        
        train_file = output_dir / "train_clean.jsonl"
        val_file = output_dir / "val_clean.jsonl"
        stats_file = output_dir / "dataset_stats.json"
        
        with open(train_file, 'w', encoding='utf-8') as f:
            for ex in train_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
        
        with open(val_file, 'w', encoding='utf-8') as f:
            for ex in val_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
        
        # Statistics
        stats = {
            "total_input": len(all_examples),
            "valid": len(valid_examples),
            "rejected": len(all_examples) - len(valid_examples),
            "rejection_reasons": dict(rejection_reasons),
            "train_count": len(train_examples),
            "val_count": len(val_examples),
            "train_split": train_split,
            "avg_instruction_len": sum(len(ex['instruction']) for ex in valid_examples) / len(valid_examples),
            "avg_output_len": sum(len(ex['output']) for ex in valid_examples) / len(valid_examples),
        }
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n💾 Saved:")
        print(f"   {train_file} ({train_file.stat().st_size / (1024**2):.1f} MB)")
        print(f"   {val_file} ({val_file.stat().st_size / (1024**2):.1f} MB)")
        print(f"   {stats_file}")
        
        # Sample examples
        print(f"\n📝 Sample valid examples:")
        for i, ex in enumerate(random.sample(valid_examples, min(3, len(valid_examples))), 1):
            print(f"\n   Example {i}:")
            print(f"   Instruction: {ex['instruction'][:80]}...")
            print(f"   Output: {ex['output'][:100]}...")
        
        return len(train_examples), len(val_examples)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean training data for remote fine-tuning")
    parser.add_argument("--input", default="./finetune_data/complete_dataset.jsonl", help="Input JSONL file")
    parser.add_argument("--output-dir", default="./clean_data", help="Output directory")
    parser.add_argument("--min-length", type=int, default=50, help="Min output length")
    parser.add_argument("--max-length", type=int, default=2048, help="Max total length")
    parser.add_argument("--train-split", type=float, default=0.95, help="Train split ratio")
    
    args = parser.parse_args()
    
    cleaner = DataCleaner(
        min_length=args.min_length,
        max_length=args.max_length
    )
    
    cleaner.clean_dataset(
        Path(args.input),
        Path(args.output_dir),
        args.train_split
    )
