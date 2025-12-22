"""
Cascade Pipeline: Turn $100 into proprietary model training data

Strategy:
- Stage A (DeepSeek-R1, $25): Generate 9,000-10,000 raw reasoning chains
- Stage B (OpenAI 4o-mini, $25): Clean & format into ForgeNumerics JSON
- Stage C (Anthropic Claude, $25): Validate 10% sample as golden standard
- Reserve: $25 contingency

Output: 10,000 training pairs + 1,000 verified test set
"""

import json
import os
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class CascadeMetrics:
    """Track budget and data flow through cascade"""
    stage_a_cost: float = 0.0
    stage_b_cost: float = 0.0
    stage_c_cost: float = 0.0
    stage_a_samples: int = 0
    stage_b_samples: int = 0
    stage_c_samples: int = 0
    total_budget: float = 100.0
    budget_remaining: float = 100.0


class CascadePipeline:
    """
    Three-stage cascade for generating and validating training data.
    """
    
    def __init__(
        self,
        deepseek_client: Any,           # DeepSeekClient instance
        openai_client: Any,             # OpenAI client
        anthropic_client: Any,          # Anthropic client
        output_dir: str = "./cascade_output"
    ):
        """
        Initialize cascade pipeline with 3 providers.
        
        Args:
            deepseek_client: DeepSeek API client (R1 for reasoning)
            openai_client: OpenAI client (4o-mini for formatting)
            anthropic_client: Anthropic client (Claude for validation)
            output_dir: Where to save outputs at each stage
        """
        self.deepseek = deepseek_client
        self.openai = openai_client
        self.anthropic = anthropic_client
        self.output_dir = output_dir
        self.metrics = CascadeMetrics()
        
        os.makedirs(output_dir, exist_ok=True)
    
    # ========================================================================
    # STAGE A: Generate Raw Ore (DeepSeek-R1, $25)
    # ========================================================================
    
    def stage_a_generate_raw_pairs(
        self,
        num_samples: int = 10000,
        domain: str = "medical",
        budget: float = 25.0
    ) -> List[Dict[str, Any]]:
        """
        Stage A: Use DeepSeek-R1 to generate complex reasoning chains.
        
        Strategy:
        - R1 is 70% cheaper than OpenAI o1 but similar quality reasoning
        - Generate ~10,000 examples with ~$25
        - Output: Raw reasoning traces (messy but brilliant)
        
        Args:
            num_samples: Target number of training pairs (~10,000)
            domain: Problem domain (medical, legal, scientific, etc.)
            budget: Budget allocation for this stage ($25)
        
        Returns:
            List of raw reasoning pairs
        """
        print(f"\n{'='*70}")
        print("STAGE A: Generate Raw Ore (DeepSeek-R1)")
        print(f"{'='*70}")
        print(f"Budget: ${budget} | Target: {num_samples} samples")
        print(f"Avg cost per sample: ${budget / num_samples:.6f}")
        
        raw_pairs = []
        samples_processed = 0
        estimated_cost = 0.0
        
        # Domain-specific prompts for diverse reasoning
        domains = {
            "medical": "Generate a complex medical scenario requiring trinary logic verification. Include diagnosis, treatment options, and risk assessment.",
            "legal": "Generate a complex legal scenario with conflicting precedents. Require trinary logic to resolve ambiguity.",
            "scientific": "Generate a complex scientific hypothesis with supporting/contradicting evidence. Use trinary logic for verification.",
            "financial": "Generate a complex financial decision with multiple constraints and outcomes. Apply trinary logic optimization.",
        }
        
        prompt_template = domains.get(domain, domains["medical"])
        
        # Batch processing for efficiency
        batch_size = 100
        num_batches = (num_samples + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            batch_start = batch_idx * batch_size
            batch_end = min((batch_idx + 1) * batch_size, num_samples)
            batch_size_actual = batch_end - batch_start
            
            print(f"  Batch {batch_idx + 1}/{num_batches} ({batch_start}-{batch_end})...")
            
            # Generate batch via DeepSeek R1
            for sample_idx in range(batch_size_actual):
                try:
                    # Vary prompt slightly for diversity
                    prompt = f"{prompt_template}\n\nSample {samples_processed + 1}: Generate a unique scenario."
                    
                    # Call DeepSeek R1 (assumes OpenAI-compatible interface)
                    response = self.deepseek.complete(
                        prompt=prompt,
                        model="deepseek-r1",
                        temperature=0.7,  # Encourage diversity
                        max_tokens=1500
                    )
                    
                    raw_pair = {
                        "sample_id": f"stage_a_{samples_processed:06d}",
                        "domain": domain,
                        "prompt": prompt,
                        "raw_reasoning": response.get("content", ""),
                        "reasoning_tokens": response.get("usage", {}).get("completion_tokens", 0),
                        "timestamp": datetime.now().isoformat(),
                        "cost_estimate": response.get("usage", {}).get("estimated_cost", 0.0),
                    }
                    
                    estimated_cost += raw_pair["cost_estimate"]
                    raw_pairs.append(raw_pair)
                    samples_processed += 1
                    
                    if samples_processed % 500 == 0:
                        print(f"    Generated {samples_processed}/{num_samples} | Cost so far: ${estimated_cost:.2f}")
                    
                    if estimated_cost >= budget * 0.95:  # Stop at 95% of budget
                        print(f"  Reached budget limit at {samples_processed} samples")
                        break
                
                except Exception as e:
                    print(f"    Error on sample {samples_processed}: {e}")
                    continue
            
            if estimated_cost >= budget * 0.95:
                break
        
        # Save stage A output
        stage_a_file = os.path.join(self.output_dir, "stage_a_raw_pairs.jsonl")
        with open(stage_a_file, "w") as f:
            for pair in raw_pairs:
                f.write(json.dumps(pair) + "\n")
        
        self.metrics.stage_a_cost = estimated_cost
        self.metrics.stage_a_samples = len(raw_pairs)
        self.metrics.budget_remaining -= estimated_cost
        
        print(f"\n✓ Stage A Complete")
        print(f"  Generated: {len(raw_pairs)} samples")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Saved: {stage_a_file}")
        print(f"  Budget remaining: ${self.metrics.budget_remaining:.2f}")
        
        return raw_pairs
    
    # ========================================================================
    # STAGE B: Refine & Format (OpenAI 4o-mini, $25)
    # ========================================================================
    
    def stage_b_format_to_json(
        self,
        raw_pairs: List[Dict[str, Any]],
        budget: float = 25.0
    ) -> List[Dict[str, Any]]:
        """
        Stage B: Use GPT-4o-mini to clean and format into ForgeNumerics JSON.
        
        Strategy:
        - 4o-mini is ultra-cheap ($0.60/1M output tokens)
        - Format DeepSeek output into strict JSON
        - Likely to have budget leftover ($5-10)
        
        Args:
            raw_pairs: Output from Stage A
            budget: Budget allocation for this stage ($25)
        
        Returns:
            List of formatted training pairs ready for ForgeNumerics
        """
        print(f"\n{'='*70}")
        print("STAGE B: Refine & Format (OpenAI 4o-mini)")
        print(f"{'='*70}")
        print(f"Budget: ${budget} | Input: {len(raw_pairs)} samples")
        
        formatted_pairs = []
        estimated_cost = 0.0
        
        formatting_prompt = """You are a data formatter for machine learning training.

Convert this raw reasoning trace into strict JSON format for the ForgeNumerics Validator:

RAW REASONING:
{raw_reasoning}

OUTPUT FORMAT (JSON only, no markdown):
{{
  "instruction": "Clear, concise problem statement",
  "reasoning_chain": "Step-by-step logical deduction",
  "trinary_logic": {{
    "premise_a": "First assertion",
    "premise_b": "Alternative assertion",
    "premise_c": "Third consideration",
    "resolution": "How these resolve to a decision"
  }},
  "confidence": 0.0-1.0,
  "citations": ["key_evidence_1", "key_evidence_2"],
  "metadata": {{
    "domain": "category",
    "difficulty": "easy|medium|hard"
  }}
}}

Respond with ONLY the JSON, no explanation."""
        
        batch_size = 50
        num_batches = (len(raw_pairs) + batch_size - 1) // batch_size
        
        for batch_idx, batch in enumerate([raw_pairs[i:i+batch_size] for i in range(0, len(raw_pairs), batch_size)]):
            print(f"  Batch {batch_idx + 1}/{num_batches} ({len(batch)} samples)...")
            
            for pair in batch:
                try:
                    prompt = formatting_prompt.format(
                        raw_reasoning=pair.get("raw_reasoning", "")[:2000]  # Truncate for cost
                    )
                    
                    # Call GPT-4o-mini
                    response = self.openai.complete(
                        prompt=prompt,
                        model="gpt-4o-mini",
                        temperature=0.2,  # Low temp for consistency
                        max_tokens=500
                    )
                    
                    # Parse JSON response
                    try:
                        formatted_json = json.loads(response.get("content", "{}"))
                    except json.JSONDecodeError:
                        print(f"    Warning: Failed to parse JSON for {pair['sample_id']}")
                        continue
                    
                    formatted_pair = {
                        "sample_id": pair["sample_id"],
                        "source_domain": pair.get("domain", "unknown"),
                        "instruction": formatted_json.get("instruction", ""),
                        "reasoning_chain": formatted_json.get("reasoning_chain", ""),
                        "trinary_logic": formatted_json.get("trinary_logic", {}),
                        "confidence": formatted_json.get("confidence", 0.5),
                        "citations": formatted_json.get("citations", []),
                        "metadata": formatted_json.get("metadata", {}),
                        "cost_estimate": response.get("usage", {}).get("estimated_cost", 0.0),
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    estimated_cost += formatted_pair["cost_estimate"]
                    formatted_pairs.append(formatted_pair)
                    
                    if len(formatted_pairs) % 500 == 0:
                        print(f"    Formatted {len(formatted_pairs)}/{len(raw_pairs)} | Cost: ${estimated_cost:.2f}")
                    
                    if estimated_cost >= budget * 0.95:
                        print(f"  Reached budget at {len(formatted_pairs)} samples")
                        break
                
                except Exception as e:
                    print(f"    Error formatting {pair['sample_id']}: {e}")
                    continue
            
            if estimated_cost >= budget * 0.95:
                break
        
        # Save stage B output
        stage_b_file = os.path.join(self.output_dir, "stage_b_formatted_pairs.jsonl")
        with open(stage_b_file, "w") as f:
            for pair in formatted_pairs:
                f.write(json.dumps(pair) + "\n")
        
        self.metrics.stage_b_cost = estimated_cost
        self.metrics.stage_b_samples = len(formatted_pairs)
        self.metrics.budget_remaining -= estimated_cost
        
        print(f"\n✓ Stage B Complete")
        print(f"  Formatted: {len(formatted_pairs)} samples")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Saved: {stage_b_file}")
        print(f"  Budget remaining: ${self.metrics.budget_remaining:.2f}")
        
        return formatted_pairs
    
    # ========================================================================
    # STAGE C: Golden Standard Check (Anthropic Claude, $25)
    # ========================================================================
    
    def stage_c_validate_golden_set(
        self,
        formatted_pairs: List[Dict[str, Any]],
        sample_rate: float = 0.10,  # Validate 10% (1,000 of 10,000)
        budget: float = 25.0
    ) -> Dict[str, Any]:
        """
        Stage C: Use Claude 3.5 Sonnet as "Supreme Court" validator.
        
        Strategy:
        - Cannot afford to validate all 10,000 with expensive Claude
        - Sample 10% (1,000 examples) randomly
        - These become your golden standard test set
        - Ensures model evaluation is trustworthy
        
        Args:
            formatted_pairs: Output from Stage B
            sample_rate: Fraction to validate (default 10%)
            budget: Budget allocation for this stage ($25)
        
        Returns:
            Dictionary with golden_set and validation_results
        """
        print(f"\n{'='*70}")
        print("STAGE C: Golden Standard Check (Anthropic Claude)")
        print(f"{'='*70}")
        
        # Sample 10% of formatted pairs
        sample_size = max(100, int(len(formatted_pairs) * sample_rate))
        sample_size = min(sample_size, len(formatted_pairs))
        
        sampled_pairs = random.sample(formatted_pairs, sample_size)
        
        print(f"Budget: ${budget} | Input: {len(formatted_pairs)} samples")
        print(f"Sampling: {sample_size} examples ({sample_rate*100:.0f}%)")
        
        validation_prompt = """You are a supreme court validator for training data quality.

Review this reasoning chain and ForgeNumerics trinary logic. Identify any flaws.

INSTRUCTION: {instruction}

REASONING: {reasoning_chain}

TRINARY LOGIC:
- Premise A: {premise_a}
- Premise B: {premise_b}
- Premise C: {premise_c}
- Resolution: {resolution}

VALIDATION TASK:
1. Is the reasoning logically sound? (yes/no)
2. Are the trinary premises exhaustive? (yes/no)
3. Does resolution follow from premises? (yes/no)
4. Any corrections needed? (describe or "none")

Respond in JSON:
{{
  "logically_sound": true/false,
  "premises_exhaustive": true/false,
  "resolution_valid": true/false,
  "corrections": "string or null",
  "approved": true/false,
  "explanation": "brief reason"
}}"""
        
        golden_set = []
        validation_results = []
        estimated_cost = 0.0
        approved_count = 0
        
        for idx, pair in enumerate(sampled_pairs):
            try:
                trinary = pair.get("trinary_logic", {})
                prompt = validation_prompt.format(
                    instruction=pair.get("instruction", "")[:500],
                    reasoning_chain=pair.get("reasoning_chain", "")[:500],
                    premise_a=trinary.get("premise_a", ""),
                    premise_b=trinary.get("premise_b", ""),
                    premise_c=trinary.get("premise_c", ""),
                    resolution=trinary.get("resolution", "")
                )
                
                # Call Claude 3.5 Sonnet
                response = self.anthropic.complete(
                    prompt=prompt,
                    model="claude-3-5-sonnet",
                    temperature=0.1,  # Deterministic validation
                    max_tokens=300
                )
                
                try:
                    validation = json.loads(response.get("content", "{}"))
                except json.JSONDecodeError:
                    validation = {"approved": False, "explanation": "Parse error"}
                
                result = {
                    "sample_id": pair["sample_id"],
                    "validation": validation,
                    "approved": validation.get("approved", False),
                    "corrections": validation.get("corrections"),
                    "cost_estimate": response.get("usage", {}).get("estimated_cost", 0.0),
                }
                
                estimated_cost += result["cost_estimate"]
                validation_results.append(result)
                
                if result["approved"]:
                    approved_count += 1
                    # Add to golden set with validation metadata
                    golden_sample = {**pair, "validation": validation, "golden_approved": True}
                    golden_set.append(golden_sample)
                
                if (idx + 1) % 100 == 0:
                    print(f"  Validated {idx + 1}/{sample_size} | Approved: {approved_count} | Cost: ${estimated_cost:.2f}")
                
                if estimated_cost >= budget * 0.95:
                    print(f"  Reached budget at {idx + 1} validations")
                    break
            
            except Exception as e:
                print(f"    Error validating {pair['sample_id']}: {e}")
                continue
        
        # Save outputs
        golden_file = os.path.join(self.output_dir, "golden_test_set.jsonl")
        with open(golden_file, "w") as f:
            for item in golden_set:
                f.write(json.dumps(item) + "\n")
        
        validation_file = os.path.join(self.output_dir, "validation_results.jsonl")
        with open(validation_file, "w") as f:
            for item in validation_results:
                f.write(json.dumps(item) + "\n")
        
        self.metrics.stage_c_cost = estimated_cost
        self.metrics.stage_c_samples = len(golden_set)
        self.metrics.budget_remaining -= estimated_cost
        
        print(f"\n✓ Stage C Complete")
        print(f"  Validated: {len(validation_results)} samples")
        print(f"  Golden Standard: {len(golden_set)} approved ({approved_count/max(1, len(validation_results))*100:.1f}%)")
        print(f"  Cost: ${estimated_cost:.2f}")
        print(f"  Saved:")
        print(f"    - {golden_file}")
        print(f"    - {validation_file}")
        print(f"  Budget remaining: ${self.metrics.budget_remaining:.2f}")
        
        return {
            "golden_set": golden_set,
            "validation_results": validation_results,
            "approval_rate": approved_count / max(1, len(validation_results))
        }
    
    # ========================================================================
    # RUN FULL CASCADE
    # ========================================================================
    
    def run_full_cascade(
        self,
        num_samples: int = 10000,
        domain: str = "medical"
    ) -> Dict[str, Any]:
        """
        Run complete cascade pipeline from raw generation to golden standard.
        
        Flow:
        1. Stage A: Generate 10,000 raw examples ($25 DeepSeek-R1)
        2. Stage B: Format into JSON ($25 GPT-4o-mini)
        3. Stage C: Validate 1,000 golden examples ($25 Claude)
        
        Args:
            num_samples: Total training samples to generate
            domain: Problem domain for generation
        
        Returns:
            Complete cascade results with all outputs
        """
        print(f"\n{'='*70}")
        print("CASCADE PIPELINE: Turning $100 into Proprietary Model Training Data")
        print(f"{'='*70}")
        print(f"Total Budget: ${self.metrics.total_budget}")
        print(f"Target: {num_samples} training pairs + {int(num_samples*0.1)} golden test set")
        
        start_time = time.time()
        
        # Stage A
        raw_pairs = self.stage_a_generate_raw_pairs(
            num_samples=num_samples,
            domain=domain,
            budget=25.0
        )
        
        if not raw_pairs:
            print("✗ Stage A failed - no samples generated")
            return {}
        
        # Stage B
        formatted_pairs = self.stage_b_format_to_json(
            raw_pairs=raw_pairs,
            budget=25.0
        )
        
        if not formatted_pairs:
            print("✗ Stage B failed - no samples formatted")
            return {}
        
        # Stage C
        golden_results = self.stage_c_validate_golden_set(
            formatted_pairs=formatted_pairs,
            sample_rate=0.10,
            budget=25.0
        )
        
        elapsed = time.time() - start_time
        
        # Summary
        print(f"\n{'='*70}")
        print("CASCADE PIPELINE: COMPLETE ✓")
        print(f"{'='*70}")
        print(f"\nSUMMARY:")
        print(f"  Stage A: {self.metrics.stage_a_samples} raw samples | ${self.metrics.stage_a_cost:.2f}")
        print(f"  Stage B: {self.metrics.stage_b_samples} formatted pairs | ${self.metrics.stage_b_cost:.2f}")
        print(f"  Stage C: {self.metrics.stage_c_samples} golden approved | ${self.metrics.stage_c_cost:.2f}")
        print(f"\nBudget Utilization:")
        print(f"  Total Spent: ${self.metrics.total_budget - self.metrics.budget_remaining:.2f}")
        print(f"  Remaining: ${self.metrics.budget_remaining:.2f} (reserve)")
        print(f"\nTime: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"\nOUTPUTS:")
        print(f"  Training data: {os.path.join(self.output_dir, 'stage_b_formatted_pairs.jsonl')}")
        print(f"  Golden test set: {os.path.join(self.output_dir, 'golden_test_set.jsonl')}")
        print(f"  Validation report: {os.path.join(self.output_dir, 'validation_results.jsonl')}")
        
        return {
            "metrics": self.metrics,
            "stage_a_samples": self.metrics.stage_a_samples,
            "stage_b_samples": self.metrics.stage_b_samples,
            "golden_samples": self.metrics.stage_c_samples,
            "golden_approval_rate": golden_results.get("approval_rate", 0.0),
            "total_cost": self.metrics.total_budget - self.metrics.budget_remaining,
            "output_dir": self.output_dir,
            "elapsed_seconds": elapsed,
        }
