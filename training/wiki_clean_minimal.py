"""
Minimal Wikipedia cleaning + chunking.

Input: JSONL with fields: {"title": str, "text": str, "url"?: str}
Output: JSONL with fields: {"doc_id", "chunk_id", "title", "text", "source", "meta"}

Usage:
  python training/wiki_clean_minimal.py \
    --input raw_wiki.jsonl \
    --output wiki_clean.jsonl \
    --min-tokens 200 \
    --max-tokens 1024 \
    --max-docs 500000

Notes:
- Deduplicates chunks by SHA256 of lowercase text.
- Skips obvious disambiguation/stub pages and very short content.
- Keeps license note (Wikipedia: CC-BY-SA).
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, List, Dict, Set

DISAMBIG_PAT = re.compile(r"disambiguation", re.IGNORECASE)
STUB_PAT = re.compile(r"This article is a stub", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")
CITATION_TAG_RE = re.compile(r"\[citation needed\]", re.IGNORECASE)
BRACE_RE = re.compile(r"\{\{[^}]*\}\}")
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")


def normalize(text: str) -> str:
    text = CITATION_TAG_RE.sub("", text)
    text = BRACE_RE.sub("", text)
    text = REF_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def should_skip(title: str, text: str, min_tokens: int) -> bool:
    head = text[:400]
    if DISAMBIG_PAT.search(head):
        return True
    if STUB_PAT.search(head):
        return True
    if len(text.split()) < max(50, min_tokens // 2):
        return True
    return False


def chunk_paragraphs(text: str, max_tokens: int) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    buf_tokens = 0

    def flush():
        nonlocal buf, buf_tokens
        if buf:
            chunks.append("\n\n".join(buf).strip())
            buf = []
            buf_tokens = 0

    for para in paragraphs:
        toks = para.split()
        if len(toks) > max_tokens:
            # hard split long paragraph
            for i in range(0, len(toks), max_tokens):
                sub = " ".join(toks[i : i + max_tokens])
                chunks.append(sub)
            continue
        if buf_tokens + len(toks) > max_tokens:
            flush()
        buf.append(para)
        buf_tokens += len(toks)
    flush()
    return chunks


def hash_text(text: str) -> str:
    return hashlib.sha256(text.lower().encode("utf-8")).hexdigest()


def iter_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main():
    ap = argparse.ArgumentParser(description="Minimal wiki cleaner")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-tokens", type=int, default=200)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--max-docs", type=int, default=None, help="Optional cap on docs processed")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    seen_hashes: Set[str] = set()
    written_docs = 0

    with out_path.open("w", encoding="utf-8") as out_f:
        for doc_idx, rec in enumerate(iter_jsonl(in_path), 1):
            if args.max_docs and written_docs >= args.max_docs:
                break
            title = rec.get("title") or ""
            raw_text = rec.get("text") or ""
            url = rec.get("url") or ""
            text = normalize(raw_text)
            if should_skip(title, text, args.min_tokens):
                continue
            chunks = chunk_paragraphs(text, args.max_tokens)
            chunk_id = 0
            wrote_any = False
            for chunk in chunks:
                if len(chunk.split()) < args.min_tokens:
                    continue
                h = hash_text(chunk)
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                obj = {
                    "doc_id": f"wiki:{doc_idx}",
                    "chunk_id": str(chunk_id),
                    "title": title,
                    "text": chunk,
                    "source": "wikipedia",
                    "meta": {
                        "url": url,
                        "license": "CC-BY-SA",
                        "hash": h,
                    },
                }
                out_f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                chunk_id += 1
                wrote_any = True
            if wrote_any:
                written_docs += 1


if __name__ == "__main__":
    main()
