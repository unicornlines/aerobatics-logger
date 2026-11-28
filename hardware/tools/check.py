"""Connectivity checks on the KiCad netlist (stand-in for ERC, which KiCad 7's CLI lacks).

    kicad-cli sch export netlist ../kicad/logger.kicad_sch -o /tmp/logger.net
    python3 check.py /tmp/logger.net
"""
import sys
from collections import defaultdict
from sexpr import parse, find, first
import design

tree = parse(open(sys.argv[1]).read())[0]
nets = first(tree, "nets")
errors, warnings = [], []
# PWR_FLAG symbols are virtual (#FLG) and left out of the netlist, so take them from design.py
flagged = {p["nets"]["1"] for sh in design.SHEETS for p in sh["parts"] if p["lib"] == "power:PWR_FLAG"}
got = {}
for n in find(nets, "net"):
    name = first(n, "name")[1].lstrip("/")
    nodes = [(first(x, "ref")[1], first(x, "pin")[1], (first(x, "pintype") or [None, ""])[1]) for x in find(n, "node")]
    got[name] = nodes
    types = [t for _, _, t in nodes]
    if name.startswith("unconnected-"):
        continue
    if len(nodes) < 2 and not any(r.startswith("TP") for r, _, _ in nodes):
        warnings.append(f"net {name}: only one pin {nodes}")
    if any(t.startswith("power_in") for t in types) and not any(t.startswith("power_out") for t in types) and name not in flagged:
        errors.append(f"net {name}: power input pins but nothing drives it")
    if sum(t.startswith("output") for t in types) > 1:
        errors.append(f"net {name}: several outputs {nodes}")
# every design connection must appear in the netlist
for sh in design.SHEETS:
    for p in sh["parts"]:
        for pin, net in p["nets"].items():
            if net == "NC" or p["ref"].startswith("#"):
                continue
            if not any((p["ref"], pin) == (r, q) for r, q, _ in got.get(net, [])):
                errors.append(f"{p['ref']}.{pin} not on net {net}")
print(f"{len(got)} nets, {len(errors)} errors, {len(warnings)} warnings")
for e in errors: print("ERROR", e)
for w in warnings: print("WARN ", w)
sys.exit(1 if errors else 0)
