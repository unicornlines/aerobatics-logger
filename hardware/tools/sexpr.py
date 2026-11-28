"""Minimal S-expression reader/writer for KiCad files."""
import re

class Sym(str):
    """Unquoted atom."""

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)

def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"bad token at {pos}")
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            lst = stack.pop()
            stack[-1].append(lst)
        elif m.group(3) is not None:
            stack[-1].append(m.group(3).replace('\\"', '"').replace('\\\\', '\\'))
        else:
            stack[-1].append(Sym(m.group(4)))
    return stack[0]

def dump(x, indent=0):
    if isinstance(x, list):
        if not x:
            return "()"
        simple = all(not isinstance(e, list) for e in x)
        if simple:
            return "(" + " ".join(dump(e) for e in x) + ")"
        out = "(" + dump(x[0])
        for e in x[1:]:
            if isinstance(e, list):
                out += "\n" + "  " * (indent + 1) + dump(e, indent + 1)
            else:
                out += " " + dump(e)
        return out + ")"
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, (int, float)):
        return fmt(x)
    return '"' + str(x).replace("\\", "\\\\").replace('"', '\\"') + '"'

def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def find(lst, key):
    return [e for e in lst if isinstance(e, list) and e and e[0] == key]

def first(lst, key):
    r = find(lst, key)
    return r[0] if r else None
