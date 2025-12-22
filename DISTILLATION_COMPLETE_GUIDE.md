# Synthetic Data Distillation: The Complete Integration Guide

## Overview

**Distillation** turns your static .txt files into fine-tuned expert models.

Instead of RAG (searching the file every time), you bake the knowledge into the model itself.

```
RAG Way:                    Distillation Way:
┌─────────┐                 ┌─────────┐
│ manual  │ ───────┐        │ manual  │ ─┐
└─────────┘        │        └─────────┘   │
                   ↓                       ↓
                Query Search           Q&A Generation
                (every time)           (one-time $10)
                   ↓                       ↓
                Read Result           Gold Dataset
                   ↓                       ↓
                Answer               Fine-Tune Model
                                      (one-time $10)
                                          ↓
                                      Expert Model
                                      (instant, smart)
```

---

## The 4-Step Pipeline

### Step 1: Load & Chunk Text

**Input**: `medical_protocol.txt` (5MB)  
**Process**: Split into 800-char semantic chunks  
**Output**: 400+ chunks  
**Cost**: FREE  
**Time**: <1 second

```python
from packages.core.src.synthetic_data_distiller import TextChunker

chunker = TextChunker(chunk_size=800, overlap=100)
chunks = chunker.load_and_chunk("medical_protocol.txt")
# Output: 400 chunks
```

---

### Step 2: Generate Q&A Pairs (DeepSeek-R1)

**Input**: 400 chunks  
**Teacher**: DeepSeek-R1 (70% cheaper than o1, similar reasoning)  
**Prompt**: "Read this section. Generate 5 complex Q&A pairs."  
**Output**: 2,000 Q&A pairs with reasoning  
**Cost**: ~$10 ($0.005/pair)  
**Time**: 10-15 minutes

**Generated Q&A Structure**:
```json
{
  "question": "Patient has symptom X, what protocol applies?",
  "answer": "Protocol 4.1 describes management of X...",
  "reasoning": "This matches Section 4.1 which specifically addresses X.",
  "difficulty": "medium",
  "source_chunk": "chunk_000042"
}
```

**Why This Works**:
- DeepSeek-R1 excels at reasoning over text
- Generates diverse Q&A (not just lookup)
- Includes reasoning chains (why answers are correct)
- 70% cheaper than OpenAI o1

---

### Step 3: Validate Q&A Pairs (Claude 3.5 Sonnet)

**Input**: 2,000 Q&A pairs  
**Validator**: Claude 3.5 Sonnet (your "Supreme Court")  
**Check**: "Is this answer grounded in the manual? Any hallucinations?"  
**Sample**: 50% (1,000 pairs validated)  
**Output**: 800-900 approved pairs  
**Cost**: ~$5  
**Time**: 5-10 minutes

**Validation Checklist**:
```
✓ Grounded in manual?
✓ No hallucination?
✓ Complete answer?
✓ No factual errors?
```

**Typical Approval Rate**: 80-90%

---

### Step 4: Export & Ready for Fine-Tuning

**Input**: 900 validated pairs  
**Export Formats**:
- `jsonl`: Standard (instruction/output)
- `alpaca`: Instruction/input/output
- `llama-factory`: Conversation format

**Output File**:
```json
{
  "instruction": "Patient has symptom X, what protocol applies?",
  "input": "",
  "output": "Protocol 4.1 describes management of X...",
  "reasoning": "This matches Section 4.1...",
  "difficulty": "medium",
  "source": "chunk_000042"
}
```

**Next**: Use with LLaMA-Factory or Together.ai fine-tuning (Vast.ai optional)

---

## Complete Example Workflow

### 1. Prepare Your Text

