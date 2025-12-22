"""
Synthetic Data Distillation: Text to Teacher to Training

Convert your local .txt files into a fine-tuned expert model.

The Workflow:
1. Chunk your .txt file
2. Generate Q&A pairs using teacher (DeepSeek-R1)
3. Validate Q&A pairs with verifier (Claude)
4. Fine-tune local model on golden dataset
5. Deploy specialized expert model

Why this works:
- RAG: Model reads the .txt every query (slow, shallow)
- Distillation: Model memorizes the .txt during training (instant, deep)

Cost: $15-25 total ($10 generation + $5 validation + $10 Vast.ai fine-tune)
Time: 60-90 minutes
Result: Expert model that understands your document
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class TextChunk:
    """A piece of text from the source document"""
    chunk_id: str
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_file: str = ""
    char_count: int = 0


@dataclass
class GeneratedQAPair:
    """Q&A pair generated from a text chunk"""
    qa_id: str
    question: str
    answer: str
    reasoning: str
    source_chunk_id: str
    confidence: float = 0.5
    difficulty: str = "medium"
    tags: List[str] = None
    generated_at: str = ""
    cost_estimate: float = 0.0


@dataclass
class ValidatedQAPair:
    """Q&A pair that has passed validation"""
    qa_id: str
    question: str
    answer: str
    reasoning: str
    source_chunk_id: str
    confidence: float
    difficulty: str
    is_valid: bool
    validation_feedback: str = ""
    verified_at: str = ""
    cost_estimate: float = 0.0


class TextChunker:
    """
    Break down .txt files into semantic chunks.
    
    Strategies:
    - Fixed size (e.g., 500 chars per chunk)
    - Sentence-based (keep sentences together)
    - Section-based (split on headers/markers)
    """
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Characters per chunk
            overlap: Overlap between chunks for context
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(
        self,
        text: str,
        source_file: str = "unknown.txt"
    ) -> List[TextChunk]:
        """
        Break text into chunks with overlap.
        
        Args:
            text: Full text from .txt file
            source_file: Original filename
        
        Returns:
            List of TextChunk objects
        """
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(text), self.chunk_size - self.overlap):
            chunk_text = text[i:i + self.chunk_size]
            
            # Skip tiny chunks
            if len(chunk_text.strip()) < 50:
                continue
            
            chunk = TextChunk(
                chunk_id=f"chunk_{chunk_id:06d}",
                text=chunk_text,
                source_file=source_file,
                char_count=len(chunk_text)
            )
            chunks.append(chunk)
            chunk_id += 1
        
        return chunks
    
    def load_and_chunk(
        self,
        file_path: str,
        chunk_size: Optional[int] = None
    ) -> List[TextChunk]:
        """Load .txt file and chunk it."""
        if chunk_size:
            self.chunk_size = chunk_size
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.chunk_text(text, source_file=Path(file_path).name)


class SyntheticDataDistiller:
    """
    Main orchestrator: Text → Q&A Generation → Validation → Training Data
    
    Pipeline:
    1. Load .txt file
    2. Chunk into semantic pieces
    3. Generate Q&A using teacher (DeepSeek-R1)
    4. Validate using verifier (Claude)
    5. Export golden dataset for fine-tuning
    """
    
    def __init__(
        self,
        teacher_client: Any,           # DeepSeekClient
        validator_client: Any,         # AnthropicClient (Claude)
        output_dir: str = "./distilled_output"
    ):
        """
        Initialize distiller.
        
        Args:
            teacher_client: DeepSeekClient for Q&A generation
            validator_client: AnthropicClient for validation
            output_dir: Where to save outputs
        """
        self.teacher = teacher_client
        self.validator = validator_client
        self.output_dir = output_dir
        self.chunker = TextChunker()
        
        os.makedirs(output_dir, exist_ok=True)
    
    # ========================================================================
    # STEP 1: Load and Chunk Text
    # ========================================================================
    
    def load_document(self, file_path: str) -> Tuple[str, List[TextChunk]]:
        """
        Load .txt file and chunk it.
        
        Args:
            file_path: Path to .txt file
        
        Returns:
            (full_text, list_of_chunks)
        """
        print(f"\n{'='*70}")
        print(f"STEP 1: Load and Chunk Document")
        print(f"{'='*70}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load text
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        print(f"Loaded: {file_path}")
        print(f"Size: {len(full_text):,} characters")
        
        # Chunk
        chunks = self.chunker.load_and_chunk(file_path)
        
        print(f"Chunked into: {len(chunks)} semantic pieces")
        print(f"Avg chunk size: {len(full_text) // len(chunks):,} chars")
        
        return full_text, chunks
    
    # ========================================================================
    # STEP 2: Generate Q&A Pairs (DeepSeek-R1, ~$10 for 2,000 pairs)
    # ========================================================================
    
    def generate_qa_pairs(
        self,
        chunks: List[TextChunk],
        questions_per_chunk: int = 5,
        budget: float = 10.0
    ) -> List[GeneratedQAPair]:
        """
        Generate Q&A pairs from text chunks using DeepSeek-R1.
        
        Strategy:
        - 5 questions per chunk (5 * 400 chunks = 2,000 pairs)
        - Cost: ~$10 for 2,000 pairs at $0.005 per pair
        - DeepSeek-R1 provides reasoning chains
        
        Args:
            chunks: Text chunks to generate Q&A from
            questions_per_chunk: How many Q&A per chunk
            budget: Budget allocation (~$10)
        
        Returns:
            List of generated Q&A pairs
        """
        print(f"\n{'='*70}")
        print("STEP 2: Generate Q&A Pairs (DeepSeek-R1)")
        print(f"{'='*70}")
        print(f"Budget: ${budget} | Target: {len(chunks) * questions_per_chunk} pairs")
        print(f"Cost/pair: ${budget / (len(chunks) * questions_per_chunk):.6f}")
        
        qa_pairs = []
        estimated_cost = 0.0
        chunk_idx = 0
        
        generation_prompt = """You are an expert educator creating training data.

