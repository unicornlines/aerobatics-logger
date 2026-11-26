#!/usr/bin/env python3
"""Pack the render scene (assembled + exploded STLs) into one compact binary for the web viewer.
   python3 case/tools/pack_viewer.py case/viewer   -> index.html, model.txt (base64), model.json
Positions are deduplicated and stored as int16 in 0.01 mm; indices as uint32. Explode offsets come from
the exploded set (pure translations per piece)."""
import json, struct, sys
from pathlib import Path
import numpy as np
import build

SCENE = build.SCENE
out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
out.mkdir(parents=True, exist_ok=True)

def read_stl(p):
    txt = p.read_text()
    v = np.array([l.split()[1:4] for l in txt.splitlines() if l.lstrip().startswith("vertex")], dtype=np.float64)
    return v

blob, meta = bytearray(), []
for p in build.PIECES:
    a = SCENE / "assembled" / f"{p['name']}.stl"
    if not a.exists() or a.stat().st_size < 200:
        continue
    va = read_stl(a)
    if len(va) == 0:
        continue
    ve = read_stl(SCENE / "exploded" / f"{p['name']}.stl")
    off = (ve.min(0) - va.min(0)).round(2).tolist() if len(ve) else [0, 0, 0]
    q = np.round(va * 100).astype(np.int64)
    uniq, inv = np.unique(q, axis=0, return_inverse=True)
    pos = uniq.astype(np.int16).tobytes()
    idx = inv.astype(np.uint32).ravel().tobytes()
    while len(blob) % 4: blob.append(0)
    o1 = len(blob); blob += pos
    while len(blob) % 4: blob.append(0)
    o2 = len(blob); blob += idx
    meta.append({**{k: p[k] for k in p if k != "edges"}, "pos": [o1, len(uniq)], "idx": [o2, len(inv)], "explode": off})
    print(f"{p['name']:12s} {len(uniq):7d} verts {len(inv)//3:7d} tris  explode {off}")
import base64 as _b
(out / "model.txt").write_text(_b.b64encode(bytes(blob)).decode())
(out / "model.json").write_text(json.dumps(meta))
print(f"model {len(blob)/1e6:.2f} MB (base64 in model.txt)")

# the page: template + manifest + boot screen
import base64
tpl = (build.CASE / "viewer" / "template.html").read_text()
scr = "data:image/png;base64," + base64.b64encode((build.RENDER / "screen-boot.png").read_bytes()).decode()
(out / "index.html").write_text(tpl.replace("__META__", json.dumps(meta)).replace("__SCREEN__", scr))
print("index.html written")