Create `medical_protocol.txt`:
```
Section 4.1: Cardiovascular Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For patients presenting with acute chest pain:

1. Initial Assessment
   - Obtain EKG within 10 minutes
   - Check troponin levels
   - Assess vital signs

2. Diagnostic Pathway
   - Normal EKG + negative troponin: Consider non-cardiac
   - Elevated troponin: Consistent with MI
   - ST elevation: STEMI protocol, activate cath lab
   ...
```

### 2. Run Distillation

```bash
# Quick start
python distiller_runner.py --input medical_protocol.txt --domain medical

# Or with custom parameters
python distiller_runner.py \
    --input medical_protocol.txt \
    --questions-per-chunk 5 \
    --generation-budget 10 \
    --validation-budget 5
```

### 3. Monitor Progress

The script outputs:
```
════════════════════════════════════════════════════════════════
STEP 1: Load and Chunk Document
════════════════════════════════════════════════════════════════
Loaded: medical_protocol.txt
Size: 5,234,892 characters
Chunked into: 412 semantic pieces
Avg chunk size: 12,707 chars

════════════════════════════════════════════════════════════════
STEP 2: Generate Q&A Pairs (DeepSeek-R1)
════════════════════════════════════════════════════════════════
Budget: $10 | Target: 2060 pairs
Cost/pair: $0.00486
  Generated 500/2060 | Cost so far: $2.43
  Generated 1000/2060 | Cost so far: $4.86
  Generated 2060/2060 | Cost so far: $10.00

✓ Generated 2060 Q&A pairs
  Cost: $9.87
  Saved: ./distilled_medical_protocol/generated_qa_pairs.jsonl

════════════════════════════════════════════════════════════════
STEP 3: Validate Q&A Pairs (Claude 3.5 Sonnet)
════════════════════════════════════════════════════════════════
Budget: $5 | Input: 2060 pairs
Sampling: 1030 for validation (50%)
  Validated 100/1030 | Approved: 89 | Cost: $0.42
  Validated 500/1030 | Approved: 432 | Cost: $2.10
  Validated 1030/1030 | Approved: 918 | Cost: $4.89

✓ Validated 1030 pairs
  Approved: 918 (89.1%)
  Cost: $4.89
  Saved: ./distilled_medical_protocol/validated_qa_pairs.jsonl

════════════════════════════════════════════════════════════════
STEP 4: Export Golden Dataset
════════════════════════════════════════════════════════════════
✓ Exported 918 golden pairs
  Format: jsonl
  Saved: ./distilled_medical_protocol/golden_dataset.jsonl

════════════════════════════════════════════════════════════════
DISTILLATION COMPLETE ✓
════════════════════════════════════════════════════════════════

RESULTS:
  Input: 5,234,892 characters from medical_protocol.txt
  Chunks: 412
  Q&A Generated: 2060
  Q&A Validated: 1030
  Golden Approved: 918
  Approval Rate: 89.1%
  Time: 1847.3s (30.8m)

OUTPUT:
  Golden Dataset: ./distilled_medical_protocol/golden_dataset.jsonl
  Ready for fine-tuning!
```

### 4. Inspect Golden Dataset

```bash
head -5 ./distilled_medical_protocol/golden_dataset.jsonl | python -m json.tool
```

Output:
```json
{
  "instruction": "What is the recommended initial assessment for acute chest pain?",
  "input": "",
  "output": "For acute chest pain, perform: 1) EKG within 10 minutes, 2) Troponin level check, 3) Vital sign assessment. This helps differentiate cardiac from non-cardiac causes.",
  "reasoning": "Section 4.1 specifically outlines these as the first-line diagnostic steps for chest pain evaluation.",
  "difficulty": "medium",
  "source": "chunk_000142"
}
```

### 5. Fine-Tune Your Model (Optional)

#### Option A: Local (LLaMA-Factory)

```bash
pip install llama-factory

llamafactory-cli train \
  --model meta-llama/Llama-2-7b-hf \
  --dataset distilled_medical_protocol/golden_dataset.jsonl \
  --output_dir ./arcticcodex-medical-7b \
  --learning_rate 1e-4 \
  --num_epochs 2 \
  --batch_size 4
```

