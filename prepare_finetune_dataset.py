#!/usr/bin/env python3
"""Prepare comprehensive fine-tuning dataset from all sources."""

import json
import gc
import re
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
import random

def load_crawled_data(data_dir: Path, max_per_domain: int = 100) -> List[Dict]:
    """Load and sample crawled academic content."""
    print(f"📂 Loading crawled data from {data_dir}...")
    
    docs = []
    domain_counts = defaultdict(int)
    
    batch_files = sorted(data_dir.glob("batch_*.jsonl"))
    
    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    
                    # Sample evenly across domains
                    if domain_counts[doc['domain']] < max_per_domain:
                        docs.append(doc)
                        domain_counts[doc['domain']] += 1
    
    print(f"   ✅ Loaded {len(docs)} documents from {len(domain_counts)} domains")
    return docs

def load_knowledge_files(knowledge_dir: Path) -> List[str]:
    """Load knowledge text files."""
    print(f"📚 Loading knowledge files from {knowledge_dir}...")
    
    texts = []
    for txt_file in sorted(knowledge_dir.glob("*.txt")):
        try:
            text = txt_file.read_text(encoding='utf-8', errors='ignore')
            if len(text) > 500:
                texts.append(text)
        except Exception as e:
            print(f"   ⚠️  Error reading {txt_file.name}: {e}")
    
    print(f"   ✅ Loaded {len(texts)} knowledge files")
    return texts

def load_existing_training_data(data_dir: Path) -> List[Dict]:
    """Load existing JSONL training data."""
    print(f"🎯 Loading existing training data from {data_dir}...")
    
    examples = []
    for jsonl_file in ['train.jsonl', 'sft.jsonl', 'seed.jsonl']:
        file_path = data_dir / jsonl_file
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        examples.append(json.loads(line))
            print(f"   ✅ Loaded {jsonl_file}: {len(examples)} examples so far")
    
    return examples

def create_qa_from_content(text: str, title: str = "") -> List[Dict]:
    """Extract potential Q&A pairs from content using pattern matching."""
    qa_pairs = []
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
    
    for para in paragraphs[:5]:  # Limit to 5 per document
        # Skip if too short or looks like navigation
        if len(para) < 200 or any(x in para.lower() for x in ['click here', 'menu', 'navigation', 'copyright']):
            continue
        
        # Create instruction-following format
        # Pattern 1: "What is..." questions
        sentences = [s.strip() for s in para.split('.') if len(s.strip()) > 50]
        if len(sentences) >= 2:
            question = f"Explain {title.split('-')[0].strip().lower() if title else 'the following concept'}"
            answer = para[:500]  # First 500 chars
            
            qa_pairs.append({
                "instruction": question,
                "input": "",
                "output": answer
            })
    
    return qa_pairs

def prepare_comprehensive_dataset(
    crawled_dir: Path,
    knowledge_dir: Path,
    existing_data_dir: Path,
    output_file: Path,
    max_crawled_per_domain: int = 100,
    max_total_examples: int = 50000
):
    """Prepare comprehensive fine-tuning dataset."""
    
    all_examples = []
    
    # 1. Load existing training data (highest priority)
    existing = load_existing_training_data(existing_data_dir)
    all_examples.extend(existing)
    print(f"\n📊 Total after existing data: {len(all_examples)}")
    gc.collect()
    
    # 2. Load crawled academic content
    crawled_docs = load_crawled_data(crawled_dir, max_crawled_per_domain)
    
    print(f"\n🔄 Converting crawled content to Q&A format...")
    crawled_qa = 0
    for i, doc in enumerate(crawled_docs):
        if len(all_examples) >= max_total_examples:
            break
        
        qa_pairs = create_qa_from_content(doc['text'], doc.get('title', ''))
        all_examples.extend(qa_pairs)
        crawled_qa += len(qa_pairs)
        
        if (i + 1) % 1000 == 0:
            print(f"   Processed {i+1}/{len(crawled_docs)} docs, generated {crawled_qa} Q&A pairs")
            gc.collect()
    
    print(f"   ✅ Generated {crawled_qa} Q&A pairs from crawled content")
    print(f"\n📊 Total after crawled data: {len(all_examples)}")
    gc.collect()
    
    # 3. Load knowledge files and create instruction pairs
    if knowledge_dir.exists():
        knowledge_texts = load_knowledge_files(knowledge_dir)
        
        print(f"\n🔄 Converting knowledge files to instruction format...")
        knowledge_qa = 0
        for text in knowledge_texts:
            if len(all_examples) >= max_total_examples:
                break
            
            qa_pairs = create_qa_from_content(text, "knowledge base")
            all_examples.extend(qa_pairs)
            knowledge_qa += len(qa_pairs)
        
        print(f"   ✅ Generated {knowledge_qa} Q&A pairs from knowledge files")
        print(f"\n📊 Total after knowledge files: {len(all_examples)}")
        gc.collect()
    
    # Shuffle for better training
    print(f"\n🔀 Shuffling {len(all_examples)} examples...")
    random.shuffle(all_examples)
    
    # Limit to max examples
    if len(all_examples) > max_total_examples:
        all_examples = all_examples[:max_total_examples]
        print(f"   Trimmed to {max_total_examples} examples")
    
    # Write output
    print(f"\n💾 Writing to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # Statistics
    print(f"\n📊 Final Dataset Statistics:")
    print(f"   Total examples: {len(all_examples):,}")
    print(f"   Output file: {output_file}")
    print(f"   File size: {output_file.stat().st_size / (1024**2):.1f} MB")
    
    # Sample examples
    print(f"\n📝 Sample examples:")
    for i, ex in enumerate(random.sample(all_examples, min(3, len(all_examples))), 1):
        print(f"\n   Example {i}:")
        print(f"   Instruction: {ex.get('instruction', '')[:100]}...")
        print(f"   Output: {ex.get('output', '')[:150]}...")
    
    return len(all_examples)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare comprehensive fine-tuning dataset")
    parser.add_argument("--crawled-dir", default="./data_for_ai", help="Crawled data directory")
    parser.add_argument("--knowledge-dir", default="./KnowledgeTXT", help="Knowledge text directory")
    parser.add_argument("--existing-data", default="./data", help="Existing training data directory")
    parser.add_argument("--output", default="./finetune_data/complete_dataset.jsonl", help="Output JSONL file")
    parser.add_argument("--max-crawled-per-domain", type=int, default=100, help="Max docs per domain")
    parser.add_argument("--max-total", type=int, default=50000, help="Max total examples")
    
    args = parser.parse_args()
    
    prepare_comprehensive_dataset(
        crawled_dir=Path(args.crawled_dir),
        knowledge_dir=Path(args.knowledge_dir),
        existing_data_dir=Path(args.existing_data),
        output_file=Path(args.output),
        max_crawled_per_domain=args.max_crawled_per_domain,
        max_total_examples=args.max_total
    )
