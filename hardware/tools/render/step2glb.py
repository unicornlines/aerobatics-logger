"""Tessellate a KiCad STEP export and write it as GLB with its colours (OCCT's glTF writer)."""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString as InfoMap
from OCP.Message import Message_ProgressRange
from OCP.IFSelect import IFSelect_RetDone

src, out = sys.argv[1], sys.argv[2]
doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
r = STEPCAFControl_Reader(); r.SetColorMode(True); r.SetNameMode(True)
assert r.ReadFile(src) == IFSelect_RetDone
assert r.Transfer(doc)
shape = r.Reader().OneShape()
BRepMesh_IncrementalMesh(shape, 0.02, False, 0.35, True)
w = RWGltf_CafWriter(TCollection_AsciiString(out), True)
ok = w.Perform(doc, InfoMap(), Message_ProgressRange())
print("ok", ok)
