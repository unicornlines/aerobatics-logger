#!/usr/bin/env python3
"""Volume, size and PETG mass of every STL in case/out (ASCII or binary STL)."""
import struct, sys
from pathlib import Path

RHO = 1.27  # g/cm3, PETG
FILL = 0.85  # walls here are thin: most of each part prints solid

def tris(p):
    b = p.read_bytes()
    if b[:5] == b"solid" and b"facet" in b[:400]:
        v = [tuple(map(float, l.split()[1:])) for l in b.decode().splitlines() if l.strip().startswith("vertex")]
        return [v[i:i + 3] for i in range(0, len(v), 3)]
    n = struct.unpack("<I", b[80:84])[0]
    return [[struct.unpack("<3f", b[84 + 50 * i + 12 + 12 * k: 84 + 50 * i + 24 + 12 * k]) for k in range(3)] for i in range(n)]

def main(d):
    total = 0
    for p in sorted(Path(d).glob("*.stl")):
        t = tris(p)
        vol = sum((a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6 for a, b, c in t)
        xs = [v[0] for tr in t for v in tr]; ys = [v[1] for tr in t for v in tr]; zs = [v[2] for tr in t for v in tr]
        g = abs(vol) / 1000 * RHO * FILL
        total += g
        print(f"{p.stem:10s} {abs(vol)/1000:7.1f} cm3  ~{g:5.1f} g   {max(xs)-min(xs):6.1f} x {max(ys)-min(ys):5.1f} x {max(zs)-min(zs):5.1f} mm")
    print(f"{'total':10s} {'':12s} ~{total:5.1f} g PETG")

main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "out")
