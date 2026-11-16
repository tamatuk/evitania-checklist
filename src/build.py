"""Builds ../index.html from the data folder, template.html and the icons folder.

Run: python3 src/build.py   (needs Pillow)
"""
import sys, json, io, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

def fail(msg):
    """Stop the build, naming the file and the broken reference or count."""
    sys.exit("build failed: " + msg)

def load(name):
    """The parsed JSON of data/<name>; a missing file or invalid JSON fails naming it."""
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        fail("data/%s: %s" % (name, e))

def cite(keys, where):
    """The source names of sources.json keys, joined with "; "; an unknown key fails naming `where`."""
    if not isinstance(keys, list):
        fail("%s: source %r is not a list of sources.json keys" % (where, keys))
    for k in keys:
        if k not in SRC:
            fail("%s: source key %r is not in sources.json" % (where, k))
    return "; ".join(SRC[k]["name"] for k in keys)

def load_systems(order):
    """(file name, system) pairs of data/systems/*.json in `order` (expect's keys), each matched by its "name"; a file
    with no expect key, an expect key with no file, or a table row with more or fewer cells than its cols fails."""
    by = {}
    for fn in sorted(os.listdir(os.path.join(DATA, "systems"))):
        if not fn.endswith(".json"): continue
        f_ = "systems/" + fn
        s_ = load(f_)
        if s_["name"] in by: fail("%s: system %r is also in %s" % (f_, s_["name"], by[s_["name"]][0]))
        if s_["name"] not in order: fail("%s: system %r has no expect key in stages.json" % (f_, s_["name"]))
        for t in s_["tables"]:
            for j, row in enumerate(t["rows"]):
                if len(row) != len(t["cols"]):
                    fail("%s: table %r row %d has %d cells for %d cols"
                         % (f_, t["title"], j + 1, len(row), len(t["cols"])))
        by[s_["name"]] = (f_, s_)
    for n_ in order:
        if n_ not in by: fail("stages.json: expect key %r has no file in data/systems" % n_)
    return [by[n_] for n_ in order]

def check_expect(expect, stages):
    """Each expect row has one number per stage; fails naming the system."""
    for n_, row in expect.items():
        if len(row) != len(stages) or not all(isinstance(x, int) for x in row):
            fail("stages.json: expect %r needs %d numbers, one per stage, has %r" % (n_, len(stages), row))

SRC = load("sources.json")
ST = load("stages.json")
check_expect(ST["expect"], ST["stages"])
SYS = load_systems(list(ST["expect"]))
DAILY = load("daily.json")
ROSTER = load("roster.json")

systems = []
for f_, s_ in SYS:
    systems.append({"name": s_["name"],
        "tiers": [{"req": t["req"], "basis": t["basis"], "source": cite(t["source"], f_)} for t in s_["tiers"]],
        "tables": [{"title": t["title"], "cols": t["cols"],
                    "rows": [[cite(x, f_) if c == "Source" else x for c, x in zip(t["cols"], row)]
                             for row in t["rows"]]}
                   for t in s_["tables"]]})

def check_daily(daily):
    """Every daily row has a unique "id"; fails naming the repeated id, or the task of a row without one."""
    raise NotImplementedError

def check_share(share, systems, daily):
    """share.json's lists hold exactly the systems' names and the daily ids; fails naming what is missing or extra."""
    raise NotImplementedError

ABOUT = load("about.json")
SHARE = load("share.json")
check_daily(DAILY)
check_share(SHARE, [s_["name"] for _, s_ in SYS], [r["id"] for r in DAILY])
data = {"roster": [[r["topic"], r["rule"], r["basis"], cite(r["source"], "roster.json")] for r in ROSTER],
        "systems": systems, "stages": ST["stages"], "reached": ST["reached"], "expect": ST["expect"],
        "daily": [[r["when"], r["task"], r["why"], cite(r["source"], "daily.json"), r["id"]] for r in DAILY],
        "shareSys": SHARE["systems"], "shareDaily": SHARE["daily"], "about": [[r["topic"], r["text"]] for r in ABOUT], "sources": [{k: s_[k] for k in ("name", "where", "link", "asof")} for s_ in SRC.values()]}


