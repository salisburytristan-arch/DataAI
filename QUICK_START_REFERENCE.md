# Quick Reference: Your 3 Training Systems

## 🚀 Quick Start (Pick One)

### Option A: I have random data to distill
```bash
python cascade_runner.py --samples 10000 --domain medical
# Output: 10,000 training pairs + 900 golden
# Cost: ~$75 | Time: 2-3 hours
```

### Option B: I have .txt files to master
```bash
python distiller_runner.py --input my_manual.txt
# Output: Q&A pairs from YOUR data
# Cost: ~$15-20 | Time: 30-45 min
```

### Option C: I need maximum quality
```python
from packages.core.src.cascade_pipeline import CascadePipeline
# Use all 3 APIs simultaneously
# Cost: Custom | Result: 3 perspectives per sample
```

---

## 📊 Side-by-Side Comparison

```
┌──────────────────┬─────────────────┬─────────────────┬──────────────────┐
│ SYSTEM           │ CASCADE         │ DISTILLATION    │ ENSEMBLE         │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Use When...      │ Need lots of    │ Have domain     │ Need best        │
│                  │ diverse data    │ .txt files      │ quality          │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Input            │ Domain template │ your_file.txt   │ Any data         │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Output Size      │ 10,000 pairs    │ 900-2K pairs    │ Unlimited        │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Cost             │ $75-100         │ $15-50          │ $0.15-0.50/sample│
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Time             │ 2-3 hours       │ 30-90 min       │ Custom           │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Quality          │ Good (3-stage)  │ Excellent       │ Best (3 views)   │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Stage A          │ DeepSeek Gen    │ Chunking (free) │ Teacher A        │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Stage B          │ OpenAI Format   │ DeepSeek Gen    │ Teacher B        │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Stage C          │ Claude Validate │ Claude Validate │ Teacher C        │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ Best For         │ Training 7B-13B │ Expert models   │ Critical apps    │
└──────────────────┴─────────────────┴─────────────────┴──────────────────┘
```

---

## 💰 Budget Allocation

### $25 Budget
- Cascade Stage A only (2,500 raw pairs)
- OR Distillation generation + validation (1 doc)

### $50 Budget
- Full Cascade (10K pairs) with partial golden set
- OR 2 documents distilled + validated

### $100 Budget (Recommended Monthly)
- **Option 1**: Full Cascade + 2 Distillations + Reserve
- **Option 2**: Deep single domain (Distill + Fine-tune)
- **Option 3**: 4-5 documents distilled with full validation

### $200+ Budget
- Multiple fine-tunes on Vast.ai
- Ensemble training with all 3 APIs
- Continuous weekly improvements

---

## 🎯 Decision Tree

```
Do you have static .txt files?
├─ YES → Use DISTILLATION
│        ✓ Most cost-effective
│        ✓ Best quality
│        ✓ Domain-specific
│        └─ $15-30 per document
│
└─ NO → Need lots of diverse data?
        ├─ YES → Use CASCADE
        │        ✓ Fast generation
        │        ✓ 3-stage quality
        │        ✓ Large dataset
        │        └─ $75-100 for 10K
        │
        └─ NO → Need maximum quality?
                 ├─ YES → Use ENSEMBLE
                 │        ✓ 3 perspectives
                 │        ✓ Highest quality
                 │        ✓ Consensus voting
                 │        └─ Custom cost
                 │
                 └─ NO → Start simple
                         └─ Try Cascade Stage A
                            $25 for 2,500 pairs
```

---

## 📝 Output Formats

All systems export to formats ready for fine-tuning:

```json
// JSONL format (standard for fine-tuning)
{
  "instruction": "User question",
  "input": "",
  "output": "Model answer",
  "reasoning": "Why this is correct",
  "difficulty": "medium"
}

// Alpaca format (instruction-based)
{
  "instruction": "Question",
  "input": "",
  "output": "Answer"
}

// LLaMA-Factory format (conversation)
{
  "messages": [
    {"role": "user", "content": "Question"},
    {"role": "assistant", "content": "Answer"}
  ]
}
```

---

## 🔧 Implementation Checklist

