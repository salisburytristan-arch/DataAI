"""
Validator utilities for ForgeNumerics-S:
- Frame parse/serialize round-trip checks
- Basic SCHEMA-driven header/payload validation (extensible)
- Grammar presence flag (placeholder; EBNF-driven checks can be added)
"""
from typing import List, Dict, Any, Tuple
from src.frames import Frame


def parse_roundtrip_ok(serialized: str) -> Tuple[bool, str]:
    try:
        fr = Frame.parse(serialized)
        s2 = fr.serialize()
        # Allow minor whitespace differences; compare normalized
        ok = serialized.strip() == s2.strip()
        return ok, s2
    except Exception as e:
        return False, f"parse_error: {e}"


def validate_against_schema(fr: Frame, schema: Dict[str, Any] | None) -> List[str]:
    """Basic validation: ensure required header keys exist and payload markers appear.
    Schema format (from SCHEMA meta-frame) example:
      {
        "TARGET_TYPE": "MEASUREMENT",
        "FIELDS": [
          {"name": "VALUE", "required": True},
          {"name": "UNIT", "required": True}
        ]
      }
    """
    errors: List[str] = []
    if not schema:
        return errors
    # Check TYPE matches
    t = next((v for (k, v) in fr.header if k == "TYPE"), None)
    target = schema.get("TARGET_TYPE")
    if target and t != target:
        errors.append(f"TYPE_MISMATCH expected={target} got={t}")
    # Required fields presence (payload markers)
    required = [f.get("name") for f in schema.get("FIELDS", []) if str(f.get("required", False)).upper() == "TRUE"]
    for name in required:
        marker = f"≛{name}"
        if marker not in fr.payload:
            errors.append(f"MISSING_REQUIRED_FIELD {name}")
    return errors


def validate_corpus(entries: List[Dict[str, Any]], schema_map: Dict[str, Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Validate a corpus JSON list of {header,payload,serialized} objects.
    Returns summary with counts and first few errors.
    """
    total = len(entries)
    ok_parse = 0
    ok_roundtrip = 0
    schema_errors: List[str] = []
    first_errors: List[str] = []
    for e in entries:
        s = e.get("serialized", "")
        fr = None
        try:
            fr = Frame.parse(s)
            ok_parse += 1
        except Exception as ex:
            if len(first_errors) < 10:
                first_errors.append(f"parse_error: {ex}")
            continue
        s_ok, s2 = parse_roundtrip_ok(s)
        if s_ok:
            ok_roundtrip += 1
        else:
            if len(first_errors) < 10:
                first_errors.append("roundtrip_mismatch")
        # Schema validation by TYPE
        if schema_map:
            typ = next((v for (k, v) in fr.header if k == "TYPE"), None)
            sch = schema_map.get(typ) if typ else None
            errs = validate_against_schema(fr, sch)
            schema_errors.extend(errs)
    return {
        "total": total,
        "ok_parse": ok_parse,
        "ok_roundtrip": ok_roundtrip,
        "schema_error_count": len(schema_errors),
        "sample_errors": first_errors[:10],
    }