import os, base64, re
from PIL import Image
R = os.path.join(HERE, "icons") + os.sep
SMALL = {"for", "of", "the", "to", "per", "in"}
def title(fn):
    w = fn.split("_")
    return " ".join(x if (i and x in SMALL) else (x.upper() if x in ("ii","d20") else x.capitalize()) for i, x in enumerate(w))
TOP = False
def files(d):
    out = []
    for root, _, fs in sorted(os.walk(R + d)):
        if TOP and root != R + d: continue
        for f in sorted(fs):
            if f.endswith(".png") and "atlas" not in f and not f.endswith("_thumb.png"):
                out.append((f[:-4], os.path.join(root, f)))
    return out
ICONS = load("icons.json")
GENERIC = {"durability", "exp", "heart", "shield", "sword", "tier"}
names, paths, T, groups = [], [], {}, []
def term(k, i):
    if k not in T and k not in ICONS["stop"]: T[k] = i
for g_ in ICONS["groups"]:
    gname, d, mode = g_["name"], g_["dir"], g_["mode"]
    start = len(names); TOP = (mode == 'top')
    for fn, p in files(d):
        if fn in GENERIC or fn == "runeword": continue
        nm = fn if mode == "raw" else (ICONS["rename"].get(fn) or (fn.upper() if mode == "rune" else title(fn)))
        i = len(names); names.append(nm); paths.append(p)
        if mode in ("all", "rune") or (mode == "multi" and " " in nm) or mode == "curated": term(nm, i)
    if groups and groups[-1][0] == gname: groups[-1][2] = len(names)
    else: groups.append([gname, start, len(names)])
idx = {n_: i for i, n_ in reversed(list(enumerate(names)))}
for k, v in ICONS["alias"].items():
    if v in idx: T[k] = idx[v]
    else: print("alias target missing:", k, "->", v)
for s_ in data["systems"]: s_["icon"] = idx[ICONS["systemIcon"][s_["name"]]]

# ---------------------------------------------------------------- talent trees (Piwu's guides, 2026-08-06)
def load_trees(tf):
    """tf["trees"] with each node's "y" as a float, as the page prints it; node orders must run 1 to n."""
    raise NotImplementedError
TREES_FILE = load("trees.json")
trees = load_trees(TREES_FILE)
for cls, t in trees.items():
    for n_ in t["nodes"]:
        if n_["k"] == "skill": continue
        f = cls.lower() + "_" + TREES_FILE["kindFile"][n_["k"]]
        if f not in idx: f = f.replace("max_hp", "maximum_hp")
        n_["i"] = idx[f]
for cls, orders in TREES_FILE["skillOrder"].items():
    by = {n_["o"]: n_ for n_ in trees[cls]["nodes"]}
    for j, o in enumerate(orders):
        assert by[o]["k"] == "skill"
        by[o]["i"] = len(names); names.append(cls + " skill"); paths.append(os.path.join(HERE, "icons", "skills", "sk_%s_%d.png" % (cls.lower(), j)))
data["trees"] = trees
CELL, COLS = 40, 24
rows = -(-len(names) // COLS)
sheet = Image.new("RGBA", (COLS * CELL, rows * CELL), (0, 0, 0, 0))
for i, p in enumerate(paths):
    im = Image.open(p).convert("RGBA")
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    im.thumbnail((CELL - 4, CELL - 4), Image.LANCZOS)
    sheet.paste(im, ((i % COLS) * CELL + (CELL - im.width) // 2, (i // COLS) * CELL + (CELL - im.height) // 2), im)
buf = io.BytesIO(); sheet.save(buf, "WEBP", quality=82, method=6)
spr = base64.b64encode(buf.getvalue()).decode()
print("icons", len(names), "sprite kB", len(spr) // 1024, "groups", groups)
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
out = (tpl.replace("/*DATA*/", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
          .replace("/*SPRITE*/", spr).replace("/*ICONNAMES*/", json.dumps(names)).replace("/*TERMS*/", json.dumps(T, ensure_ascii=False)).replace("/*GROUPS*/", json.dumps(groups)).replace("/*COLS*/", str(COLS)))
cut = out.index("</style>") + len("</style>")
open(os.path.join(HERE, "..", "index.html"), "w", encoding="utf-8").write('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<style>html{color-scheme:dark}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n' + out[:cut] + '\n</head>\n<body>\n' + out[cut:] + '\n</body>\n</html>\n')
print(len(out), len(T), "terms")
