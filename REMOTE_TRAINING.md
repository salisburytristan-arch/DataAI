# Remote Training Commands (Vast.ai)

## 1. Connect to Your Instance

```powershell
# Direct SSH (recommended)
ssh -p 57710 root@108.255.76.60

# With port forwarding for TensorBoard
ssh -p 57710 root@108.255.76.60 -L 6006:localhost:6006
```

## 2. Upload Your Data

From your local PC:

```powershell
# Compress first
tar -czf clean_data.tar.gz clean_data/

# Upload
scp -P 57710 clean_data.tar.gz root@108.255.76.60:/workspace/

# Upload training script
scp -P 57710 train_remote_qlora.py root@108.255.76.60:/workspace/
scp -P 57710 setup_remote.sh root@108.255.76.60:/workspace/
```

## 3. Setup Remote Environment

On the Vast.ai instance:

```bash
cd /workspace
chmod +x setup_remote.sh
./setup_remote.sh

# Extract data
tar -xzf clean_data.tar.gz
```

## 4. Training Configurations

### A) 14B Model (Validation Run - 4 GPUs)

**Purpose**: Prove your data works before scaling to 32B+

```bash
tmux new -s train14b

accelerate launch --num_processes=4 \
  --main_process_port=29500 \
  train_remote_qlora.py \
  --model_name Qwen/Qwen2.5-14B \
  --output_dir ./arcticcodex_14b_lora \
  --num_train_epochs 3 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 2e-4 \
  --warmup_ratio 0.03 \
  --lr_scheduler_type cosine \
  --bf16 True \
  --logging_steps 10 \
  --save_steps 500 \
  --eval_steps 500 \
  --save_total_limit 3 \
  --gradient_checkpointing True \
  --lora_r 64 \
  --lora_alpha 128 \
  --max_seq_length 4096 \
  --report_to tensorboard
```

**Expected**:
- Time: ~6-8 hours for 50K examples
- Memory: ~12GB per GPU
- Cost: ~$10-12

**Detach**: `Ctrl+B`, then `D`  
**Reattach**: `tmux attach -t train14b`

### B) 32B Model (Production - 8 GPUs with FSDP)

**After 14B validates**, scale to 32B:

Create `fsdp_config.yaml`:

```yaml
compute_environment: LOCAL_MACHINE
distributed_type: FSDP
fsdp_config:
  fsdp_auto_wrap_policy: TRANSFORMER_BASED_WRAP
  fsdp_backward_prefetch_policy: BACKWARD_PRE
  fsdp_cpu_ram_efficient_loading: true
  fsdp_forward_prefetch: false
  fsdp_offload_params: false
  fsdp_sharding_strategy: FULL_SHARD
  fsdp_state_dict_type: SHARDED_STATE_DICT
  fsdp_sync_module_states: true
  fsdp_transformer_layer_cls_to_wrap: Qwen2DecoderLayer
  fsdp_use_orig_params: true
machine_rank: 0
main_process_ip: localhost
main_process_port: 29500
num_machines: 1
num_processes: 8
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false
```

Then:

```bash
tmux new -s train32b

accelerate launch --config_file fsdp_config.yaml \
  train_remote_qlora.py \
  --model_name Qwen/Qwen2.5-32B \
  --output_dir ./arcticcodex_32b_lora \
  --num_train_epochs 3 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 \
  --warmup_ratio 0.03 \
  --lr_scheduler_type cosine \
  --bf16 True \
  --logging_steps 10 \
  --save_steps 500 \
  --eval_steps 500 \
  --gradient_checkpointing True \
  --lora_r 32 \
  --lora_alpha 64 \
  --max_seq_length 2048 \
  --report_to tensorboard
```

**Expected**:
- Time: ~12-16 hours
- Memory: ~20GB per GPU
- Cost: ~$20-25

### C) 40B Model (Maximum - 12 GPUs with FSDP)

Only if 32B isn't enough:

```bash
# Update fsdp_config.yaml: num_processes: 12

tmux new -s train40b

accelerate launch --config_file fsdp_config.yaml \
  train_remote_qlora.py \
  --model_name meta-llama/Llama-3.1-40B \
  --output_dir ./arcticcodex_40b_lora \
  --num_train_epochs 2 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 6 \
  --learning_rate 1e-4 \
  --lora_r 32 \
  --lora_alpha 64 \
  --max_seq_length 2048
```

## 5. Monitor Training

### Option A: TensorBoard (via SSH tunnel)

On remote:
```bash
tensorboard --logdir ./arcticcodex_14b_lora/runs --host 0.0.0.0 --port 6006
```

On local (in another terminal):
```powershell
ssh -p 57710 root@108.255.76.60 -L 6006:localhost:6006
```

Then open: http://localhost:6006

### Option B: Watch Logs

```bash
tail -f arcticcodex_14b_lora/trainer_log.txt
```

### Option C: GPU Usage

```bash
watch -n 1 nvidia-smi
# Or prettier:
nvtop
```

## 6. Download Trained Model

When training completes:

```powershell
# From your local PC
scp -P 57710 -r root@108.255.76.60:/workspace/arcticcodex_14b_lora ./models/

# Compress first if large
ssh -p 57710 root@108.255.76.60 "cd /workspace && tar -czf arcticcodex_14b_lora.tar.gz arcticcodex_14b_lora/"
scp -P 57710 root@108.255.76.60:/workspace/arcticcodex_14b_lora.tar.gz ./models/
```

**LoRA adapter is only ~50-200MB** - fast download!

## 7. Troubleshooting

### Out of Memory

Reduce batch size or sequence length:
```bash
--per_device_train_batch_size 1 \
--gradient_accumulation_steps 32 \
--max_seq_length 2048
```

### Training Stalls

Check if data loading is slow:
```bash
# Add to training command:
--dataloader_num_workers 4 \
--dataloader_pin_memory True
```

### Connection Drops

Always use `tmux` so training continues:
```bash
tmux new -s train
# Run training...
# Detach: Ctrl+B, D
# Reconnect later: tmux attach -t train
```

### Slow Epochs

Enable sequence packing (requires custom collator - let me know if needed)

## 8. Cost Optimization

Your rental: **$1.689/hr**

| Model | GPUs | Time | Cost |
|-------|------|------|------|
| 14B | 4 | 6h | ~$10 |
| 32B | 8 | 12h | ~$20 |
| 40B | 12 | 16h | ~$27 |

**Tip**: Run 14B first to validate data quality. If eval loss doesn't improve, fix data before scaling to 32B.

## 9. Recommended Workflow

```bash
# Day 1: Validation (14B, 4 GPUs)
accelerate launch --num_processes=4 train_remote_qlora.py [14B args]
# Cost: $10, proves data works

# Day 2: Production (32B, 8 GPUs)
accelerate launch --config_file fsdp_config.yaml train_remote_qlora.py [32B args]
# Cost: $20, production model

# Total: $30 for 14B + 32B trained models
```

## 10. Next Steps After Training

```powershell
# Download model
scp -P 57710 -r root@108.255.76.60:/workspace/arcticcodex_14b_lora ./models/

# Test locally (see HYBRID_WORKFLOW.md)
python test_finetuned_model.py --model ./models/arcticcodex_14b_lora
```

Ready to connect and start training?
