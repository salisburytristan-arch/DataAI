import argparse
from src.tasks import list_tasks, run_task
from src.data_loader import DataLoader
from src.numeric import decode_decimal_t
from src.compaction import compress_file, decompress_blob_t
from src.numeric import decode_float_t
from src.numeric import float_t_value
from src.numeric import encode_int_u3
from src.extdict import DictionaryAllocator, enumerate_free_combos
from src.frames import trits_to_bytes, Frame
from src.meta_frames import (
    build_grammar_frame,
    build_schema_frame,
    build_explain_frame,
    build_task_frame,
    build_caps_frame,
    build_error_frame,
    build_tensor_frame,
    build_dict_update_enhanced,
    build_train_pair_frame,
    build_dict_policy_frame,
)
from src.canonicalize import canonicalize_string, is_canonical
from src.errors import ParseError
from src.vault_ops import (
    vault_ingest,
    vault_reindex,
    vault_verify,
    vault_snapshot,
    vault_restore,
)
from src.orchestrator import run_distillation_job
from src import retriever as retr
from src.embeddings import hash_embed

def main():
    parser = argparse.ArgumentParser(description="ForgeNumerics-S Learning Tool CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List available tasks")

    p_u3 = sub.add_parser("practice-int-u3", help="Practice INT-U3 encoding/decoding")
    p_u3.add_argument("--value", required=True, type=int)

    p_s3 = sub.add_parser("practice-int-s3", help="Practice INT-S3 encoding/decoding")
    p_s3.add_argument("--value", required=True, type=int)

    p_dec = sub.add_parser("practice-decimal-t", help="Practice DECIMAL-T encode/decode")
    p_dec.add_argument("--sign-positive", action="store_true", help="Use positive sign (default negative if not provided)")
    p_dec.add_argument("--scale", required=True, type=int, help="Number of decimal digits")
    p_dec.add_argument("--integer", required=True, type=int, help="Integer digits without decimal point (magnitude)")

    p_frame = sub.add_parser("practice-frame-measurement", help="Build/parse a MEASUREMENT frame using DECIMAL-T value")
    p_frame.add_argument("--unit", default="meter")
    p_frame.add_argument("--sign-positive", action="store_true")
    p_frame.add_argument("--scale", required=True, type=int)
    p_frame.add_argument("--integer", required=True, type=int)

    p_float = sub.add_parser("practice-float-t", help="Practice FLOAT-T encode/decode (fixed widths from config)")
    p_float.add_argument("--sign-positive", action="store_true")
    p_float.add_argument("--exponent", required=True, type=int)
    p_float.add_argument("--mantissa", required=True, help="Mantissa trits string (⊙⊗Φ) of configured width")

    p_comp = sub.add_parser("compress-file", help="Compress a file (gzip/zlib) and emit BLOB-T + frame")
    p_comp.add_argument("--file", required=True, help="Path to text/binary file to compress")
    p_comp.add_argument("--out-dir", default="out", help="Directory to write outputs")
    p_comp.add_argument("--base-name", default=None, help="Base name for output files (defaults to input stem)")

    dec = sub.add_parser("decompress-file", help="Decode BLOB-T trits and decompress")
    dec.add_argument("--blob-t", required=True, help="Path to BLOB-T trits text file")
    dec.add_argument("--codec", required=True, choices=["gzip", "zlib"], help="Compression codec used")
    dec.add_argument("--out-dir", required=True, help="Directory to write decoded outputs")
    dec.add_argument("--base-name", required=False)

    p_free = sub.add_parser("list-free-combos", help="List available free symbol combos")
    p_free.add_argument("--limit", type=int, default=100, help="Max number to show")

    p_alloc = sub.add_parser("allocate-word", help="Allocate a word to an extension dictionary")
    p_alloc.add_argument("--word", required=True, help="Word to allocate")
    p_alloc.add_argument("--extdict", required=True, help="Extension dictionary ID (e.g., EXTDICT_SITE_A_0001)")
    p_alloc.add_argument("--combo", required=False, help="Force specific combo (optional)")

    p_show = sub.add_parser("show-extdict", help="Show contents of an extension dictionary")
    p_show.add_argument("--extdict", required=True, help="Extension dictionary ID")

    p_dict_update = sub.add_parser("generate-dict-update", help="Generate DICT_UPDATE frame for recent allocations")
    p_dict_update.add_argument("--extdict", required=True, help="Extension dictionary ID")
    p_dict_update.add_argument("--limit", type=int, default=10, help="Number of recent allocations to include")

    p_vec = sub.add_parser("practice-vector", help="Build a VECTOR frame from numeric tokens")
    p_vec.add_argument("--values", nargs="+", required=True, help="List of numeric tokens")

    p_mat = sub.add_parser("practice-matrix", help="Build a MATRIX frame (pass rows as JSON)")
    p_mat.add_argument("--rows", required=True, help="JSON array of rows, e.g., '[[\"≗⊙⊙⊗\",\"≗⊙⊙Φ\"],[\"≗⊙⊙⊙\",\"≗⊙⊙⊗\"]]'")

    p_log = sub.add_parser("practice-log", help="Build a LOG frame")
    p_log.add_argument("--severity", required=True, help="Severity level (INFO, WARN, ERROR)")
    p_log.add_argument("--message", required=True, help="Log message")
    p_log.add_argument("--timestamp", help="Optional timestamp (numeric token)")
    p_log.add_argument("--details", help="Optional details string")

    p_fact = sub.add_parser("practice-fact", help="Build a FACT frame (knowledge triple)")
    p_fact.add_argument("--subject", required=True, help="Subject token")
    p_fact.add_argument("--predicate", required=True, help="Predicate token")
    p_fact.add_argument("--object", required=True, help="Object token")
    p_fact.add_argument("--confidence", help="Optional confidence score (numeric token)")
    p_fact.add_argument("--source", help="Optional source identifier")

    # Meta-frame commands
    p_grammar = sub.add_parser("build-grammar-frame", help="Wrap EBNF grammar file into GRAMMAR frame")
    p_grammar.add_argument("--file", required=True, help="Path to EBNF grammar file")
    p_grammar.add_argument("--version", default="2.0", help="Grammar/version tag")

    p_schema = sub.add_parser("build-schema", help="Create SCHEMA frame from fields JSON")
    p_schema.add_argument("--target-type", required=True, help="Target frame TYPE (e.g., MEASUREMENT)")
    p_schema.add_argument("--fields-json", required=True, help="Path to JSON list of field specs")
    p_schema.add_argument("--description", help="Optional schema description")
    p_schema.add_argument("--json", action="store_true", help="Emit JSON instead of serialized text")

    p_explain = sub.add_parser("build-explain", help="Create EXPLAIN frame")
    p_explain.add_argument("--target-id", required=True)
    p_explain.add_argument("--summary", required=True)
    p_explain.add_argument("--details", nargs="*", help="Optional detail lines")
    p_explain.add_argument("--json", action="store_true")

    p_task = sub.add_parser("build-task", help="Create TASK frame")
    p_task.add_argument("--task-type", required=True)
    p_task.add_argument("--instruction", required=True)
    p_task.add_argument("--input", required=True, help="Input data")
    p_task.add_argument("--expected", required=True, help="Expected output token/frame")
    p_task.add_argument("--difficulty", default="BASIC")
    p_task.add_argument("--json", action="store_true")

    p_caps = sub.add_parser("build-caps", help="Create CAPS frame (supports & limits)")
    p_caps.add_argument("--supports", nargs="+", required=True, help="List like FEATURE=YES/NO")
    p_caps.add_argument("--limits", nargs="*", help="List like MAX_TENSOR_SIZE=100000")
    p_caps.add_argument("--json", action="store_true")

    p_error = sub.add_parser("build-error", help="Create ERROR frame")
    p_error.add_argument("--error-type", required=True)
    p_error.add_argument("--location", required=True)
    p_error.add_argument("--code", required=True)
    p_error.add_argument("--detail", required=True)
    p_error.add_argument("--suggestion", help="Optional recovery suggestion")
    p_error.add_argument("--json", action="store_true")

    p_tensor = sub.add_parser("build-tensor", help="Create TENSOR frame")
    p_tensor.add_argument("--dtype", required=True, help="Data type token (e.g., INT_U3)")
    p_tensor.add_argument("--shape", required=True, help="Comma-separated dimensions, e.g., 2,3,4")
    p_tensor.add_argument("--data", nargs="+", required=True, help="Flattened data tokens")
    p_tensor.add_argument("--order", default="ROW_MAJOR")
    p_tensor.add_argument("--json", action="store_true")

    p_train_pair = sub.add_parser("build-train-pair", help="Create TRAIN_PAIR frame")
    p_train_pair.add_argument("--nl", required=True, help="Natural language text")
    p_train_pair.add_argument("--forge", required=True, help="ForgeNumerics frame or tokens")
    p_train_pair.add_argument("--json", action="store_true")

    p_dict_policy = sub.add_parser("build-dict-policy", help="Create DICT_POLICY frame")
    p_dict_policy.add_argument("--min-freq", type=int, required=True)
    p_dict_policy.add_argument("--domains", nargs="+", required=True, help="Allowed domains list")
    p_dict_policy.add_argument("--max-growth", type=int, required=True, help="Max growth per day")
    p_dict_policy.add_argument("--json", action="store_true")

    p_dict_update_e = sub.add_parser("build-dict-update-enhanced", help="Create enhanced DICT_UPDATE frame")
    p_dict_update_e.add_argument("--extdict-id", required=True)
    p_dict_update_e.add_argument("--pairs", nargs="+", required=True, help="Word=Combo entries")
    p_dict_update_e.add_argument("--stats", nargs="*", help="freq:source entries matching pairs order")
    p_dict_update_e.add_argument("--json", action="store_true")
    
    # New validation/canonicalization commands
    p_validate = sub.add_parser("validate", help="Validate a frame string (parse + structure checks)")
    p_validate.add_argument("--frame", required=True, help="Frame string to validate")
    
    p_canonicalize = sub.add_parser("canonicalize", help="Canonicalize a frame string")
    p_canonicalize.add_argument("--frame", required=True, help="Frame string to canonicalize")
    p_canonicalize.add_argument("--file", help="Alternatively, read frame from file")
    
    p_diff = sub.add_parser("diff", help="Compare two frame strings (bytewise or semantic)")
    p_diff.add_argument("--frame1", help="First frame string")
    p_diff.add_argument("--file1", help="Or read first frame from file")
    p_diff.add_argument("--frame2", help="Second frame string")
    p_diff.add_argument("--file2", help="Or read second frame from file")
    p_diff.add_argument("--semantic", action="store_true", help="Compare canonical forms instead of raw bytes")

    # Vault operations
    p_v_ingest = sub.add_parser("vault-ingest", help="Ingest files into Vault (stub)")
    p_v_ingest.add_argument("--path", required=True, help="Path to source directory")

    p_v_reindex = sub.add_parser("vault-reindex", help="Reindex Vault store (stub)")
    p_v_reindex.add_argument("--store", required=True, help="Path to Vault store")

    p_v_verify = sub.add_parser("vault-verify", help="Verify Vault integrity (stub)")
    p_v_verify.add_argument("--store", required=True, help="Path to Vault store")

    p_v_snapshot = sub.add_parser("vault-snapshot", help="Snapshot Vault store (stub)")
    p_v_snapshot.add_argument("--store", required=True, help="Path to Vault store")
    p_v_snapshot.add_argument("--out-dir", required=True, help="Directory to write snapshot")

    p_v_restore = sub.add_parser("vault-restore", help="Restore Vault snapshot (stub)")
    p_v_restore.add_argument("--snapshot", required=True, help="Path to snapshot directory")
    p_v_restore.add_argument("--store", required=True, help="Path to Vault store")

    # Orchestrator distillation job
    p_distill = sub.add_parser("orchestrator-distill", help="Run distillation over tasks JSON (stub)")
    p_distill.add_argument("--project-id", required=True, help="Project identifier")
    p_distill.add_argument("--tasks-json", required=True, help="Path to JSON array of tasks")
    p_distill.add_argument("--out-dir", required=True, help="Output directory for JSONL and Forge frames")
    p_distill.add_argument("--max-turns", type=int)
    p_distill.add_argument("--index", help="Path to index JSON for evidence retrieval")
    p_distill.add_argument("--query-embedding", help="Path to JSON list/array of floats for query embedding (optional)")
    p_distill.add_argument("--embed-index", help="Path to embeddings sidecar JSON (path, chunk_id, embedding)")
    p_distill.add_argument("--hash-embedding-dim", type=int, default=None, help="If set, auto-generate hash embedding for queries")

    # Build/search index
    p_build_idx = sub.add_parser("vault-build-index", help="Build text index over a directory and save to JSON")
    p_build_idx.add_argument("--source", required=True, help="Directory to index (.md/.txt)")
    p_build_idx.add_argument("--out", required=True, help="Path to write index JSON")
    p_build_idx.add_argument("--max-chars", type=int, default=600)
    p_build_idx.add_argument("--hash-embedding-dim", type=int, default=None, help="If set, also write a hash embedding sidecar JSON")

    p_search = sub.add_parser("vault-search", help="Search an index JSON and return top-K evidence")
    p_search.add_argument("--index", required=True, help="Path to index JSON")
    p_search.add_argument("--query", required=True, help="Query string")
    p_search.add_argument("--k", type=int, default=6)
    p_search.add_argument("--embed-index", help="Path to embeddings sidecar JSON (path, chunk_id, embedding)")
    p_search.add_argument("--query-embedding", help="Path to JSON list/array of floats for query embedding (optional)")
    p_search.add_argument("--hash-embedding-dim", type=int, default=None, help="If set, auto-generate hash embedding for the query")
    
    def frame_to_json(frame):
        return {
            "header": [{"key": k, "value": v} for (k, v) in frame.header],
            "payload": frame.payload,
            "serialized": frame.serialize(),
        }

    args = parser.parse_args()

    if args.cmd == "list":
        for name, desc in list_tasks().items():
            print(f"{name}: {desc}")
    elif args.cmd == "practice-int-u3":
        res = run_task("int-u3", value=args.value)
        print(res)
    elif args.cmd == "practice-int-s3":
        res = run_task("int-s3", value=args.value)
        print(res)
    elif args.cmd == "practice-decimal-t":
        # default sign to False if flag not set
        res = run_task("decimal-t", sign_positive=bool(args.sign_positive), scale=args.scale, integer_value=args.integer)
        # pretty print human value
        sp, sc, iv = res["decoded"]
        sign = 1 if sp else -1
        value = sign * iv * (10 ** (-sc))
        print({**res, "value": value})
    elif args.cmd == "practice-frame-measurement":
        dl = DataLoader()
        defaults = dl.defaults()
        unit = args.unit or defaults.get("unit", "meter")
        res = run_task(
            "frame-measurement",
            unit=unit,
            sign_positive=bool(args.sign_positive),
            scale=args.scale,
            integer_value=args.integer,
        )
        print(res)
    elif args.cmd == "practice-float-t":
        dl = DataLoader()
        defaults = dl.defaults()
        numeric_cfg = (defaults and {})
        # Load widths from config via DataLoader directly
        cfg = dl._load_config() or {}
        exp_width = cfg.get("numeric", {}).get("float_t", {}).get("exponent_trits", 10)
        man_width = cfg.get("numeric", {}).get("float_t", {}).get("mantissa_trits", 20)
        res = run_task("float-t", sign_positive=bool(args.sign_positive), exponent=args.exponent, mantissa=args.mantissa, exp_width=exp_width, man_width=man_width)
        print(res)
        try:
            val = float_t_value(bool(args.sign_positive), args.exponent, args.mantissa)
            print(f"Approximate numeric value: {val}")
        except Exception as e:
            print(f"Could not compute numeric value: {e}")
    elif args.cmd == "compress-file":
        res = compress_file(args.file, out_dir=args.out_dir, base_name=args.base_name)
        print({k: res[k] for k in [
            "original_bytes","gzip_bytes","zlib_bytes","gzip_ratio","zlib_ratio"
        ]})
        print({"gzip_frame_len": len(res["gzip_frame"])})
        for k in ["out_raw","out_gzip","out_zlib","out_blob_gzip","out_blob_zlib","out_frame_gzip"]:
            if k in res:
                print({k: res[k]})
    elif args.cmd == "decompress-file":
        res = decompress_blob_t(args.blob_t, args.codec, args.out_dir, base_name=args.base_name)
        print(res)
    elif args.cmd == "list-free-combos":
        free = enumerate_free_combos(limit=args.limit)
        print(f"Free symbol combos (showing {len(free)} of available):")
        for i, combo in enumerate(free, 1):
            print(f"  {i}. {combo}")
    elif args.cmd == "allocate-word":
        allocator = DictionaryAllocator()
        combo = allocator.allocate_word(args.word, args.extdict, force_combo=args.combo)
        if combo:
            print(f"✓ Allocated: {args.word} → {combo} in {args.extdict}")
        else:
            print(f"✗ Failed to allocate {args.word} (may already exist or combo unavailable)")
    elif args.cmd == "show-extdict":
        allocator = DictionaryAllocator()
        extdict = allocator.load_extdict(args.extdict)
        entries = extdict.get_entries()
        print(f"Extension Dictionary: {args.extdict}")
        print(f"Entry count: {len(entries)}")
        for word, combo in sorted(entries):
            print(f"  {word} → {combo}")
    elif args.cmd == "generate-dict-update":
        allocator = DictionaryAllocator()
        extdict = allocator.load_extdict(args.extdict)
        entries = extdict.get_entries()
        # Take most recent N entries
        recent = entries[-args.limit:] if len(entries) > args.limit else entries
        frame = allocator.make_dict_update_frame(args.extdict, recent)
        serialized = frame.serialize()
        print(f"DICT_UPDATE frame for {args.extdict}:")
        print(serialized)
    elif args.cmd == "practice-vector":
        res = run_task("schema-vector", values=args.values)
        print(f"Serialized: {res['serialized']}")
        print(f"Parsed values: {res['parsed']}")
    elif args.cmd == "practice-matrix":
        import json
        rows = json.loads(args.rows)
        res = run_task("schema-matrix", rows=rows)
        print(f"Serialized: {res['serialized']}")
        print(f"Parsed matrix:")
        for i, row in enumerate(res['parsed']):
            print(f"  Row {i}: {row}")
    elif args.cmd == "practice-log":
        res = run_task("schema-log", 
                      severity=args.severity,
                      message=args.message,
                      timestamp=args.timestamp,
                      details=args.details)
        print(f"Serialized: {res['serialized']}")
        print(f"Parsed: {res['parsed']}")
    elif args.cmd == "practice-fact":
        res = run_task("schema-fact",
                      subject=args.subject,
                      predicate=args.predicate,
                      obj=args.object,
                      confidence=args.confidence,
                      source=args.source)
        print(f"Serialized: {res['serialized']}")
        print(f"Parsed: {res['parsed']}")
    elif args.cmd == "build-grammar-frame":
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        frame = build_grammar_frame(content, version=args.version)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-schema":
        import json
        with open(args.fields_json, 'r', encoding='utf-8') as f:
            fields = json.load(f)
        frame = build_schema_frame(args.target_type, fields, description=args.description)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-explain":
        frame = build_explain_frame(args.target_id, args.summary, details=args.details)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-task":
        frame = build_task_frame(args.task_type, args.instruction, args.input, args.expected, args.difficulty)
        print(frame.serialize())
    elif args.cmd == "build-caps":
        supports = {}
        for item in args.supports:
            if '=' in item:
                k, v = item.split('=', 1)
                supports[k.strip()] = v.strip()
        limits = {}
        if args.limits:
            for item in args.limits:
                if '=' in item:
                    k, v = item.split('=', 1)
                    try:
                        limits[k.strip()] = encode_int_u3(int(v))
                    except Exception:
                        limits[k.strip()] = v.strip()
        frame = build_caps_frame(supports, limits)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-error":
        frame = build_error_frame(args.error_type, args.location, args.code, args.detail, suggestion=args.suggestion)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-tensor":
        shape = [int(x) for x in args.shape.split(',') if x.strip()]
        frame = build_tensor_frame(args.dtype, shape, args.data, order=args.order)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-train-pair":
        frame = build_train_pair_frame(args.nl, args.forge)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-dict-policy":
        frame = build_dict_policy_frame(args.min_freq, args.domains, args.max_growth)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "build-dict-update-enhanced":
        pairs = []
        for p in args.pairs:
            if '=' in p:
                w, c = p.split('=', 1)
                pairs.append((w, c))
        stats = []
        if args.stats:
            for s in args.stats:
                if ':' in s:
                    fstr, source = s.split(':', 1)
                    try:
                        freq = int(fstr)
                    except Exception:
                        freq = 0
                    stats.append({"freq": freq, "source": source})
        # If stats shorter than pairs, pad
        while len(stats) < len(pairs):
            stats.append({"freq": 0, "source": "UNKNOWN"})
        frame = build_dict_update_enhanced(args.extdict_id, pairs, stats)
        if args.json:
            import json
            print(json.dumps(frame_to_json(frame), ensure_ascii=False))
        else:
            print(frame.serialize())
    elif args.cmd == "verify-blob-t":
        # Read text, strip prefix if present, decode to bytes
        import binascii
        with open(args.blob_t, 'r', encoding='utf-8') as f:
            t = f.read().strip()
        if t.startswith('≗Φ⊙'):
            t = t[3:]
        dec = trits_to_bytes(t)
        # Load reference
        with open(args.reference, 'rb') as f:
            ref = f.read()
        equal = dec == ref
        mismatches = 0 if equal else sum(1 for a,b in zip(dec, ref) if a!=b)
        print({
            "equal": equal,
            "decoded_len": len(dec),
            "reference_len": len(ref),
            "mismatches": mismatches,
            "decoded_head_hex": binascii.hexlify(dec[:32]).decode('ascii'),
            "reference_head_hex": binascii.hexlify(ref[:32]).decode('ascii'),
        })
    elif args.cmd == "generate-curriculum":
        import os
        from src.curriculum import build_basic_curriculum, build_full_curriculum, write_curriculum, write_curriculum_json
        os.makedirs(args.out_dir, exist_ok=True)
        basic = build_basic_curriculum()
        full = build_full_curriculum(args.size)
        basic_path = os.path.join(args.out_dir, 'forge_curriculum_basic.txt')
        full_path = os.path.join(args.out_dir, 'forge_curriculum_full.txt')
        write_curriculum(basic_path, basic)
        write_curriculum(full_path, full)
        out = {"basic_path": basic_path, "basic_count": len(basic), "full_path": full_path, "full_count": len(full)}
        if args.json:
            json_path = os.path.join(args.out_dir, 'forge_curriculum_full.json')
            write_curriculum_json(json_path, full)
            out["json_path"] = json_path
        print(out)
    elif args.cmd == "verify-corpus":
        import json
        from src.validator import validate_corpus
        with open(args.file, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        schema_map = None
        if args.schemas_json:
            with open(args.schemas_json, 'r', encoding='utf-8') as sf:
                schema_map = json.load(sf)
        res = validate_corpus(corpus, schema_map=schema_map)
        print(res)
    elif args.cmd == "export-splits":
        import json, os, random
        os.makedirs(args.out_dir, exist_ok=True)
        with open(args.file, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        random.seed(args.seed)
        items = corpus[:]
        random.shuffle(items)
        n = len(items)
        n_train = int(n * args.train)
        n_valid = int(n * args.valid)
        train = items[:n_train]
        valid = items[n_train:n_train+n_valid]
        test = items[n_train+n_valid:]
        def write_jsonl(path, arr):
            with open(path, 'w', encoding='utf-8') as f:
                for obj in arr:
                    f.write(json.dumps(obj, ensure_ascii=False))
                    f.write('\n')
        train_p = os.path.join(args.out_dir, 'train.jsonl')
        valid_p = os.path.join(args.out_dir, 'valid.jsonl')
        test_p = os.path.join(args.out_dir, 'test.jsonl')
        write_jsonl(train_p, train)
        write_jsonl(valid_p, valid)
        write_jsonl(test_p, test)
        print({"counts": {"train": len(train), "valid": len(valid), "test": len(test)}, "paths": {"train": train_p, "valid": valid_p, "test": test_p}})
    elif args.cmd == "validate":
        try:
            frame = Frame.parse(args.frame)
            print({
                "valid": True,
                "frame": frame_to_json(frame),
                "message": "Frame parsed successfully"
            })
        except ParseError as e:
            print({
                "valid": False,
                "error_code": str(e.code),
                "message": e.message,
                "location": str(e.location) if e.location else None,
                "context": e.context,
                "suggestion": e.suggestion
            })
        except Exception as e:
            print({
                "valid": False,
                "error_code": "UNKNOWN",
                "message": str(e)
            })
    elif args.cmd == "canonicalize":
        input_frame = None
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_frame = f.read()
        elif args.frame:
            input_frame = args.frame
        if not input_frame:
            print({"error": "Must provide --frame or --file"})
            return
        try:
            canonical = canonicalize_string(input_frame)
            was_canonical = is_canonical(input_frame)
            print({
                "original": input_frame.strip(),
                "canonical": canonical,
                "was_canonical": was_canonical,
                "changed": input_frame.strip() != canonical
            })
        except ParseError as e:
            print({
                "error": str(e.code),
                "message": e.message,
                "suggestion": e.suggestion
            })
        except Exception as e:
            print({"error": str(e)})
    elif args.cmd == "diff":
        frame1_str = None
        frame2_str = None
        if args.file1:
            with open(args.file1, 'r', encoding='utf-8') as f:
                frame1_str = f.read().strip()
        elif args.frame1:
            frame1_str = args.frame1.strip()
        if args.file2:
            with open(args.file2, 'r', encoding='utf-8') as f:
                frame2_str = f.read().strip()
        elif args.frame2:
            frame2_str = args.frame2.strip()
        if not frame1_str or not frame2_str:
            print({"error": "Must provide both frames (--frame1/--file1 and --frame2/--file2)"})
            return
        try:
            if args.semantic:
                # Compare canonical forms
                c1 = canonicalize_string(frame1_str)
                c2 = canonicalize_string(frame2_str)
                identical = c1 == c2
                print({
                    "semantic_identical": identical,
                    "canonical_1": c1,
                    "canonical_2": c2
                })
            else:
                # Bytewise comparison
                identical = frame1_str == frame2_str
                print({
                    "bytewise_identical": identical,
                    "length_1": len(frame1_str),
                    "length_2": len(frame2_str),
                    "frame_1": frame1_str[:100] + "..." if len(frame1_str) > 100 else frame1_str,
                    "frame_2": frame2_str[:100] + "..." if len(frame2_str) > 100 else frame2_str
                })
        except ParseError as e:
            print({
                "error": str(e.code),
                "message": e.message
            })
        except Exception as e:
            print({"error": str(e)})
    elif args.cmd == "vault-ingest":
        res = vault_ingest(args.path)
        print(res)
    elif args.cmd == "vault-reindex":
        res = vault_reindex(args.store)
        print(res)
    elif args.cmd == "vault-verify":
        res = vault_verify(args.store)
        print(res)
    elif args.cmd == "vault-snapshot":
        res = vault_snapshot(args.store, args.out_dir)
        print(res)
    elif args.cmd == "vault-restore":
        res = vault_restore(args.snapshot, args.store)
        print(res)
    elif args.cmd == "orchestrator-distill":
        import json
        with open(args.tasks_json, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        # Simple student and teachers (stubs)
        def student(prompt: str) -> str:
            return "".join([
                "Final answer based on prompt sections.\n",
                "(Stub) This would be generated by a local or remote model.\n",
            ])

        def teacher_reasoning(draft: str, evidence: list) -> dict:
            return {"role": "reasoning", "suggestion": draft, "citations": list(range(1, len(evidence)+1))}

        def teacher_verifier(draft: str, evidence: list) -> dict:
            return {"role": "verifier", "citations": list(range(1, len(evidence)+1))}

        def retriever(query: str, k: int) -> list:
            # Use provided index if available; else try adjacent to tasks JSON
            import os
            idx_path = args.index or os.path.join(os.path.dirname(args.tasks_json), 'vault_index.json')
            evidence_items: list = []
            try:
                if os.path.exists(idx_path):
                    idx = retr.load_index(idx_path)
                    if args.embed_index and os.path.exists(args.embed_index):
                        idx = retr.attach_embeddings(idx, args.embed_index)
                    q_emb = None
                    if args.query_embedding and os.path.exists(args.query_embedding):
                        import json as _json
                        with open(args.query_embedding, 'r', encoding='utf-8') as ef:
                            q_emb = _json.load(ef)
                    elif args.hash_embedding_dim:
                        q_emb = hash_embed(query, dim=args.hash_embedding_dim)
                    evidence_items = retr.search(idx, query, k, query_embedding=q_emb)
            except Exception:
                evidence_items = []
            return evidence_items

        out = run_distillation_job(
            project_id=args.project_id,
            tasks=tasks,
            student_client=student,
            retriever=retriever,
            teachers=[teacher_reasoning, teacher_verifier],
            out_dir=args.out_dir,
            max_turns=args.max_turns,
        )
        print(out)
    elif args.cmd == "vault-build-index":
        idx = retr.build_index(args.source, max_chars=args.max_chars)
        outp = retr.save_index(idx, args.out)
        out = {"index_path": outp, "doc_count": idx.get("doc_count")}
        if args.hash_embedding_dim:
            emb = retr.build_hash_embeddings(idx, dim=args.hash_embedding_dim)
            emb_path = args.out + ".embeddings.json"
            emb_out = retr.save_embeddings(emb, emb_path)
            out["embedding_sidecar"] = emb_out
        print(out)
    elif args.cmd == "vault-search":
        idx = retr.load_index(args.index)
        if args.embed_index:
            import os
            if os.path.exists(args.embed_index):
                idx = retr.attach_embeddings(idx, args.embed_index)
        q_emb = None
        if args.query_embedding:
            import os
            if os.path.exists(args.query_embedding):
                import json as _json
                with open(args.query_embedding, 'r', encoding='utf-8') as ef:
                    q_emb = _json.load(ef)
        elif args.hash_embedding_dim:
            q_emb = hash_embed(args.query, dim=args.hash_embedding_dim)
        results = retr.search(idx, args.query, args.k, query_embedding=q_emb)
        print({"count": len(results), "items": results})
if __name__ == "__main__":
    main()
