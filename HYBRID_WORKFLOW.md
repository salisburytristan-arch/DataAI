# Hybrid Fine-Tuning Workflow for AMD RX 6600

## Your Hardware Profile

✅ **Strengths**:
- 32GB RAM → Excellent for data processing
- 6c/12t CPU → Good for tokenization/preprocessing
- 8GB VRAM → Perfect for quantized inference

❌ **Limitations**:
- AMD GPU on Windows → Poor CUDA tooling support
- 8GB VRAM → Not enough for 7B+ training

**Strategy**: Local data prep + Remote training + Local inference

---

## Phase 1: LOCAL - Data Preparation (Your PC)

### Step 1: Prepare Raw Dataset

```powershell
# Combine all sources
python prepare_finetune_dataset.py --max-total 50000
```

**Output**: `finetune_data/complete_dataset.jsonl` (~50K examples)

### Step 2: Clean & Validate

```powershell
# Remove duplicates, garbage, normalize formatting
python clean_training_data.py `
  --input ./finetune_data/complete_dataset.jsonl `
  --output-dir ./clean_data `
  --min-length 50 `
  --max-length 2048 `
  --train-split 0.95
```

**Output**:
- `clean_data/train_clean.jsonl` (training set)
- `clean_data/val_clean.jsonl` (validation set)
- `clean_data/dataset_stats.json` (quality metrics)

**What this does**:
- ✅ Removes duplicates (SHA256 content hashing)
- ✅ Filters garbage (navigation text, punctuation-only)
- ✅ Normalizes formatting (whitespace, quotes, Unicode)
- ✅ Validates lengths (50–2048 chars)
- ✅ Splits train/val (95%/5%)

### Step 3: Upload to Remote

```powershell
# Compress for upload
tar -czf clean_data.tar.gz clean_data/

# Or use SCP/SFTP to rental GPU
scp clean_data.tar.gz user@vast-gpu:/workspace/
```

---

## Phase 2: REMOTE - Fine-Tuning (Vast.ai / RunPod)

### Recommended Rental: Vast.ai L40S or RTX 4090

**Specs needed**:
- GPU: L40S (48GB) or RTX 4090 (24GB)
- VRAM: 24GB+ for 7B models with LoRA
- Cost: $0.50–$1.00/hour
- Time: 4–8 hours for 50K examples

### Setup Remote Environment

```bash
# On rental GPU (Ubuntu + CUDA)
cd /workspace
tar -xzf clean_data.tar.gz

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers datasets accelerate peft bitsandbytes scipy

# Clone training script (create this next)
wget https://raw.githubusercontent.com/your-repo/finetune_remote.py
```

### Run Training (QLoRA for memory efficiency)

```bash
python finetune_remote.py \
  --model_name_or_path mistralai/Mistral-7B-v0.1 \
  --train_file clean_data/train_clean.jsonl \
  --val_file clean_data/val_clean.jsonl \
  --output_dir ./arcticcodex_lora \
  --num_train_epochs 3 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --learning_rate 2e-4 \
  --lora_r 16 \
  --lora_alpha 32 \
  --lora_dropout 0.05 \
  --max_seq_length 2048 \
  --fp16 True \
  --save_steps 500 \
  --logging_steps 10
```

**Training time**: ~6 hours for 50K examples on L40S

**Output**: `arcticcodex_lora/` (LoRA adapter ~50MB)

### Download Trained Model

```powershell
# From your PC
scp -r user@vast-gpu:/workspace/arcticcodex_lora ./models/
```

---

## Phase 3: LOCAL - Inference (Your PC)

### Option A: Run with Transformers (Slower, 8GB VRAM needed)

```powershell
pip install transformers peft torch

python test_finetuned_model.py --model ./models/arcticcodex_lora
```

### Option B: Quantize to GGUF + llama.cpp (Recommended)

**Why**: AMD GPU Vulkan support, faster, runs in 4GB VRAM

```powershell
# Install llama.cpp with Vulkan (AMD GPU support)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DLLAMA_VULKAN=1
cmake --build build --config Release

# Convert LoRA to GGUF
python convert.py ./models/arcticcodex_lora --outfile ./models/arcticcodex.gguf --outtype q4_0

# Run inference
.\build\bin\Release\main.exe `
  -m .\models\arcticcodex.gguf `
  -n 256 `
  -p "### Instruction:\nExplain machine learning\n\n### Response:\n" `
  --n-gpu-layers 35
```

**Performance**: ~20-30 tokens/sec on RX 6600

### Option C: Use Ollama (Easiest)

```powershell
# Install Ollama (auto-detects AMD GPU)
winget install Ollama.Ollama

# Create model from GGUF
ollama create arcticcodex -f Modelfile

# Run
ollama run arcticcodex "Explain quantum computing"
```

---

## Cost & Time Breakdown

| Phase | Where | Time | Cost |
|-------|-------|------|------|
| Data prep | Local | 1-2 hours | $0 |
| Upload | Local → Remote | 10 mins | $0 |
| Training | Vast.ai L40S | 6 hours | ~$4 |
| Download | Remote → Local | 5 mins | $0 |
| Quantization | Local | 10 mins | $0 |
| **Total** | | **~8 hours** | **~$4** |

---

## Data Quality Checklist

Before uploading to remote GPU:

- [ ] Duplicates removed (`dataset_stats.json` shows 0 duplicates)
- [ ] Avg output length > 100 chars
- [ ] Rejection rate < 30%
- [ ] Validation set is 5% of total
- [ ] Sample examples look coherent
- [ ] File sizes: train ~200MB, val ~10MB

**Bad data = wasted GPU hours = wasted money**

Spend time on local data cleaning!

---

## Iteration Loop

1. **Train on remote GPU** (6 hours, $4)
2. **Download LoRA adapter** (5 mins)
3. **Test locally with llama.cpp** (instant)
4. **If quality is bad**: Fix dataset locally, re-upload, repeat

This loop costs $4 per iteration vs. $1000+ for local NVIDIA GPU.

---

## Next Steps

1. **Right now** (local):
   ```powershell
   python prepare_finetune_dataset.py --max-total 50000
   python clean_training_data.py
   ```

2. **Rent GPU** (when ready):
   - Vast.ai: Search "RTX 4090" or "L40S"
   - RunPod: "Secure Cloud" tier
   - Lambda Labs: On-demand A100

3. **Upload & train** (remote):
   ```bash
   python finetune_remote.py
   ```

4. **Download & test** (local):
   ```powershell
   ollama run arcticcodex
   ```

Want me to create the remote training script next?
