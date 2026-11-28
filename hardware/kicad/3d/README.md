# 3D models

`SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount.step`: from the KiCad library
([kicad-packages3D](https://gitlab.com/kicad/libraries/kicad-packages3D), `Connector_Coaxial.3dshapes`),
CC-BY-SA 4.0 with the KiCad libraries exception. KiCad 7 ships no model for J50. This one runs along its own +x,
so `tools/pcb.py` places it turned +90° about z to match KiCad 7's footprint, whose jack runs along +y.
