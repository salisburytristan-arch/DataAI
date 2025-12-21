from src.frames import trits_to_bytes
import binascii
from pathlib import Path

def main():
    tpath = Path('out/Compaction_Test.blob_t.zlib.txt')
    opath = Path('out/Compaction_Test.zlib')
    t = tpath.read_text(encoding='utf-8')
    allowed = set(['≗','⊙','⊗','Φ','⊛'])
    t = ''.join(ch for ch in t if ch in allowed).strip()
    if t.startswith('≗Φ⊙'):
        t = t[3:]
    t = ''.join(ch for ch in t if ch in set(['⊙','⊗','Φ','⊛']))
    dec = trits_to_bytes(t)
    orig = opath.read_bytes()
    print('Decoded length:', len(dec), 'Original length:', len(orig))
    print('Lengths equal?', len(dec)==len(orig))
    print('Decoded head:', binascii.hexlify(dec[:32]))
    print('Original head:', binascii.hexlify(orig[:32]))
    mismatches = sum(1 for a,b in zip(dec,orig) if a!=b)
    print('Mismatches:', mismatches)

if __name__ == '__main__':
    main()
