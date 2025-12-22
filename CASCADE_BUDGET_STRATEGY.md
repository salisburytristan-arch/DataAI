# Cascade Pipeline: $100 Budget Strategy

## The Goal
Turn $100 of API credits into a proprietary **10,000-sample training dataset** with a verified golden test set.

---

## Budget Breakdown

| Stage | Provider | Role | Budget | Est. Samples | Cost/Sample | Output |
|-------|----------|------|--------|--------------|-------------|--------|
| A | DeepSeek-R1 | Raw reasoning generation | $25 | 10,000 | $0.0025 | Raw traces |
| B | GPT-4o-mini | JSON formatting | $25 | 10,000 | $0.0025 | Clean JSON |
| C | Claude 3.5 Sonnet | Validation (10% sample) | $25 | 1,000 validated | $0.025 | Golden set |
| Reserve | - | Contingency | $25 | - | - | Safety buffer |
| **TOTAL** | | | **$100** | **10,000 + 1,000** | | |

---

## Stage A: Raw Ore Generation (DeepSeek-R1, $25)

### Why DeepSeek-R1?
- **Cost**: 70% cheaper than OpenAI o1
- **Quality**: Comparable reasoning chains
- **Output**: Verbose but brilliant traces
- **Target**: 10,000 examples at $0.0025 each

### Example Prompt
```
Generate a complex medical scenario requiring trinary logic verification.

Include:
1. Initial presentation (symptoms)
2. Diagnostic options (multiple hypotheses)
3. Risk factors (contradicting evidence)
4. Decision framework (how to resolve ambiguity)

Output: Detailed reasoning chain with uncertainty quantification
```

### Success Criteria
✓ 9,000-10,000 samples generated  
✓ ~$20-25 spent  
✓ Reasoning traces 500-2000 tokens each  
✓ Diverse problem domains  

### Output File
`stage_a_raw_pairs.jsonl` — One raw reasoning per line

---

## Stage B: Refine & Format (GPT-4o-mini, $25)

### Why GPT-4o-mini?
- **Cost**: $0.60/1M output tokens (ultra-cheap)
- **Task**: Clean + structure DeepSeek output
- **Format**: Strict JSON for ForgeNumerics validator
- **Token efficiency**: Likely $5-10 leftover

### Transformation
```
RAW DEEPSEEK OUTPUT:
"So the patient presents with symptoms A and B... 
could be condition X or Y... research shows X more likely 
because of Z... but Y has rare presentation... 
I think we should..."

↓ GPT-4o-mini ↓

FORMATTED JSON:
{
  "instruction": "39-year-old with...",
  "reasoning_chain": "Step 1: Rule out... Step 2: Compare...",
  "trinary_logic": {
    "premise_a": "Most likely diagnosis based on presentation",
    "premise_b": "Alternative diagnosis with supporting evidence",
    "premise_c": "Edge case or atypical presentation",
    "resolution": "Recommended diagnostic path"
  },
  "confidence": 0.87,
  "citations": ["pubmed_123", "nih_guide_456"],
  "metadata": {
    "domain": "medical",
    "difficulty": "hard"
  }
}
```

### Batch Processing
- 50 samples per batch
- Parallel API calls
- Error recovery (fallback to raw if JSON parsing fails)

### Success Criteria
✓ 9,500-10,000 samples formatted  
✓ Valid JSON (parseable)  
✓ All required fields populated  
✓ $5-15 spent (budget buffer)  

### Output File
`stage_b_formatted_pairs.jsonl` — Ready for training or validation

---

## Stage C: Golden Standard Check (Anthropic Claude, $25)

### Why Claude 3.5 Sonnet?
- **Expense**: Can't validate all 10,000 (too costly)
- **Strategy**: Random sample 10% (1,000 examples)
- **Authority**: "Supreme court" of reasoning quality
- **Goal**: Build trustworthy test set for model evaluation

### Validation Checklist
For each sampled example, Claude answers:

1. **Logically sound?** (yes/no)  
   Are premises consistent? Does reasoning follow rules of logic?

2. **Premises exhaustive?** (yes/no)  
   Do the 3 premises cover the decision space?

3. **Resolution valid?** (yes/no)  
   Does final choice follow from the 3 premises?

4. **Corrections needed?** (if yes)  
   Suggest fix or mark "none"

### Example Validation
```
INPUT:
{
  "instruction": "39M with chest pain, EKG normal, troponin negative",
  "premises": {
    "a": "Low probability ACS given normal biomarkers",
    "b": "Atypical presentation could mask MI",
    "c": "Anxiety or musculoskeletal pain common"
  },
  "resolution": "Observation with serial troponins, return precautions"
}

CLAUDE RESPONSE:
{
  "logically_sound": true,
  "premises_exhaustive": true,
  "resolution_valid": true,
  "corrections": null,
  "approved": true,
  "explanation": "Well-reasoned with appropriate risk stratification"
}
```

### Golden Set Composition
```
Input: 10,000 formatted samples
↓
Sample: 1,000 randomly (10%)
↓
Validate: Each with Claude
↓
Filter: Keep only "approved: true"
↓
Output: ~800-900 golden approved samples (80-90% approval typical)
```

### Success Criteria
✓ 1,000 samples validated  
✓ ~$20-25 spent  
✓ 80-90% approval rate  
✓ Golden set size: 800-900 samples  

### Output Files
- `golden_test_set.jsonl` — Approved examples with validation metadata
- `validation_results.jsonl` — Full validation report for all 1,000

---

## Data Quality Pipeline

