"""
Minimal Wikipedia XML dump extractor to JSONL (title + text).
Avoids wikiextractor regex bug; uses streaming iterparse.

Usage:
  python training/wiki_extract_minimal.py \
    --input /root/KnowledgeTXT/enwiki-20251101-pages-articles-multistream.xml.bz2 \
    --output /root/raw_wiki.jsonl \
    --max-pages 1000000

Outputs JSONL lines: {"title": str, "text": str, "url": str}
Skip disambiguation and redirect pages; drop empty text.
"""

import argparse
import bz2
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

DISAMBIG_RE = re.compile(r"\{\{disambig(uation)?\}\}", re.IGNORECASE)
REDIRECT_RE = re.compile(r"#redirect", re.IGNORECASE)


def iter_pages(bz2_path: Path, max_pages: int | None):
    ctx = ET.iterparse(bz2.open(bz2_path, "rb"), events=("end",))
    title = None
    text = None
    ns = None
    for event, elem in ctx:
        if elem.tag.endswith("}page"):
            # extract title/text within this page
            title = elem.findtext(".//{*}title") or ""
            ns_text = elem.findtext(".//{*}ns") or "0"
            ns = int(ns_text) if ns_text.isdigit() else 0
            text = elem.findtext(".//{*}text") or ""
            yield title, ns, text
            elem.clear()
            if max_pages is not None:
                max_pages -= 1
                if max_pages <= 0:
                    break


def is_skip(title: str, ns: int, text: str) -> bool:
    if ns != 0:
        return True
    head = text[:200].lower()
    if REDIRECT_RE.match(head):
        return True
    if DISAMBIG_RE.search(text[:500]):
        return True
    if not text.strip():
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description="Minimal wiki XML to JSONL extractor")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    written = 0
    with out_path.open("w", encoding="utf-8") as out_f:
        for title, ns, text in iter_pages(in_path, args.max_pages):
            if is_skip(title, ns, text):
                continue
            obj = {
                "title": title,
                "text": text,
                "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
            }
            out_f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written} pages to {out_path}")


if __name__ == "__main__":
    main()