#### Option B: Cloud (Together.ai, ~$30)

```python
import together

together.api_key = os.getenv("TOGETHER_API_KEY")

job = together.finetune(
    model="meta-llama/Llama-2-7b-hf",
    training_data="distilled_medical_protocol/golden_dataset.jsonl",
    num_epochs=2,
    learning_rate=1e-4,
)
```

#### Option C: Vast.ai GPU Rental (~$20-30 for 4090 for 1 hour)

```python
from packages.core.src.vast_provisioner import VastProvisioner
import subprocess

provisioner = VastProvisioner(api_key=os.getenv("VAST_API_KEY"))

# Find cheapest 4090
instances = provisioner.search_instances(
    gpu_types=["RTX 4090"],
    min_vram=24,
    max_price=0.50
)

# Provision
instance = provisioner.provision(instances[0]["id"])
provisioner.setup_ssh_tunnel(instance)

# Upload dataset and train
subprocess.run([
    "scp", "-P", "2222",
    "distilled_medical_protocol/golden_dataset.jsonl",
    f"root@localhost:~/dataset.jsonl"
])

# SSH into instance and run LLaMA-Factory training
# (Training takes 30-60 min on 4090)
```

---

## Budget Breakdown

### Minimal ($15-20)
- Generation (DeepSeek): $10
- Validation (Claude): $5
- Fine-tuning: Not included
- **Result**: Golden dataset, ready to use

### Standard ($30-40)
- Generation: $10
- Validation: $5
- Fine-tuning (Vast.ai 1 hour): $15
- **Result**: Specialist model trained and ready

### Premium ($50-75)
- Generation: $15 (more Q&A)
- Validation: $10 (better approval)
- Fine-tuning: $25 (longer training, better model)
- **Result**: High-quality specialist model

### Full Budget ($100)
- 3-4 documents distilled
- High generation + validation budget
- Multiple model fine-tunes
- Backup cost for retries
- **Result**: Specialist models for multiple domains

---

## When to Use Distillation vs RAG

| Scenario | Distillation | RAG |
|----------|--------------|-----|
| Static knowledge (medical guidelines) | ✓✓✓ | ✓ |
| Frequently changing data | ✗ | ✓✓ |
| High query volume | ✓✓✓ | ✓ |
| Complex reasoning required | ✓✓✓ | ✓ |
| One-off queries | ✗ | ✓✓ |
| Cost-sensitive (many queries) | ✓✓✓ | ✓ |
| Large documents (>20MB) | ✓ | ✓✓✓ |
| Real-time updates needed | ✗ | ✓✓✓ |

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Low approval rate (<70%) | Bad Q&A generation | Improve DeepSeek prompts |
| High validation cost | Too many samples | Reduce validation budget, increase sample rate |
| Slow generation | API rate limits | Reduce concurrent requests |
| Memory errors | Chunk size too large | Reduce `chunk_size` in TextChunker |
| JSON parse errors | Malformed responses | Add response validation |

---

## Advanced: Custom Domain Templates

Customize generation for your domain:

```python
domain_prompts = {
    "medical": "Generate clinical scenarios from this text...",
    "legal": "Generate case scenarios from this legal code...",
    "technical": "Generate debugging scenarios from this docs...",
    "financial": "Generate portfolio scenarios from this guide...",
}
```

---

## Next Steps

1. **Prepare text** (choose something valuable & static)
2. **Run distillation** (`python distiller_runner.py --input your_file.txt`)
3. **Inspect golden dataset** (review sample outputs)
4. **Fine-tune model** (optional, LLaMA-Factory or Vast.ai)
5. **Deploy specialist model** (use instead of RAG)

**Total time**: 30-90 minutes  
**Total cost**: $15-50  
**Result**: Expert model that understands your knowledge base
