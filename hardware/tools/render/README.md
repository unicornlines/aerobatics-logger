# Board renders

Studio renders of the board for review. Run from this folder, with KiCad 7, `cadquery-ocp`,
`cairosvg`, Pillow, Node and Playwright's Chromium installed:

```sh
mkdir -p out
kicad-cli pcb export step --subst-models -f -o out/board.step ../../kicad/logger.kicad_pcb
python3 step2glb.py out/board.step out/board.glb          # parts with their KiCad colours
python3 textures.py ../../kicad/logger.kicad_pcb out      # top/bottom textures from the plotted layers
python3 scene.py ../../kicad/logger.kicad_pcb out/scene.json
npm install && cp render.html out/ && ln -sf ../node_modules out/node_modules
node shoot.js out ../../renders                           # board-hero.png, board-top.png, board-bottom.png
```

The board body is drawn by `render.html` itself (matte black mask, ENIG pads, white silk), so the
copper and silkscreen in the renders are the real ones. Parts without a KiCad 3D model get a plain
box from `scene.py`. KiCad has to find its STEP models for `--subst-models`; if the 3D model
variables don't resolve, point the footprints' model paths at the STEP files directly.

KiCad 7's `--subst-models` only swaps in a STEP file when the `.wrl` named in the footprint exists too, and the
board's model paths mix `KICAD6_3DMODEL_DIR`, `KICAD7_3DMODEL_DIR` and `KISYS3DMOD`. The reliable way is a scratch
copy of the board with every model path made absolute and pointed at the `.step` file. Also drop the models of
parts that `scene.py` draws as stand-ins: KiCad 7 ships models for a few of them (U15, U16, F1, F2), which would
otherwise sit on top of the boxes. KiCad 7 has no model for the microSD socket (Hirose DM3AT) or the edge SMA (J50),
so those come from the current kicad-packages3D. The SMA's model is kept in `kicad/3d/` and set by `pcb.py`
(`MODELS`), turned 90° to match KiCad 7's footprint; without that turn the jack renders lying along the left edge.
