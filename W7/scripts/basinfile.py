"""Read a HEC-HMS .basin text file: elements, attributes, topology."""
import re
BLOCK = re.compile(r'^(Subbasin|Junction|Reach|Reservoir|Sink|Diversion|Source): (.+?)\r?\n(.*?)^End:', re.S | re.M)

def parse(path):
    """-> {name: {'type': str, 'attrs': {key: value (first occurrence)}}} in file order."""
    txt = open(path, encoding="utf-8").read(); els = {}
    for typ, name, body in BLOCK.findall(txt):
        attrs = {}
        for line in body.splitlines():
            m = re.match(r'^\s*([^:]+?): (.*)$', line)
            if m and m.group(1).strip() not in attrs: attrs[m.group(1).strip()] = m.group(2).strip()
        els[name.strip()] = {"type": typ, "attrs": attrs}
    return els

def downstream(els):
    return {n: e["attrs"].get("Downstream") for n, e in els.items()}

def upstream_of(els, target):
    """Names of all elements whose downstream chain passes through `target` (target itself excluded)."""
    ds = downstream(els); out = set()
    for n in els:
        cur, seen = ds.get(n), set()
        while cur and cur not in seen:
            if cur == target: out.add(n); break
            seen.add(cur); cur = ds.get(cur)
    return out

def xy(e):
    return float(e["attrs"]["Canvas X"]), float(e["attrs"]["Canvas Y"])

def num(e, key, default=None):
    v = e["attrs"].get(key)
    try: return float(v)
    except (TypeError, ValueError): return default