### Pre-Flight
- [ ] Set `DEEPSEEK_API_KEY` in .env
- [ ] Set `OPENAI_API_KEY` in .env
- [ ] Set `ANTHROPIC_API_KEY` in .env
- [ ] Python 3.12+ installed
- [ ] Virtual environment activated

### Run Cascade
- [ ] `python cascade_runner.py --samples 10000`
- [ ] Monitor cost tracking
- [ ] Review stage_b_formatted_pairs.jsonl
- [ ] Check golden_test_set.jsonl

### Run Distillation
- [ ] Prepare your .txt file
- [ ] `python distiller_runner.py --input file.txt`
- [ ] Review generated_qa_pairs.jsonl
- [ ] Check validation results
- [ ] Inspect golden_dataset.jsonl

### Fine-Tune (Optional)
- [ ] Set `VAST_API_KEY` if using Vast.ai
- [ ] `pip install llama-factory`
- [ ] Point trainer to golden_dataset.jsonl
- [ ] Train for 1-2 epochs
- [ ] Deploy specialist model

### Evaluate
- [ ] Approval rate > 75%?
- [ ] Cost per sample acceptable?
- [ ] Time to completion reasonable?
- [ ] Ready for next iteration?

---

## 💡 Pro Tips

1. **Start small**: Run one system, measure results, scale up
2. **Validate first**: Always run validation before fine-tuning
3. **Budget wisely**: Keep 20-25% reserve for retries
4. **Domain focus**: Distillation works better than Cascade for specialized domains
5. **Iterate**: Each month improve on last month's process
6. **Monitor**: Track cost/quality/time for each run
7. **Reserve capacity**: Don't spend entire budget at once

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| API key error | Check .env file spelling |
| High cost | Reduce max_tokens, batch size |
| Low approval rate | Review prompts, improve chunking |
| Slow generation | Check API rate limits |
| Memory issues | Reduce chunk_size parameter |
| JSON parse errors | Add response validation |

---

## 🎓 Learning Path

```
Week 1: Learn the Systems
  └─ Read TRAINING_SYSTEMS_INTEGRATION.md
  └─ Review CASCADE_BUDGET_STRATEGY.md
  └─ Review DISTILLATION_COMPLETE_GUIDE.md

Week 2: Proof of Concept
  └─ Run Cascade pipeline ($25)
  └─ Run Distillation on 1 doc ($15)
  └─ Compare outputs

Week 3: Production
  └─ Fine-tune specialist model ($20)
  └─ Deploy and evaluate
  └─ Plan next iteration

Week 4+: Scale & Iterate
  └─ Distill 2-3 more domains
  └─ Experiment with ensemble
  └─ Build portfolio of specialist models
```

---

## 🚀 Sample $100 Monthly Plan

```
Week 1: Cascade
  python cascade_runner.py --samples 10000
  Cost: $25 (Gen + Val) | Output: 10K pairs

Week 2: Distillation (1 doc)
  python distiller_runner.py --input medical_manual.txt
  Cost: $20 | Output: 1K golden pairs

Week 3: Distillation (2nd doc)
  python distiller_runner.py --input legal_guide.txt
  Cost: $20 | Output: 1K golden pairs

Week 4: Fine-tune + Reserve
  Fine-tune on Vast.ai: $20
  Reserve for experiments: $15

RESULT THIS MONTH:
  • 10,000 general training pairs
  • 2 specialized datasets
  • 1 fine-tuned expert model
  • Metrics and cost breakdown
  • $15 buffer for next week
```

---

## 📚 Complete Documentation

- **CASCADE_BUDGET_STRATEGY.md** → $100 3-stage pipeline
- **DISTILLATION_COMPLETE_GUIDE.md** → .txt file mastery
- **TRAINING_SYSTEMS_INTEGRATION.md** → Full integration guide
- **cascade_runner.py** → Run cascade immediately
- **distiller_runner.py** → Run distillation immediately

---

## 🎯 Your Goal

**Turn $100 → Expert AI Model in Your Domain**

✓ Cascade: Diverse training data  
✓ Distillation: Domain expertise  
✓ Ensemble: Maximum quality  

Pick one. Execute. Measure. Scale.

**You're ready. Go build something amazing.**
