from src.frames import bytes_to_trits, trits_to_bytes
import os, gzip, zlib, binascii

def check(name, data: bytes):
    trits = bytes_to_trits(data)
    back = trits_to_bytes(trits)
    ok = back == data
    print(f"[{name}] len={len(data)} roundtrip_ok={ok}")
    if not ok:
        mismatches = sum(1 for a,b in zip(back,data) if a!=b)
        print(f"  mismatches={mismatches}")
        print(f"  head back={binascii.hexlify(back[:32])}")
        print(f"  head orig={binascii.hexlify(data[:32])}")

if __name__ == '__main__':
    # Random
    check('random-1k', os.urandom(1024))
    # Zlib
    raw = os.urandom(4096)
    zl = zlib.compress(raw, level=9)
    check('zlib', zl)
    try:
        assert zlib.decompress(trits_to_bytes(bytes_to_trits(zl))) == raw
        print('[zlib] decompress_ok=True')
    except Exception as e:
        print('[zlib] decompress_ok=False', e)
    # Gzip
    gz = gzip.compress(raw)
    check('gzip', gz)
    try:
        assert gzip.decompress(trits_to_bytes(bytes_to_trits(gz))) == raw
        print('[gzip] decompress_ok=True')
    except Exception as e:
        print('[gzip] decompress_ok=False', e)