```
Stage A: Raw Generation
├─ Inputs: Domain templates
├─ Constraints: Budget cap, token limits
├─ Output: 10,000 raw reasoning traces
└─ Quality: Messy but creative

Stage B: Formatting
├─ Inputs: Raw reasoning from A
├─ Constraints: JSON schema, consistency
├─ Output: 10,000 clean training pairs
└─ Quality: Structured, usable

Stage C: Validation
├─ Inputs: 10% sample from B
├─ Constraints: Expert validation rules
├─ Output: 800-900 golden approved
└─ Quality: Trustworthy test set
```

---

## Usage

### Quick Start
```bash
# 1. Set API keys in .env
export DEEPSEEK_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."

# 2. Run cascade
python cascade_runner.py --samples 10000 --domain medical

# 3. Outputs in ./cascade_output/
ls -la cascade_output/
# stage_a_raw_pairs.jsonl (10,000 raw)
# stage_b_formatted_pairs.jsonl (10,000 formatted)
# golden_test_set.jsonl (800-900 approved)
# validation_results.jsonl (1,000 validations)
```

### Programmatic Usage
```python
from packages.core.src.cascade_pipeline import CascadePipeline
from packages.core.src.llm_providers import DeepSeekClient, OpenAIClient, AnthropicClient
import os

# Initialize
deepseek = DeepSeekClient(api_key=os.getenv("DEEPSEEK_API_KEY"))
openai = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
anthropic = AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Run
cascade = CascadePipeline(deepseek, openai, anthropic)
results = cascade.run_full_cascade(num_samples=10000, domain="medical")

# Access results
print(f"Training pairs: {results['stage_b_samples']}")
print(f"Golden approved: {results['stage_c_samples']}")
print(f"Total cost: ${results['total_cost']:.2f}")
```

---

## Output Structure

### stage_b_formatted_pairs.jsonl
```json
{
  "sample_id": "stage_a_000001",
  "source_domain": "medical",
  "instruction": "A 52-year-old woman presents with...",
  "reasoning_chain": "Step 1: Differential includes... Step 2: Key distinguishing features...",
  "trinary_logic": {
    "premise_a": "Most likely diagnosis given presentation",
    "premise_b": "Alternative explanation with supporting evidence",
    "premise_c": "Rare but critical consideration",
    "resolution": "Recommended next steps"
  },
  "confidence": 0.87,
  "citations": ["source_1", "source_2"],
  "metadata": {
    "domain": "medical",
    "difficulty": "hard"
  },
  "cost_estimate": 0.003,
  "timestamp": "2025-12-22T10:30:45Z"
}
```

### golden_test_set.jsonl
Same structure + validation metadata:
```json
{
  ...all fields from stage_b...,
  "validation": {
    "logically_sound": true,
    "premises_exhaustive": true,
    "resolution_valid": true,
    "corrections": null,
    "approved": true,
    "explanation": "Well-reasoned with appropriate context"
  },
  "golden_approved": true
}
```

---

## Cost Optimization Tips

1. **Batch efficiency**: Process 50-100 samples per API batch
2. **Temperature tuning**: 
   - A: 0.7 (diversity for generation)
   - B: 0.2 (consistency for formatting)
   - C: 0.1 (determinism for validation)
3. **Token limits**: Truncate inputs to essential parts
4. **Fallback handling**: Skip failed samples rather than retry
5. **Reserve wisely**: Keep $25 for retry/variations

---

## Next Steps: Fine-Tuning

Once you have 10,000 formatted pairs + 900 golden test set:

### Option 1: Local Fine-Tuning (Free)
```bash
# Install LLaMA-Factory
pip install llama-factory

# Fine-tune on your golden + training set
llamafactory-cli train \
  --model meta-llama/Llama-2-7b-hf \
  --dataset cascade_training.jsonl \
  --output_dir ./arcticcodex-7b-adapter
```

### Option 2: Together.ai Fine-Tuning ($100-500)
```python
import together
together.api_key = os.getenv("TOGETHER_API_KEY")

# Fine-tune on Together platform
job = together.finetune(
    model="meta-llama/Llama-2-7b-hf",
    training_data="cascade_output/stage_b_formatted_pairs.jsonl",
    test_data="cascade_output/golden_test_set.jsonl",
    num_epochs=2,
)
```

### Option 3: Hugging Face Hub (Free hosting)
```bash
# Create dataset card
huggingface-cli repo create arcticcodex-training-data

# Push to hub
huggingface-cli upload arcticcodex-training-data cascade_output/
```

---

## Success Metrics

After running cascade:

| Metric | Target | Indicator |
|--------|--------|-----------|
| Training pairs generated | 10,000 | ✓ stage_b_formatted_pairs.jsonl size |
| Golden approved samples | 800-900 | ✓ golden_test_set.jsonl lines |
| Budget utilization | $75-95 | ✓ metrics in results.json |
| Approval rate | 80-90% | ✓ validation_results.jsonl analysis |
| Average confidence | >0.8 | ✓ mean of confidence field |
| Format validity | 100% | ✓ all JSON parseable |

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Budget exceeded | Token usage higher than expected | Reduce max_tokens per stage |
| Low approval rate (<70%) | Formatting issues | Review stage B output, adjust prompt |
| Slow generation | Sequential processing | Use batch API calls (if available) |
| JSON parse errors | Malformed 4o-mini output | Add validation before B→C |
| High cost per sample | Verbose outputs | Reduce context length, use summarization |

---

## Timeline

| Stage | Time | Cost |
|-------|------|------|
| A (10K generation) | 30-60 min | $25 |
| B (10K formatting) | 20-40 min | $25 |
| C (1K validation) | 10-20 min | $25 |
| Total | **60-120 min** | **$75** |

Plus $25 reserve = **$100 total**, **2-3 hours wall time**.

---

**Result**: 10,000 training pairs + 900 golden test set  
**Cost**: ~$75 (25% reserve remaining)  
**Model readiness**: Full dataset for 7B-13B fine-tuning  
