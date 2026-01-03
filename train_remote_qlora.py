#!/usr/bin/env python3
"""Remote training script optimized for Vast.ai 12×RTX 5060 Ti."""

import os
import sys
import torch
import transformers
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from peft.tuners.lora import LoraLayer
import bitsandbytes as bnb
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ModelArguments:
    model_name: str = field(default="Qwen/Qwen2.5-14B")
    trust_remote_code: bool = field(default=True)

@dataclass
class DataArguments:
    train_file: str = field(default="./clean_data/train_clean.jsonl")
    eval_file: str = field(default="./clean_data/val_clean.jsonl")
    max_seq_length: int = field(default=4096)

@dataclass
class LoRAArguments:
    lora_r: int = field(default=64)
    lora_alpha: int = field(default=128)
    lora_dropout: float = field(default=0.05)
    target_modules: str = field(
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj"
    )

def format_instruction(example):
    """Alpaca format."""
    if example.get('input', '').strip():
        text = f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Response:\n{example['output']}"
    else:
        text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
    return {"text": text}

def print_trainable_parameters(model):
    """Print trainable parameter count."""
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    
    print(f"\n🔧 Model Parameters:")
    print(f"   Trainable: {trainable_params:,} ({100 * trainable_params / all_param:.2f}%)")
    print(f"   Total: {all_param:,}")
    print(f"   Memory (4-bit): ~{all_param * 0.5 / 1e9:.1f}GB\n")

def main():
    parser = transformers.HfArgumentParser((
        ModelArguments,
        DataArguments,
        LoRAArguments,
        TrainingArguments
    ))
    model_args, data_args, lora_args, training_args = parser.parse_args_into_dataclasses()
    
    print("=" * 80)
    print("🚀 ArcticCodex Remote Training - Vast.ai 12×RTX 5060 Ti")
    print("=" * 80)
    print(f"\n📦 Model: {model_args.model_name}")
    print(f"📊 Training data: {data_args.train_file}")
    print(f"📊 Validation data: {data_args.eval_file}")
    print(f"🎯 Output: {training_args.output_dir}")
    print(f"⚙️  GPUs: {torch.cuda.device_count()}")
    print(f"💾 Max sequence length: {data_args.max_seq_length}")
    print(f"🔄 Epochs: {training_args.num_train_epochs}")
    print(f"📦 Batch size per GPU: {training_args.per_device_train_batch_size}")
    print(f"📊 Gradient accumulation: {training_args.gradient_accumulation_steps}")
    print(f"📈 Effective batch size: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps * torch.cuda.device_count()}")
    print(f"🧮 LoRA r={lora_args.lora_r}, α={lora_args.lora_alpha}\n")
    
    # Load tokenizer
    print("🔧 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name,
        trust_remote_code=model_args.trust_remote_code,
        padding_side="right",
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Load model in 4-bit
    print(f"🔧 Loading model in 4-bit (NF4)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name,
        load_in_4bit=True,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=model_args.trust_remote_code,
        quantization_config=transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        ),
        attn_implementation="flash_attention_2" if training_args.bf16 else None,
    )
    
    # Prepare for LoRA
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    
    # LoRA config
    target_modules = lora_args.target_modules.split(',')
    lora_config = LoraConfig(
        r=lora_args.lora_r,
        lora_alpha=lora_args.lora_alpha,
        target_modules=target_modules,
        lora_dropout=lora_args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, lora_config)
    print_trainable_parameters(model)
    
    # Load dataset
    print("📂 Loading datasets...")
    train_dataset = load_dataset('json', data_files=data_args.train_file, split='train')
    eval_dataset = load_dataset('json', data_files=data_args.eval_file, split='train')
    
    print(f"   Train examples: {len(train_dataset):,}")
    print(f"   Eval examples: {len(eval_dataset):,}\n")
    
    # Format as instructions
    train_dataset = train_dataset.map(format_instruction, remove_columns=train_dataset.column_names)
    eval_dataset = eval_dataset.map(format_instruction, remove_columns=eval_dataset.column_names)
    
    # Tokenize
    def tokenize_function(examples):
        result = tokenizer(
            examples['text'],
            truncation=True,
            max_length=data_args.max_seq_length,
            padding=False,
        )
        result["labels"] = result["input_ids"].copy()
        return result
    
    print("🔄 Tokenizing...")
    train_dataset = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=['text'],
        num_proc=4,
        desc="Tokenizing train",
    )
    
    eval_dataset = eval_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=['text'],
        num_proc=4,
        desc="Tokenizing eval",
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )
    
    # Train
    print("🏋️  Starting training...\n")
    print("=" * 80)
    trainer.train()
    
    # Save
    print("\n" + "=" * 80)
    print(f"💾 Saving model to {training_args.output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(training_args.output_dir)
    
    print("\n✅ Training complete!")
    print(f"\n📦 Download your model:")
    print(f"   scp -P 57710 -r root@108.255.76.60:{training_args.output_dir} ./models/")

if __name__ == "__main__":
    main()
