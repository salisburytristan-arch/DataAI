import os
import gzip
import zlib
from typing import Dict, Any
from .frames import make_blob_t, Frame, MODE_WORD, trits_to_bytes

RESULT_KEYS = [
    "original_bytes",
    "gzip_bytes",
    "zlib_bytes",
    "gzip_ratio",
    "zlib_ratio",
]

def compress_file(path: str, out_dir: str | None = None, base_name: str | None = None) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as f:
        raw = f.read()
    gz = gzip.compress(raw)
    zl = zlib.compress(raw, level=9)
    res: Dict[str, Any] = {
        "original_bytes": len(raw),
        "gzip_bytes": len(gz),
        "zlib_bytes": len(zl),
        "gzip_ratio": round(len(gz) / len(raw), 4) if len(raw) else 0,
        "zlib_ratio": round(len(zl) / len(raw), 4) if len(raw) else 0,
        "gzip_blob_t": make_blob_t(gz),
        "zlib_blob_t": make_blob_t(zl),
    }
    # Write outputs if requested
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        stem = base_name or os.path.splitext(os.path.basename(path))[0]
        raw_path = os.path.join(out_dir, f"{stem}.raw")
        gz_path = os.path.join(out_dir, f"{stem}.gz")
        zl_path = os.path.join(out_dir, f"{stem}.zlib")
        blob_gz_path = os.path.join(out_dir, f"{stem}.blob_t.gzip.txt")
        blob_zl_path = os.path.join(out_dir, f"{stem}.blob_t.zlib.txt")
        frame_gz_path = os.path.join(out_dir, f"{stem}.frame.gzip.txt")
        with open(raw_path, "wb") as f:
            f.write(raw)
        with open(gz_path, "wb") as f:
            f.write(gz)
        with open(zl_path, "wb") as f:
            f.write(zl)
        # write textual tokens/frames for inspection
        with open(blob_gz_path, "w", encoding="utf-8") as f:
            f.write(make_blob_t(gz))
        with open(blob_zl_path, "w", encoding="utf-8") as f:
            f.write(make_blob_t(zl))
        res.update({
            "out_raw": raw_path,
            "out_gzip": gz_path,
            "out_zlib": zl_path,
            "out_blob_gzip": blob_gz_path,
            "out_blob_zlib": blob_zl_path,
        })

    # Build a simple frame for the gzip variant
    header = [
        ("VER", "2.0-T"),
        ("DICT", "DICT_v2025_11"),
        ("TYPE", "COMPRESSED"),
        ("COMP", "GZIP"),
    ]
    payload = [res["gzip_blob_t"]]
    frame = Frame(header=header, payload=payload)
    res["gzip_frame"] = frame.serialize()
    if out_dir:
        stem = base_name or os.path.splitext(os.path.basename(path))[0]
        frame_gz_path = os.path.join(out_dir, f"{stem}.frame.gzip.txt")
        with open(frame_gz_path, "w", encoding="utf-8") as f:
            f.write(res["gzip_frame"])
        res["out_frame_gzip"] = frame_gz_path
    return res

def decompress_blob_t(trits_text_path: str, codec: str, out_dir: str, base_name: str | None = None) -> Dict[str, Any]:
    """Decode BLOB-T trits text back to bytes and decompress via codec (gzip|zlib)."""
    if not os.path.exists(trits_text_path):
        raise FileNotFoundError(trits_text_path)
    with open(trits_text_path, "r", encoding="utf-8") as f:
        trits_text = f.read()
    # Sanitize: keep only valid trit symbols and mode markers
    allowed = set(["≗","⊙","⊗","Φ","⊛"])  # MODE_NUM + trit alphabet
    trits_text = "".join(ch for ch in trits_text if ch in allowed).strip()
    if trits_text.startswith("≗Φ⊙"):
        trits_body = trits_text[len("≗Φ⊙"):]
    else:
        trits_body = trits_text
    # Ensure only trit symbols remain in body
    trit_set = set(["⊙","⊗","Φ","⊛"])  # include reserved
    trits_body = "".join(ch for ch in trits_body if ch in trit_set)
    blob_bytes = trits_to_bytes(trits_body)
    stem = base_name or os.path.splitext(os.path.basename(trits_text_path))[0]
    os.makedirs(out_dir, exist_ok=True)
    blob_out = os.path.join(out_dir, f"{stem}.blob.bin")
    with open(blob_out, "wb") as f:
        f.write(blob_bytes)
    codec_l = codec.lower()
    if codec_l == "gzip":
        decompressed = gzip.decompress(blob_bytes)
    elif codec_l == "zlib":
        decompressed = zlib.decompress(blob_bytes)
    else:
        raise ValueError("Unsupported codec. Use 'gzip' or 'zlib'.")
    dec_out = os.path.join(out_dir, f"{stem}.decompressed")
    with open(dec_out, "wb") as f:
        f.write(decompressed)
    return {"blob_bytes": len(blob_bytes), "decompressed_bytes": len(decompressed), "paths": {"blob": blob_out, "decompressed": dec_out}}
