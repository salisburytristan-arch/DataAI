"""
End-to-End: Text → Q&A → Validation → Fine-Tuned Expert Model

This orchestrates all 4 steps:
  Step 1: Load .txt file
  Step 2: Generate Q&A pairs (DeepSeek Teacher)
  Step 3: Validate pairs (Claude Verifier)
  Step 4: Fine-tune 7B model on Vast.ai 4090

Result: A specialized expert model that UNDERSTANDS your document
(not just looks it up like RAG)
"""

import os
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class E2EMetrics:
    """Track entire pipeline metrics"""
    start_time: float = 0.0
    step1_time: float = 0.0
    step2_time: float = 0.0
    step3_time: float = 0.0
    step4_time: float = 0.0
    
    step1_cost: float = 0.0
    step2_cost: float = 0.0
    step3_cost: float = 0.0
    step4_cost: float = 0.0
    
    total_qa_generated: int = 0
    total_qa_validated: int = 0
    validation_approval_rate: float = 0.0


class TextToExpertModelOrchestrator:
    """
    Complete pipeline: Text file → Fine-tuned expert model
    
    Workflow:
    1. Load & chunk .txt
    2. Generate Q&A (DeepSeek, "Read section, generate 5 complex Q&A")
    3. Validate Q&A (Claude, "Is this factually accurate?")
    4. Fine-tune 7B (Vast.ai 4090, "Learn this golden dataset")
    """
    
    def __init__(
        self,
        teacher_client: Any,           # DeepSeekClient
        validator_client: Any,         # AnthropicClient
        vast_provisioner: Any,         # VastProvisioner (optional)
        output_dir: str = "./expert_model"
    ):
        self.teacher = teacher_client
        self.validator = validator_client
        self.provisioner = vast_provisioner
        self.output_dir = output_dir
        self.metrics = E2EMetrics()
        
        os.makedirs(output_dir, exist_ok=True)
        self.metrics.start_time = time.time()
    
    # ========================================================================
    # STEP 1: Load & Chunk Text
    # ========================================================================
    
    def step_1_load_chunk_text(self, file_path: str) -> Dict[str, Any]:
        """
        Step 1: Load .txt file and chunk semantically
        
        Input: manual.txt (5MB medical protocol)
        Output: 400+ chunks ready for Q&A generation
        Cost: FREE
        Time: <1 second
        """
        print(f"\n{'='*70}")
        print("STEP 1: Load & Chunk Text")
        print(f"{'='*70}")
        
        step_start = time.time()
        
        # Load text
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        print(f"✓ Loaded: {Path(file_path).name}")
        print(f"  Size: {len(full_text):,} characters")
        
        # Chunk semantically (800 chars with 100 overlap)
        chunks = []
        chunk_size = 800
        overlap = 100
        
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk_text = full_text[i:i + chunk_size]
            if len(chunk_text.strip()) < 50:
                continue
            chunks.append({
                "id": f"chunk_{len(chunks):06d}",
                "text": chunk_text,
                "char_count": len(chunk_text)
            })
        
        print(f"✓ Chunked: {len(chunks)} semantic pieces")
        print(f"  Avg: {len(full_text) // len(chunks):,} chars/chunk")
        
        step_time = time.time() - step_start
        self.metrics.step1_time = step_time
        
        # Save chunks
        chunks_file = os.path.join(self.output_dir, "chunks.jsonl")
        with open(chunks_file, "w") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")
        
        print(f"✓ Saved: {chunks_file}")
        print(f"  Time: {step_time:.1f}s")
        
        return {
            "file_path": file_path,
            "full_text": full_text,
            "chunks": chunks,
            "chunks_file": chunks_file,
        }
    
    # ========================================================================
    # STEP 2: Generate Q&A Pairs (Teacher Loop)
    # ========================================================================
    
    def step_2_generate_qa_pairs(
        self,
        chunks: list,
        full_text: str,
        questions_per_chunk: int = 5,
        budget: float = 10.0
    ) -> Dict[str, Any]:
        """
        Step 2: Generate Q&A pairs using DeepSeek Teacher
        
        Input: 400 chunks
        Teacher Prompt: "Read this section. Generate 5 complex scenarios 
                         that a user might ask, with reasoning-heavy answers."
        Output: 2,000 Q&A pairs (REASONING TRACES)
        Cost: ~$10 ($0.005/pair)
        Time: 10-15 minutes
        
        Example:
          Text: "Section 4.1: Use 5mg of X for Y."
          Teacher: Q: "Patient has Y, what helps?"
                   A: "Protocol 4.1 says use 5mg of X. This treats Y by..."
                   R: "This matches Section 4.1 which specifically..."
        """
        print(f"\n{'='*70}")
        print("STEP 2: Generate Q&A Pairs (DeepSeek Teacher)")
        print(f"{'='*70}")
        
        step_start = time.time()
        
        print(f"✓ Input: {len(chunks)} chunks")
        print(f"✓ Target: {len(chunks) * questions_per_chunk} Q&A pairs")
        print(f"✓ Budget: ${budget}")
        
        qa_pairs = []
        estimated_cost = 0.0
        
        generation_prompt = """You are creating training data from technical documentation.

Read this section:

---
{chunk_text}
---

Generate {num_questions} COMPLEX, REALISTIC questions a user might ask about this section.

For EACH question:
1. Write natural question (as user would ask it)
2. Provide detailed answer grounded in the text
3. Show your reasoning (why this answer is correct)
4. Rate difficulty: easy/medium/hard

Format as JSON array - NO MARKDOWN:
[
  {{
    "question": "When should we use this protocol?",
    "answer": "This protocol applies when... (detailed answer from text)",
    "reasoning": "The text states in section X that... Therefore...",
    "difficulty": "medium"
  }},
  ...
]

CRITICAL: Do NOT make up information. Only use what's in the provided text."""
        
        for idx, chunk in enumerate(chunks):
            try:
                prompt = generation_prompt.format(
                    chunk_text=chunk["text"][:1500],
                    num_questions=questions_per_chunk
                )
                
                # Call DeepSeek-R1 (the reasoning model)
                response = self.teacher.complete(
                    prompt=prompt,
                    model="deepseek-r1",
                    temperature=0.7,
                    max_tokens=1200
                )
                
                # Parse JSON response
                try:
                    import re
                    content = response.get("content", "[]")
                    json_match = re.search(r'\[[\s\S]*\]', content)
                    if json_match:
                        qa_list = json.loads(json_match.group())
                    else:
                        qa_list = json.loads(content)
                except:
                    print(f"  Warning: Parse error on chunk {idx}")
                    continue
                
                # Add to collection
                for qa_idx, qa in enumerate(qa_list):
                    pair = {
                        "qa_id": f"{chunk['id']}_qa_{qa_idx}",
                        "question": qa.get("question", ""),
                        "answer": qa.get("answer", ""),
                        "reasoning": qa.get("reasoning", ""),
                        "difficulty": qa.get("difficulty", "medium"),
                        "source_chunk": chunk["id"],
                    }
                    qa_pairs.append(pair)
                    estimated_cost += response.get("usage", {}).get("estimated_cost", 0.0) / max(1, len(qa_list))
                
                if (idx + 1) % 50 == 0:
                    print(f"  Generated {len(qa_pairs):,} pairs | Cost: ${estimated_cost:.2f}")
                
                if estimated_cost >= budget * 0.95:
                    print(f"  Reached budget at chunk {idx + 1}")
                    break
            
            except Exception as e:
                print(f"  Error chunk {idx}: {e}")
                continue
        
        # Save Q&A pairs
        qa_file = os.path.join(self.output_dir, "generated_qa_pairs.jsonl")
        with open(qa_file, "w") as f:
            for pair in qa_pairs:
                f.write(json.dumps(pair) + "\n")
        
        step_time = time.time() - step_start
        self.metrics.step2_time = step_time
        self.metrics.step2_cost = estimated_cost
        self.metrics.total_qa_generated = len(qa_pairs)
        
        print(f"\n✓ Generated: {len(qa_pairs):,} Q&A pairs")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Time: {step_time/60:.1f} minutes")
        print(f"  Saved: {qa_file}")
        
        return {
            "qa_pairs": qa_pairs,
            "qa_file": qa_file,
            "cost": estimated_cost,
        }
    
    # ========================================================================
    # STEP 3: Validate Q&A Pairs (Verifier Loop)
    # ========================================================================
    
    def step_3_validate_qa_pairs(
        self,
        qa_pairs: list,
        full_text: str,
        budget: float = 5.0
    ) -> Dict[str, Any]:
        """
        Step 3: Validate Q&A using Claude Verifier
        
        Input: 2,000 Q&A pairs
        Verifier Prompt: "Is this Q&A factually accurate based on the text?
                          Any hallucinations? Grade: Y/N"
        Output: Filtered "Gold Dataset" (80-90% approval rate)
        Cost: ~$5
        Time: 5-10 minutes
        
        Result: Filter out hallucinations, keep only verified pairs
        """
        print(f"\n{'='*70}")
        print("STEP 3: Validate Q&A Pairs (Claude Verifier)")
        print(f"{'='*70}")
        
        step_start = time.time()
        
        # Validate 50% sample (cheaper, still effective)
        import random
        sample_size = max(100, int(len(qa_pairs) * 0.5))
        sample_size = min(sample_size, len(qa_pairs))
        sampled = random.sample(qa_pairs, sample_size)
        
        print(f"✓ Input: {len(qa_pairs):,} Q&A pairs")
        print(f"✓ Validating: {sample_size} pairs (50% sample)")
        print(f"✓ Budget: ${budget}")
        
        validation_prompt = """You are a quality control verifier for training data.

TEXT EXCERPT:
{text_excerpt}

Q&A PAIR TO VALIDATE:
Q: {question}
A: {answer}

VERIFICATION:
1. Is answer grounded in the text? (yes/no)
2. Does answer avoid hallucination? (yes/no)
3. Is answer complete? (yes/no)

Respond ONLY in JSON - no explanation:
{{
  "grounded": true/false,
  "no_hallucination": true/false,
  "complete": true/false,
  "approved": true/false
}}"""
        
        validated = []
        estimated_cost = 0.0
        approved_count = 0
        
        for idx, pair in enumerate(sampled):
            try:
                # Find text excerpt containing answer
                answer_snippet = pair["answer"][:100]
                ref_idx = full_text.lower().find(answer_snippet.lower())
                if ref_idx >= 0:
                    ref_start = max(0, ref_idx - 200)
                    ref_end = min(len(full_text), ref_idx + 500)
                    text_excerpt = full_text[ref_start:ref_end]
                else:
                    text_excerpt = full_text[:500]
                
                prompt = validation_prompt.format(
                    text_excerpt=text_excerpt[:800],
                    question=pair["question"],
                    answer=pair["answer"][:500]
                )
                
                # Call Claude 3.5 Sonnet (the verifier)
                response = self.validator.complete(
                    prompt=prompt,
                    model="claude-3-5-sonnet",
                    temperature=0.1,  # Deterministic
                    max_tokens=300
                )
                
                try:
                    validation = json.loads(response.get("content", "{}"))
                except:
                    validation = {"approved": False}
                
                is_approved = validation.get("approved", False)
                if is_approved:
                    approved_count += 1
                    validated.append({**pair, "validated": True})
                
                estimated_cost += response.get("usage", {}).get("estimated_cost", 0.0)
                
                if (idx + 1) % 100 == 0:
                    print(f"  Validated {idx + 1}/{sample_size} | Approved: {approved_count}")
                
                if estimated_cost >= budget * 0.95:
                    break
            
            except Exception as e:
                print(f"  Error validating pair {idx}: {e}")
                continue
        
        # Save validated pairs
        validated_file = os.path.join(self.output_dir, "golden_dataset.jsonl")
        with open(validated_file, "w") as f:
            for pair in validated:
                # Format for fine-tuning
                f.write(json.dumps({
                    "instruction": pair["question"],
                    "input": "",
                    "output": pair["answer"],
                    "reasoning": pair["reasoning"],
                    "difficulty": pair["difficulty"],
                }) + "\n")
        
        step_time = time.time() - step_start
        self.metrics.step3_time = step_time
        self.metrics.step3_cost = estimated_cost
        self.metrics.total_qa_validated = len(validated)
        self.metrics.validation_approval_rate = approved_count / max(1, len(sampled))
        
        print(f"\n✓ Validated: {len(sampled)} pairs")
        print(f"  Approved: {approved_count} ({self.metrics.validation_approval_rate*100:.1f}%)")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Time: {step_time/60:.1f} minutes")
        print(f"  Saved: {validated_file}")
        
        return {
            "golden_dataset": validated,
            "golden_dataset_file": validated_file,
            "approval_rate": self.metrics.validation_approval_rate,
        }
    
    # ========================================================================
    # STEP 4: Fine-Tune Model on Vast.ai
    # ========================================================================
    
    def step_4_fine_tune_on_vast(
        self,
        golden_dataset_file: str,
        model_name: str = "meta-llama/Llama-2-7b-hf",
        num_epochs: int = 2,
        budget: float = 20.0
    ) -> Dict[str, Any]:
        """
        Step 4: Fine-tune 7B model on Vast.ai 4090
        
        Input: golden_dataset.jsonl (900-1000 verified Q&A pairs)
        Model: Llama-2-7b or Mistral-7b
        GPU: RTX 4090 ($0.30-0.50/hour)
        Duration: 30-60 minutes for 2 epochs
        Cost: ~$15-25
        
        Result: Specialized expert model that UNDERSTANDS the document
                (can reason, combine rules, catch edge cases)
                NOT just lookup/RAG
        """
        print(f"\n{'='*70}")
        print("STEP 4: Fine-Tune Model on Vast.ai")
        print(f"{'='*70}")
        
        if not self.provisioner:
            print("⚠ Vast.ai provisioner not configured")
            print("  Skipping GPU training (you can run this manually)")
            print(f"  Dataset ready: {golden_dataset_file}")
            return {"skipped": True}
        
        step_start = time.time()
        
        print(f"✓ Model: {model_name}")
        print(f"✓ Dataset: {golden_dataset_file}")
        print(f"✓ Epochs: {num_epochs}")
        print(f"✓ Budget: ${budget}")
        
        try:
            # Search for cheapest 4090
            print("\n  Finding cheapest 4090 instance...")
            instances = self.provisioner.search_instances(
                gpu_types=["RTX 4090"],
                min_vram=24,
                max_price=0.50
            )
            
            if not instances:
                print("  ✗ No available instances found")
                return {"error": "No instances available"}
            
            best = instances[0]
            print(f"  ✓ Found: {best['gpu_name']} @ ${best['dph_total']}/hour")
            
            # Provision instance
            print(f"\n  Provisioning instance {best['id']}...")
            instance = self.provisioner.provision(
                machine_id=best['id'],
                vllm_model=model_name,
                name_prefix="acx-expert-trainer"
            )
            
            print(f"  ✓ Instance launched: {instance.instance_id}")
            
            # Setup SSH tunnel
            print(f"  Setting up SSH tunnel...")
            self.provisioner.setup_ssh_tunnel(instance)
            print(f"  ✓ Tunnel ready")
            
            # Upload dataset
            print(f"\n  Uploading dataset...")
            subprocess.run([
                "scp", "-P", "2222", "-r",
                golden_dataset_file,
                f"root@localhost:~/dataset.jsonl"
            ], check=True)
            print(f"  ✓ Dataset uploaded")
            
            # Training script
            training_script = f"""#!/bin/bash
cd /root
pip install -q llama-factory

llamafactory-cli train \\
  --model_name_or_path {model_name} \\
  --dataset_path ./dataset.jsonl \\
  --output_dir ./arcticcodex-expert \\
  --num_epochs {num_epochs} \\
  --learning_rate 1e-4 \\
  --batch_size 4 \\
  --bf16 \\
  --max_steps 1000 \\
  --save_strategy steps \\
  --save_steps 100

echo "Training complete!"
"""
            
            # Run training
            print(f"\n  Starting fine-tuning (this may take 30-60 min)...")
            start_train = time.time()
            
            # Write and execute training script
            with open("/tmp/train.sh", "w") as f:
                f.write(training_script)
            
            result = subprocess.run([
                "ssh", "-p", "2222", "root@localhost",
                "bash", "-s"
            ], stdin=open("/tmp/train.sh"), capture_output=True, text=True)
            
            train_time = time.time() - start_train
            
            if result.returncode == 0:
                print(f"  ✓ Training complete!")
                print(f"    Time: {train_time/60:.1f} minutes")
                
                # Download trained model
                print(f"\n  Downloading trained model...")
                subprocess.run([
                    "scp", "-P", "2222", "-r",
                    "root@localhost:~/arcticcodex-expert",
                    os.path.join(self.output_dir, "arcticcodex-expert")
                ])
                print(f"  ✓ Model saved to {self.output_dir}/arcticcodex-expert")
            else:
                print(f"  ✗ Training failed:")
                print(result.stderr)
            
            # Cleanup
            print(f"\n  Cleaning up instance...")
            self.provisioner.destroy_instance(instance.instance_id)
            print(f"  ✓ Instance destroyed")
            
            # Calculate actual cost
            train_hours = train_time / 3600
            actual_cost = train_hours * best['dph_total']
            
            step_time = time.time() - step_start
            self.metrics.step4_time = step_time
            self.metrics.step4_cost = actual_cost
            
            return {
                "success": True,
                "model_path": os.path.join(self.output_dir, "arcticcodex-expert"),
                "training_time": train_time,
                "cost": actual_cost,
                "gpu_hours": train_hours,
            }
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # RUN COMPLETE PIPELINE
    # ========================================================================
    
    def run_complete_pipeline(
        self,
        file_path: str,
        questions_per_chunk: int = 5,
        fine_tune: bool = True
    ) -> Dict[str, Any]:
        """
        Execute all 4 steps end-to-end:
        
        1. Load & chunk text file
        2. Generate Q&A (DeepSeek teacher)
        3. Validate Q&A (Claude verifier)
        4. Fine-tune 7B model (Vast.ai 4090)
        
        Result: Expert model that understands your document
        """
        print(f"\n{'='*70}")
        print("TEXT → TEACHER → TRAINING → EXPERT MODEL")
        print(f"{'='*70}")
        print(f"Total pipeline time: ~2-3 hours")
        print(f"Total cost: ~$30-40 (without fine-tune: $15-20)")
        
        # STEP 1
        step1_result = self.step_1_load_chunk_text(file_path)
        
        # STEP 2
        step2_result = self.step_2_generate_qa_pairs(
            chunks=step1_result["chunks"],
            full_text=step1_result["full_text"],
            questions_per_chunk=questions_per_chunk,
        )
        
        # STEP 3
        step3_result = self.step_3_validate_qa_pairs(
            qa_pairs=step2_result["qa_pairs"],
            full_text=step1_result["full_text"],
        )
        
        # STEP 4 (optional)
        step4_result = {}
        if fine_tune and self.provisioner:
            step4_result = self.step_4_fine_tune_on_vast(
                golden_dataset_file=step3_result["golden_dataset_file"]
            )
        
        # SUMMARY
        total_time = time.time() - self.metrics.start_time
        total_cost = (self.metrics.step2_cost + 
                     self.metrics.step3_cost + 
                     self.metrics.step4_cost)
        
        print(f"\n{'='*70}")
        print("PIPELINE COMPLETE ✓")
        print(f"{'='*70}")
        print(f"\nTIME:")
        print(f"  Step 1 (Load):     {self.metrics.step1_time:.1f}s")
        print(f"  Step 2 (Generate): {self.metrics.step2_time/60:.1f} min")
        print(f"  Step 3 (Validate): {self.metrics.step3_time/60:.1f} min")
        if step4_result and "training_time" in step4_result:
            print(f"  Step 4 (Fine-tune): {step4_result['training_time']/60:.1f} min")
        print(f"  Total:             {total_time/60:.1f} min")
        
        print(f"\nCOST:")
        print(f"  Generation (Step 2): ${self.metrics.step2_cost:.2f}")
        print(f"  Validation (Step 3): ${self.metrics.step3_cost:.2f}")
        if step4_result and "cost" in step4_result:
            print(f"  Fine-tune (Step 4):  ${step4_result['cost']:.2f}")
        print(f"  Total:               ${total_cost:.2f}")
        
        print(f"\nDATA:")
        print(f"  Input file: {Path(file_path).name}")
        print(f"  Q&A generated: {self.metrics.total_qa_generated:,}")
        print(f"  Q&A validated: {self.metrics.total_qa_validated:,}")
        print(f"  Approval rate: {self.metrics.validation_approval_rate*100:.1f}%")
        
        print(f"\nOUTPUTS:")
        print(f"  Golden dataset: {step3_result['golden_dataset_file']}")
        if step4_result and "model_path" in step4_result:
            print(f"  Trained model: {step4_result['model_path']}")
        
        print(f"\nNEXT STEPS:")
        print(f"  1. Model understands your document (not just lookup)")
        print(f"  2. Can reason about combinations of rules")
        print(f"  3. Can catch edge cases")
        print(f"  4. Deploy and test!")
        
        return {
            "status": "complete",
            "metrics": self.metrics,
            "step1": step1_result,
            "step2": step2_result,
            "step3": step3_result,
            "step4": step4_result,
            "total_time": total_time,
            "total_cost": total_cost,
        }
