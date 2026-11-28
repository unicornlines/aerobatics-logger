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

# labels for the main board parts, read from the KiCad layout (refs -> what they are)
import re
BOARD_LABELS = {"U5": "MCU · STM32H723", "U12": "Flash 512 MB", "U6": "IMU · ICM-45686", "U9": "Magnetometer · BMM350",
    "U7": "Barometer · BMP390", "U17": "Humidity · SHT40", "MK1": "Microphone (back)", "U10": "GNSS · NEO-M9N",
    "U11": "Radio · ESP32-C6", "J50": "GNSS antenna", "J1": "USB-C", "J60": "microSD", "J2": "Battery",
    "U13": "Charger · BQ24074", "U3": "Buck · TPS62130", "U15": "Cell protection", "J63": "Qwiic", "J62": "Camera / marker",
    "J20": "SWD", "J61": "Display FPC"}
pcb = (build.CASE.parent / "hardware" / "kicad" / "logger.kicad_pcb").read_text()
bt = float(re.search(r"board_t = ([\d.]+);", (build.CASE / "board.scad").read_text()).group(1))
heights = {m.group(1): float(m.group(2)) for m in re.finditer(r'\["([^"]+)", "[FB]", \[[^\]]*\], ([\d.]+)\]', (build.CASE / "board.scad").read_text())}
blabels = []
for f in re.split(r"\n  \(footprint ", pcb)[1:]:
    ref = re.search(r'(?:fp_text reference|property "Reference") "([^"]+)"', f)
    if not ref or ref.group(1) not in BOARD_LABELS: continue
    r = ref.group(1); at = re.search(r"\(at ([\d.\-]+) ([\d.\-]+)", f); side = re.search(r'\(layer "([FB])\.Cu"\)', f).group(1)
    x, y = float(at.group(1)) - 100, 62 - (float(at.group(2)) - 100); h = heights.get(r, 1.0)
    blabels.append({"ref": r, "name": BOARD_LABELS[r], "p": [round(x, 2), round(y, 2), round(h if side == "F" else -bt - h, 2)], "side": side})
order = list(BOARD_LABELS); blabels.sort(key=lambda b: order.index(b["ref"]))
print(len(blabels), "board labels")

# the page: template + manifest + boot screen
import base64
tpl = (build.CASE / "viewer" / "template.html").read_text()
scr = "data:image/png;base64," + base64.b64encode((build.RENDER / "screen-boot.png").read_bytes()).decode()
(out / "index.html").write_text(tpl.replace("__META__", json.dumps(meta)).replace("__SCREEN__", scr).replace("__BLABELS__", json.dumps(blabels)))
print("index.html written")
