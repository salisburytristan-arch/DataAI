"""
Train a 7B-14B conversational student model on local JSONL data.

Usage (single node, 2xH100):
  python training/train_student.py \
    --model mistralai/Mistral-7B-Instruct-v0.3 \
    --data-dir data \
    --output-dir outputs/student-7b \
    --deepspeed training/deepspeed_zero3_2xH100.json \
    --max-seq-len 4096 \
    --per-device-batch 4 \
    --grad-accum 32 \
    --max-steps 1500

Requires: torch, transformers>=4.37, datasets, deepspeed, accelerate.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import datasets
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as err:
                logger.warning("Skipping malformed line in %s: %s", path, err)


def record_to_messages(record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
    # Flexible handling for different record schemas
    if "messages" in record and isinstance(record["messages"], list):
        messages = record["messages"]
    elif {"system", "user", "assistant"}.issubset(record):
        messages = []
        if record.get("system"):
            messages.append({"role": "system", "content": str(record["system"])})
        messages.append({"role": "user", "content": str(record["user"])})
        messages.append({"role": "assistant", "content": str(record["assistant"])})
    elif "prompt" in record and "response" in record:
        messages = []
        if record.get("system"):
            messages.append({"role": "system", "content": str(record["system"])})
        messages.append({"role": "user", "content": str(record["prompt"])})
        messages.append({"role": "assistant", "content": str(record["response"])})
    else:
        return None

    # Drop empty content to keep template clean
    normalized = [{"role": m["role"], "content": str(m["content"]).strip()} for m in messages if m.get("content")]
    return normalized if len(normalized) >= 2 else None


def load_conversations(data_dir: Path) -> List[Dict[str, Any]]:
    candidates = [
        data_dir / "seed.jsonl",
        data_dir / "train.jsonl",
        data_dir / "sft.jsonl",
        data_dir / "wiki_articles.jsonl",
        data_dir / "wiki_teacher_labeled.jsonl",
        data_dir / "synth" / "train.jsonl",
    ]
    records: List[Dict[str, Any]] = []

    for path in candidates:
        if not path.exists():
            continue
        for rec in read_jsonl(path):
            messages = record_to_messages(rec)
            if not messages:
                continue
            records.append({"messages": messages})
    logger.info("Loaded %d conversations from %d files", len(records), len([p for p in candidates if p.exists()]))
    return records


def build_dataset(tokenizer, records: List[Dict[str, Any]], max_seq_len: int):
    ds = datasets.Dataset.from_list(records)

    def _tokenize(example):
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=True,
            add_generation_prompt=False,
            max_length=max_seq_len,
            truncation=True,
        )
        return {"input_ids": text["input_ids"], "attention_mask": text["attention_mask"]}

    return ds.map(_tokenize, remove_columns=["messages"], batched=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train conversational student model")
    parser.add_argument("--model", required=True, help="Base model name or path (e.g., mistralai/Mistral-7B-Instruct-v0.3)")
    parser.add_argument("--data-dir", default="data", help="Path to data directory with JSONL files")
    parser.add_argument("--output-dir", default="outputs/student-7b", help="Where to store checkpoints")
    parser.add_argument("--deepspeed", default=None, help="Path to DeepSpeed config JSON")
    parser.add_argument("--max-seq-len", type=int, default=4096, help="Max sequence length")
    parser.add_argument("--per-device-batch", type=int, default=4, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=32, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=0.05, help="Weight decay")
    parser.add_argument("--warmup-ratio", type=float, default=0.03, help="Warmup ratio")
    parser.add_argument("--max-steps", type=int, default=1500, help="Max training steps (-1 to use epochs)")
    parser.add_argument("--save-steps", type=int, default=500, help="Save every N steps")
    parser.add_argument("--logging-steps", type=int, default=20, help="Log every N steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def main():
    args = parse_args()
    data_dir = Path(args.data_dir)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    records = load_conversations(data_dir)
    if not records:
        raise SystemExit("No data found in expected JSONL files.")

    tokenized = build_dataset(tokenizer, records, args.max_seq_len)

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        max_steps=args.max_steps,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        evaluation_strategy="no",
        lr_scheduler_type="cosine",
        bf16=True,
        gradient_checkpointing=True,
        deepspeed=args.deepspeed,
        seed=args.seed,
        report_to=["none"],
        ddp_find_unused_parameters=False,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=data_collator,
    )

    logger.info("Starting training with %d samples", len(tokenized))
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    logger.info("Training complete. Model saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
