from src.frames import bytes_to_trits, trits_to_bytes
import os
import zlib, gzip

def test_blob_roundtrip_random_bytes():
    data = os.urandom(1024)
    trits = bytes_to_trits(data)
    back = trits_to_bytes(trits)
    assert back == data

def test_blob_roundtrip_zlib():
    raw = os.urandom(4096)
    zl = zlib.compress(raw, level=9)
    trits = bytes_to_trits(zl)
    back = trits_to_bytes(trits)
    assert back == zl
    assert zlib.decompress(back) == raw

def test_blob_roundtrip_gzip():
    raw = os.urandom(4096)
    gz = gzip.compress(raw)
    trits = bytes_to_trits(gz)
    back = trits_to_bytes(trits)
    assert back == gz
    assert gzip.decompress(back) == raw