Read this text section:

---
{text_chunk}
---

Generate {num_questions} complex, realistic questions that someone might ask about this content.

For EACH question:
1. Write a natural question (how a user would ask it)
2. Provide the detailed answer based on the text
3. Show your reasoning (why this is correct)
4. Estimate difficulty (easy/medium/hard)

Format as JSON array:
[
  {{
    "question": "What is...",
    "answer": "The answer is...",
    "reasoning": "Here's why: ...",
    "difficulty": "medium"
  }},
  ...
]

Important:
- Do NOT make up information
- Ground everything in the provided text
- Make questions diverse (not all similar)
- Include edge cases and combinations"""
        
        for chunk in chunks:
            try:
                prompt = generation_prompt.format(
                    text_chunk=chunk.text[:1500],  # Truncate for cost
                    num_questions=questions_per_chunk
                )
                
                # Call DeepSeek-R1
                response = self.teacher.complete(
                    prompt=prompt,
                    model="deepseek-r1",
                    temperature=0.7,
                    max_tokens=1200
                )
                
                # Parse response
                try:
                    content = response.get("content", "[]")
                    # Extract JSON from response (may have markdown wrapping)
                    import re
                    json_match = re.search(r'\[[\s\S]*\]', content)
                    if json_match:
                        qa_list = json.loads(json_match.group())
                    else:
                        qa_list = json.loads(content)
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"  Warning: Failed to parse JSON for chunk {chunk.chunk_id}: {e}")
                    continue
                
                # Convert to GeneratedQAPair objects
                for qa_idx, qa in enumerate(qa_list):
                    pair = GeneratedQAPair(
                        qa_id=f"{chunk.chunk_id}_qa_{qa_idx}",
                        question=qa.get("question", ""),
                        answer=qa.get("answer", ""),
                        reasoning=qa.get("reasoning", ""),
                        source_chunk_id=chunk.chunk_id,
                        confidence=0.7,
                        difficulty=qa.get("difficulty", "medium"),
                        tags=[],
                        generated_at=datetime.now().isoformat(),
                        cost_estimate=response.get("usage", {}).get("estimated_cost", 0.0) / max(1, len(qa_list))
                    )
                    qa_pairs.append(pair)
                    estimated_cost += pair.cost_estimate
                
                chunk_idx += 1
                if chunk_idx % 50 == 0:
                    print(f"  Generated {len(qa_pairs)}/{len(chunks)*questions_per_chunk} | Cost: ${estimated_cost:.2f}")
                
                if estimated_cost >= budget * 0.95:
                    print(f"  Reached budget at chunk {chunk_idx}")
                    break
            
            except Exception as e:
                print(f"  Error on chunk {chunk.chunk_id}: {e}")
                continue
        
        # Save generated pairs
        qa_file = os.path.join(self.output_dir, "generated_qa_pairs.jsonl")
        with open(qa_file, "w") as f:
            for pair in qa_pairs:
                f.write(json.dumps({
                    "qa_id": pair.qa_id,
                    "question": pair.question,
                    "answer": pair.answer,
                    "reasoning": pair.reasoning,
                    "source_chunk_id": pair.source_chunk_id,
                    "confidence": pair.confidence,
                    "difficulty": pair.difficulty,
                    "cost_estimate": pair.cost_estimate,
                }) + "\n")
        
        print(f"\n✓ Generated {len(qa_pairs)} Q&A pairs")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Saved: {qa_file}")
        
        return qa_pairs
    
    # ========================================================================
    # STEP 3: Validate Q&A Pairs (Claude, ~$5 for validation)
    # ========================================================================
    
    def validate_qa_pairs(
        self,
        qa_pairs: List[GeneratedQAPair],
        full_text: str,
        sample_rate: float = 0.5,  # Validate 50%
        budget: float = 5.0
    ) -> Tuple[List[ValidatedQAPair], float]:
        """
        Validate Q&A pairs against original text using Claude.
        
        Strategy:
        - Validate 50% of pairs (cheaper than validating all)
        - Claude checks: Is answer grounded in text? No hallucinations?
        - Filter out bad pairs
        - Cost: ~$5 for 500-1000 validations
        
        Args:
            qa_pairs: Generated Q&A pairs
            full_text: Original full text (for reference)
            sample_rate: Fraction to validate (0.5 = 50%)
            budget: Budget allocation (~$5)
        
        Returns:
            (validated_pairs, approval_rate)
        """
        print(f"\n{'='*70}")
        print("STEP 3: Validate Q&A Pairs (Claude 3.5 Sonnet)")
        print(f"{'='*70}")
        
        # Sample pairs
        sample_size = max(100, int(len(qa_pairs) * sample_rate))
        sample_size = min(sample_size, len(qa_pairs))
        sampled_pairs = random.sample(qa_pairs, sample_size)
        
        print(f"Budget: ${budget} | Input: {len(qa_pairs)} pairs")
        print(f"Sampling: {sample_size} for validation ({sample_rate*100:.0f}%)")
        
        validation_prompt = """You are a quality control validator for training data.

