#!/usr/bin/env python3
"""Build everything for the case from the board:

    python3 case/tools/build.py            # print STLs + renders
    python3 case/tools/build.py --extract  # first re-read the board from KiCad
    python3 case/tools/build.py --no-render

Writes case/stl/*.stl (print orientation), case/renders/*.png and prints a mass estimate.
Needs openscad (2021.01 or newer), xvfb not needed; node + playwright for the renders.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
SCAD = CASE / "case.scad"
STL = CASE / "stl"
RENDER = CASE / "tools" / "render"
SCENE = RENDER / "scene"

PRINT_PARTS = ["front", "keybridge", "tray", "plate", "lcd_frame", "cap_up", "cap_ok", "cap_dn"]

# Assembly pieces and how they look. Names must match piece() in case.scad.
PIECES = [
    {"name": "plate", "colour": "#3b3f46", "roughness": 0.7},
    {"name": "tray", "colour": "#26282d", "roughness": 0.6},
    {"name": "cell", "colour": "#4f7fb5", "roughness": 0.35, "edges": False},
    {"name": "pcb", "colour": "#1f4a32", "roughness": 0.45},
    {"name": "parts", "colour": "#1e1f22", "roughness": 0.5, "edges": False},
    {"name": "metal", "colour": "#c9cdd2", "roughness": 0.25, "metal": 0.9, "edges": False},
    {"name": "white", "colour": "#efefea", "roughness": 0.5, "edges": False},
    {"name": "led", "colour": "#ffb300", "roughness": 0.3, "edges": False},
    {"name": "switch", "colour": "#2b2d31", "roughness": 0.5},
    {"name": "stem", "colour": "#8b5a2b", "roughness": 0.5},
    {"name": "lcd_frame", "colour": "#4a4d55", "roughness": 0.6},
    {"name": "lcd", "colour": "#cdd0d4", "roughness": 0.3, "edges": False},
    {"name": "lcd_active", "colour": "#aab6a2", "roughness": 0.2, "clearcoat": 1, "edges": False},
    {"name": "keybridge", "colour": "#c2185b", "roughness": 0.45},
    {"name": "caps_body", "colour": "#c2185b", "roughness": 0.45},
    {"name": "caps_first", "colour": "#ece9e2", "roughness": 0.55},
    {"name": "front_body", "colour": "#26282d", "roughness": 0.6},
    {"name": "front_first", "colour": "#ece9e2", "roughness": 0.6},
    {"name": "cover", "colour": "#e8f4ff", "roughness": 0.05, "alpha": 0.28, "clearcoat": 1, "edges": False},
]
VIEWS = {
    "hero":     {"set": "assembled", "dir": [-0.55, -1.0, 0.75], "dist": 3.0, "fov": 20},
    "hero-boot": {"set": "assembled", "dir": [-0.3, -0.5, 1.0], "dist": 2.4, "fov": 20, "screen": "screen-boot.png"},
    "front":    {"set": "assembled", "dir": [0.0, -0.18, 1.0], "dist": 3.1, "fov": 20},
    "exploded": {"set": "exploded", "dir": [-0.75, -1.0, 0.55], "dist": 2.9, "fov": 22, "gap": 4},
    "back":     {"set": "assembled", "dir": [0.35, 0.8, -1.0], "dist": 3.0, "fov": 20, "gap": 60, "under": True},
    "right":    {"set": "assembled", "dir": [1.0, -0.35, 0.3], "dist": 3.4, "fov": 20},
    # sections: keep x < cut, look from +x (through the middle key, and through USB-C / microSD)
    "section-key": {"set": "assembled", "dir": [1.0, -0.12, 0.12], "dist": 2.6, "fov": 20, "clip": [-1, 0, 0, 62.2]},
    "section-sd":  {"set": "assembled", "dir": [0.12, -1.0, 0.15], "dist": 2.4, "fov": 20, "clip": [0, 1, 0, -30.5], "shift": [30, 0, 0]},
    "left":     {"set": "assembled", "dir": [-1.0, -0.45, 0.35], "dist": 3.2, "fov": 20},
    # through the microphone port (keep y > cut, look from -y) and through the humidity chamber
    "section-mic": {"set": "assembled", "dir": [-0.25, -1.0, 0.3], "dist": 1.3, "fov": 20, "clip": [0, 1, 0, -21.68], "shift": [-40, 0, 0]},
    # cut just under the face, from above: mic and barometer ducts, humidity chamber (left end of the unit)
    "section-ducts": {"set": "assembled", "dir": [0.15, -0.35, 1.0], "dist": 1.1, "fov": 20, "clip": [0, 0, -1, 4.6], "shift": [-42, -12, 0]},
    "released": {"set": "released", "dir": [-0.45, -1.0, 0.5], "dist": 2.9, "fov": 20},
}


def scad(out, **defs):
    args = ["openscad", "-o", str(out)]
    for k, v in defs.items():
        args += ["-D", f'{k}={json.dumps(v) if isinstance(v, str) else v}']
    r = subprocess.run(args + [str(SCAD)], capture_output=True, text=True)
    log = r.stdout + r.stderr
    if r.returncode or "ERROR" in log:
        raise SystemExit(f"openscad failed for {out.name}:\n{log[-2000:]}")
    return log


def main():
    if "--extract" in sys.argv:
        subprocess.run([sys.executable, str(CASE / "tools" / "extract_board.py")], check=True)
    STL.mkdir(exist_ok=True)
    jobs = [(STL / f"{p}.stl", {"part": p}) for p in PRINT_PARTS]
    render = "--no-render" not in sys.argv
    if render:
        # assembled, exploded, and "released": the unit slid half off its plate
        for set_, e in (("assembled", 0), ("exploded", 1)):
            (SCENE / set_).mkdir(parents=True, exist_ok=True)
            jobs += [(SCENE / set_ / f"{p['name']}.stl", {"part": "piece", "piece_name": p["name"], "explode": e}) for p in PIECES]
        (SCENE / "released").mkdir(parents=True, exist_ok=True)
        jobs += [(SCENE / "released" / f"{p['name']}.stl", {"part": "piece", "piece_name": p["name"], "explode": 0, "release": 1}) for p in PIECES]
    with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
        logs = list(ex.map(lambda j: scad(j[0], **j[1]), jobs))
    for line in logs[0].splitlines():
        if "ECHO" in line:
            print(line.replace('ECHO: "', "").rstrip('"'))
    subprocess.run([sys.executable, str(CASE / "tools" / "mass.py"), str(STL)], check=True)
    if render:
        (RENDER / "scene.json").write_text(json.dumps({"pieces": [{"alpha": 1, **p} for p in PIECES], "views": VIEWS}, indent=1))
        env = dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip())
        subprocess.run(["node", str(RENDER / "shoot.js"), str(CASE / "renders")], check=True, env=env)


if __name__ == "__main__":
    main()
