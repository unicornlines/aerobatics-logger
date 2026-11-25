"""Load symbols from KiCad libraries (system or project) and flatten 'extends'."""
import copy, os
from sexpr import parse, find, first, Sym

SYS = "/usr/share/kicad/symbols"
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_LIB = os.path.join(HERE, "..", "kicad", "logger.kicad_sym")
_cache = {}

def _lib(nick):
    if nick not in _cache:
        path = PROJECT_LIB if nick == "logger" else os.path.join(SYS, nick + ".kicad_sym")
        with open(path) as f:
            _cache[nick] = parse(f.read())[0]
    return _cache[nick]

def _raw(nick, name):
    for s in find(_lib(nick), "symbol"):
        if s[1] == name:
            return copy.deepcopy(s)
    raise KeyError(f"{nick}:{name}")

def symbol(lib_id):
    nick, name = lib_id.split(":")
    s = _raw(nick, name)
    ext = first(s, "extends")
    if ext:
        parent = symbol(f"{nick}:{ext[1]}")
        pname = parent[1].split(":")[1]
        body = [e for e in parent[2:] if not (isinstance(e, list) and e[0] == "property")]
        for e in body:
            if isinstance(e, list) and e[0] == "symbol":
                e[1] = name + e[1][len(pname):]
        props = find(s, "property")
        pprops = {p[1]: p for p in find(parent, "property")}
        for p in props:
            pprops[p[1]] = p
        flags = [e for e in parent[2:] if isinstance(e, list) and e[0] in ("pin_names", "pin_numbers", "in_bom", "on_board", "power", "exclude_from_sim")]
        rest = [e for e in body if not (isinstance(e, list) and e[0] in ("pin_names", "pin_numbers", "in_bom", "on_board", "power", "exclude_from_sim"))]
        s = [Sym("symbol"), name] + flags + list(pprops.values()) + rest
    s[1] = lib_id
    return s

def pins(sym, unit=1):
    """Return {number: (x, y, angle, name, type)} for the given unit (lib coords, Y up)."""
    out = {}
    base = sym[1].split(":")[1]
    for sub in find(sym, "symbol"):
        suffix = sub[1][len(base) + 1:]
        u = int(suffix.split("_")[0])
        if u not in (0, unit):
            continue
        for p in find(sub, "pin"):
            at = first(p, "at")
            name = first(p, "name")[1]
            num = first(p, "number")[1]
            out.setdefault(num, []).append((float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0, name, str(p[1])))
    return out
