"""Make top/bottom board textures (matte black mask, ENIG pads, white silk) from KiCad layer SVGs."""
import subprocess, sys, io
import cairosvg
from PIL import Image, ImageChops, ImageOps

pcb, outdir = sys.argv[1], sys.argv[2]
PX_PER_MM = 24
W_MM, H_MM = 88.0, 62.0
size = (int(W_MM * PX_PER_MM), int(H_MM * PX_PER_MM))

RAW_W = 3200   # plot wider than needed, then crop to the board edge: "board area" also counts parts hanging over the edge
_crop = None

def plot(layers):
    svg = f"{outdir}/{layers.split(',')[0]}.svg"
    subprocess.run(["kicad-cli", "pcb", "export", "svg", pcb, "-o", svg, "--layers", layers,
                    "--page-size-mode", "2", "--exclude-drawing-sheet", "--black-and-white"], check=True, capture_output=True)
    png = cairosvg.svg2png(url=svg, output_width=RAW_W, background_color="white")
    return ImageOps.invert(Image.open(io.BytesIO(png)).convert("L"))   # white = drawn

def layer(name):
    global _crop
    if _crop is None:
        _crop = plot("Edge.Cuts").point(lambda v: 255 if v > 64 else 0).getbbox()
    return plot(f"{name},Edge.Cuts").crop(_crop).resize(size, Image.LANCZOS)

def compose(side):
    cu, mask, silk = layer(f"{side}.Cu"), layer(f"{side}.Mask"), layer(f"{side}.SilkS")
    edge = layer("Edge.Cuts")
    cu = ImageChops.subtract(cu, edge); mask = ImageChops.subtract(mask, edge); silk = ImageChops.subtract(silk, edge)
    base = Image.new("RGB", size, (24, 26, 28))           # matte black mask over FR4
    copper_under = Image.new("RGB", size, (40, 43, 46))   # copper shows faintly through the mask
    gold = Image.new("RGB", size, (214, 178, 92))          # ENIG
    white = Image.new("RGB", size, (236, 236, 232))
    img = Image.composite(copper_under, base, cu)
    img = Image.composite(gold, img, ImageChops.multiply(mask, cu))
    img = Image.composite(white, img, ImageChops.subtract(silk, mask))
    if side == "B":
        img = ImageOps.mirror(img)
    img.save(f"{outdir}/{side.lower()}_texture.png")

compose("F"); compose("B")
print("textures", size)