REFERENCE TEXT (excerpt):
{reference_text}

QUESTION & ANSWER TO VALIDATE:
Q: {question}
A: {answer}

VALIDATION CHECKLIST:
1. Is the answer grounded in the provided text? (yes/no)
2. Does the answer avoid hallucination? (yes/no)
3. Is the answer complete and accurate? (yes/no)
4. Are there any factual errors? (describe)

Respond ONLY in JSON:
{{
  "grounded": true/false,
  "no_hallucination": true/false,
  "complete": true/false,
  "approved": true/false,
  "errors": "string or null",
  "confidence": 0.0-1.0
}}"""
        
        validated = []
        estimated_cost = 0.0
        approved_count = 0
        
        for idx, pair in enumerate(sampled_pairs):
            try:
                # Get reference text snippet (find answer in full text)
                ref_idx = full_text.lower().find(pair.answer[:100].lower())
                if ref_idx >= 0:
                    ref_start = max(0, ref_idx - 200)
                    ref_end = min(len(full_text), ref_idx + 500)
                    reference_text = full_text[ref_start:ref_end]
                else:
                    reference_text = full_text[:500]
                
                prompt = validation_prompt.format(
                    reference_text=reference_text[:800],
                    question=pair.question,
                    answer=pair.answer[:500]
                )
                
                # Call Claude
                response = self.validator.complete(
                    prompt=prompt,
                    model="claude-3-5-sonnet",
                    temperature=0.1,
                    max_tokens=300
                )
                
                try:
                    validation = json.loads(response.get("content", "{}"))
                except json.JSONDecodeError:
                    validation = {"approved": False, "errors": "Parse error"}
                
                is_valid = validation.get("approved", False)
                if is_valid:
                    approved_count += 1
                
                validated_pair = ValidatedQAPair(
                    qa_id=pair.qa_id,
                    question=pair.question,
                    answer=pair.answer,
                    reasoning=pair.reasoning,
                    source_chunk_id=pair.source_chunk_id,
                    confidence=pair.confidence,
                    difficulty=pair.difficulty,
                    is_valid=is_valid,
                    validation_feedback=validation.get("errors", ""),
                    verified_at=datetime.now().isoformat(),
                    cost_estimate=response.get("usage", {}).get("estimated_cost", 0.0)
                )
                
                estimated_cost += validated_pair.cost_estimate
                validated.append(validated_pair)
                
                if (idx + 1) % 100 == 0:
                    print(f"  Validated {idx + 1}/{sample_size} | Approved: {approved_count} | Cost: ${estimated_cost:.2f}")
                
                if estimated_cost >= budget * 0.95:
                    print(f"  Reached budget at {idx + 1} validations")
                    break
            
            except Exception as e:
                print(f"  Error validating {pair.qa_id}: {e}")
                continue
        
        # Save validated pairs
        validated_file = os.path.join(self.output_dir, "validated_qa_pairs.jsonl")
        with open(validated_file, "w") as f:
            for pair in validated:
                if pair.is_valid:  # Only save approved pairs
                    f.write(json.dumps({
                        "qa_id": pair.qa_id,
                        "question": pair.question,
                        "answer": pair.answer,
                        "reasoning": pair.reasoning,
                        "source_chunk_id": pair.source_chunk_id,
                        "difficulty": pair.difficulty,
                        "validated": True,
                        "cost_estimate": pair.cost_estimate,
                    }) + "\n")
        
        approval_rate = approved_count / max(1, len(validated))
        
        print(f"\n✓ Validated {len(validated)} pairs")
        print(f"  Approved: {approved_count} ({approval_rate*100:.1f}%)")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Saved: {validated_file}")
        
        return validated, approval_rate
    
    # ========================================================================
    # STEP 4: Export Golden Dataset (Ready for Fine-Tuning)
    # ========================================================================
    
    def export_golden_dataset(
        self,
        validated_pairs: List[ValidatedQAPair],
        format: str = "jsonl"
    ) -> str:
        """
        Export golden dataset in format ready for fine-tuning.
        
        Formats:
        - jsonl: One training example per line
        - alpaca: Instruction/input/output format
        - llama-factory: Conversation format
        
        Args:
            validated_pairs: Validated Q&A pairs
            format: Export format
        
        Returns:
            Path to exported file
        """
        print(f"\n{'='*70}")
        print("STEP 4: Export Golden Dataset")
        print(f"{'='*70}")
        
        # Keep only approved pairs
        approved = [p for p in validated_pairs if p.is_valid]
        
        if format == "jsonl":
            output_file = os.path.join(self.output_dir, "golden_dataset.jsonl")
            with open(output_file, "w") as f:
                for pair in approved:
                    f.write(json.dumps({
                        "instruction": pair.question,
                        "input": "",
                        "output": pair.answer,
                        "reasoning": pair.reasoning,
                        "difficulty": pair.difficulty,
                        "source": pair.source_chunk_id,
                    }) + "\n")
        
        elif format == "alpaca":
            output_file = os.path.join(self.output_dir, "golden_dataset_alpaca.jsonl")
            with open(output_file, "w") as f:
                for pair in approved:
                    f.write(json.dumps({
                        "instruction": pair.question,
                        "input": "",
                        "output": pair.answer,
                    }) + "\n")
        
        elif format == "llama-factory":
            output_file = os.path.join(self.output_dir, "golden_dataset_llama.jsonl")
            with open(output_file, "w") as f:
                for pair in approved:
                    f.write(json.dumps({
                        "messages": [
                            {"role": "user", "content": pair.question},
                            {"role": "assistant", "content": pair.answer}
                        ]
                    }) + "\n")
        
        print(f"✓ Exported {len(approved)} golden pairs")
        print(f"  Format: {format}")
        print(f"  Saved: {output_file}")
        
        return output_file
    
    # ========================================================================
    # RUN FULL PIPELINE
    # ========================================================================
    
    def distill_document(
        self,
        file_path: str,
        questions_per_chunk: int = 5,
        generation_budget: float = 10.0,
        validation_budget: float = 5.0
    ) -> Dict[str, Any]:
        """
        Run complete distillation pipeline: Text → Q&A → Validation → Golden Dataset.
        
        Flow:
        1. Load and chunk .txt file
        2. Generate Q&A pairs using DeepSeek-R1 ($10)
        3. Validate pairs using Claude ($5)
        4. Export golden dataset for fine-tuning
        
        Args:
            file_path: Path to .txt file
            questions_per_chunk: Q&A generated per chunk
            generation_budget: Budget for generation ($10)
            validation_budget: Budget for validation ($5)
        
        Returns:
            Dictionary with results and metrics
        """
        print(f"\n{'='*70}")
        print("SYNTHETIC DATA DISTILLATION: Text to Training Data")
        print(f"{'='*70}")
        print(f"Total Budget: ${generation_budget + validation_budget}")
        
        import time
        start_time = time.time()
        
        # Step 1: Load and chunk
        full_text, chunks = self.load_document(file_path)
        
        # Step 2: Generate Q&A
        qa_pairs = self.generate_qa_pairs(
            chunks=chunks,
            questions_per_chunk=questions_per_chunk,
            budget=generation_budget
        )
        
        if not qa_pairs:
            print("✗ No Q&A pairs generated")
            return {}
        
        # Step 3: Validate
        validated_pairs, approval_rate = self.validate_qa_pairs(
            qa_pairs=qa_pairs,
            full_text=full_text,
            sample_rate=0.5,
            budget=validation_budget
        )
        
        # Step 4: Export
        golden_file = self.export_golden_dataset(validated_pairs, format="jsonl")
        
        elapsed = time.time() - start_time
        
        # Summary
        print(f"\n{'='*70}")
        print("DISTILLATION COMPLETE ✓")
        print(f"{'='*70}")
        print(f"\nRESULTS:")
        print(f"  Input: {len(full_text):,} characters from {Path(file_path).name}")
        print(f"  Chunks: {len(chunks)}")
        print(f"  Q&A Generated: {len(qa_pairs)}")
        print(f"  Q&A Validated: {len(validated_pairs)}")
        print(f"  Golden Approved: {len([p for p in validated_pairs if p.is_valid])}")
        print(f"  Approval Rate: {approval_rate*100:.1f}%")
        print(f"  Time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
        print(f"\nOUTPUT:")
        print(f"  Golden Dataset: {golden_file}")
        print(f"  Ready for fine-tuning!")
        
        return {
            "input_file": file_path,
            "input_size": len(full_text),
            "chunks": len(chunks),
            "qa_generated": len(qa_pairs),
            "qa_validated": len(validated_pairs),
            "golden_approved": len([p for p in validated_pairs if p.is_valid]),
            "approval_rate": approval_rate,
            "golden_dataset_file": golden_file,
            "elapsed_seconds": elapsed,
        }
