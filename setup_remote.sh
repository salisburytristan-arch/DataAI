#!/bin/bash
# Setup script for Vast.ai rental GPU

set -e

echo "🚀 ArcticCodex Remote Training Setup"
echo "======================================"

# System info
echo ""
echo "📊 System Information:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# Update system
echo "📦 Updating system packages..."
apt-get update -qq
apt-get install -y -qq git wget curl vim tmux htop nvtop

# Install Python packages
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip -q

# Core ML libraries
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
pip install transformers datasets accelerate peft bitsandbytes scipy sentencepiece -q
pip install flash-attn --no-build-isolation -q
pip install tensorboard wandb -q

echo ""
echo "✅ Installation complete!"
echo ""
echo "📂 Workspace ready at: /workspace"
echo ""
echo "🔑 Next steps:"
echo "   1. Upload your data:"
echo "      scp -P 57710 -r clean_data root@108.255.76.60:/workspace/"
echo ""
echo "   2. Upload training script:"
echo "      scp -P 57710 train_remote_qlora.py root@108.255.76.60:/workspace/"
echo ""
echo "   3. Start training (14B model, 4 GPUs):"
echo "      cd /workspace"
echo "      accelerate launch --num_processes=4 train_remote_qlora.py \\"
echo "        --model_name Qwen/Qwen2.5-14B \\"
echo "        --output_dir ./arcticcodex_14b_lora \\"
echo "        --num_train_epochs 3 \\"
echo "        --per_device_train_batch_size 1 \\"
echo "        --gradient_accumulation_steps 16 \\"
echo "        --learning_rate 2e-4 \\"
echo "        --bf16 True \\"
echo "        --logging_steps 10 \\"
echo "        --save_steps 500 \\"
echo "        --eval_steps 500 \\"
echo "        --lora_r 64 \\"
echo "        --lora_alpha 128"
echo ""
echo "   4. Monitor with tmux:"
echo "      tmux new -s train"
echo "      # Then run training inside tmux"
echo "      # Detach: Ctrl+B, then D"
echo "      # Reattach: tmux attach -t train"
echo ""
