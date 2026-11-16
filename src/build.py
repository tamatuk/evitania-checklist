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
                    fail("%s: table %r row %d has %d cells for %d cols" % (f_, t["title"], j + 1, len(row), len(t["cols"])))
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
                    "rows": [[cite(x, f_) if c == "Source" else x for c, x in zip(t["cols"], row)] for row in t["rows"]]}
                   for t in s_["tables"]]})

about = [
 ["What it is", "A rule checklist for Evitania Online, filled in by hand. Your stage sets which tier of each system is expected, and each system lists its tiers."],
 ["How to use", "Pick your stage at the top. Set your tier for each system with the plus and minus buttons, or open a system and click the highest tier you have reached."],
 ["Basis: Guide", "The requirement is a target or recommendation stated in the source."],
 ["Basis: Game data", "The requirement is a game threshold, cost or unlock reported by the source."],
 ["Basis: Estimate", "Ordered or set from several sources; no single guide states it as a target. Treat it as a draft."],
 ["Stage expectations", "The expected tier at each stage is a synthesis of the guides, not a community standard."],
 ["No save import", "Since game version 0.311.0 the save file is encrypted and the developers ask players not to share ways to decode it, so tiers are set by hand."],
 ["Freshness", "Built 2026-11-15 from sources dated April to November 2026, around game version 0.323.1. Numbers marked Game data were re-checked on 2026-11-14 against the wiki data files and the developer patch notes. All sources are unofficial; check values in-game after patches."],
 ["Not covered", "Guild research, the Tower, fishing (event mini-game so far) and the Hourglass Restoration of Eternity tabs have no tiers here: the guides for them are thin or not written yet. Trinkets have a first draft."],
]
DAILY_IDS = ["quest", "login", "boss-keys", "vendor-1", "vendor-2", "vendor-3", "tower", "mail-codes", "cost-cruncher", "bonfire-fuel", "slyme-egg", "fate-spiral", "curio-coins", "event-dungeons", "guild-donations"]
assert len(DAILY_IDS) == len(DAILY) == len(set(DAILY_IDS))
# append-only: positions are part of the share-link format
SHARE_SYS = ["Hunter", "Bonfire", "Ash", "Sacrifice", "Pusher gear", "Gatherer gear", "Gathering", "Gems", "Pets", "Cards", "Runes", "Engineer", "Curio", "Hourglass", "Characters", "Trinkets"]
SHARE_DAILY = ["quest", "login", "boss-keys", "vendor-1", "vendor-2", "vendor-3", "tower", "mail-codes", "cost-cruncher", "bonfire-fuel", "slyme-egg", "fate-spiral", "curio-coins", "event-dungeons", "guild-donations"]
assert set(SHARE_SYS) == {s_["name"] for _, s_ in SYS} and set(SHARE_DAILY) == set(DAILY_IDS)
data = {"roster": [[r["topic"], r["rule"], r["basis"], cite(r["source"], "roster.json")] for r in ROSTER],
        "systems": systems, "stages": ST["stages"], "reached": ST["reached"], "expect": ST["expect"],
        "daily": [[r["when"], r["task"], r["why"], cite(r["source"], "daily.json"), i] for r, i in zip(DAILY, DAILY_IDS)],
        "shareSys": SHARE_SYS, "shareDaily": SHARE_DAILY, "about": about, "sources": [{k: s_[k] for k in ("name", "where", "link", "asof")} for s_ in SRC.values()]}


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
REN = {"attack_speed_training": "Speed Training (attack)", "movement_speed_training": "Speed Training (movement)",
       "chance_to_get_1_ash_per_kill": "Hot Stuff", "stoney_mcstoneface": "Stoney McStoneface", "zhai_haluds_gate": "Zhai Halud's Gate",
       "the_crabs_pickaxe": "The Crab's Pickaxe", "maevaths_horn": "Maevath's Horn", "deaths_flower": "Death's Flower",
       "necromancers_hand": "Necromancer's Hand", "servants_idol": "Servant's Idol", "worms_horn": "Worm's Horn",
       "act1_hard": "Act 1 Hard card", "act2_hard": "Act 2 Hard card", "act1_nightmare": "Act 1 Nightmare card", "act2_nightmare": "Act 2 Nightmare card",
       "crab": "Crab Miner", "watches": "Watch", "ciphered_billding": "Ciphered Billding", "fifth_stab": "Fifth Slab", "entombed_mask": "Entombed Mask"}
GENERIC = {"durability", "exp", "heart", "shield", "sword", "tier"}
groups_def = [
 ("Hunter trainings", "bonuses/images/hunter_upgrades", "all", None),
 ("Sacrifices", "bonuses/images/bonfire_sacrifice", "all", None),
 ("Ash tree", "bonuses/images/bonfire_ash", "all", None),
 ("Heat bonuses", "bonuses/images/bonfire_bonuses", "all", None),
 ("Engineer", "items/images/engineer", "all", None),
 ("Engineer upgrades", "bonuses/images/engineer_upgrades", "multi", None),
 ("Gem shop", "bonuses/images/gem_shop", "multi", None),
 ("Monsters, bosses and nodes", "cards/images", "curated", None),
 ("Runes", "items/images/runes", "rune", None),
 ("Curios", "items/images/curio", "multi", None),
 ("Smeltery and usables", "items/images/smeltery", "all", None),
 ("Smeltery and usables", "items/images/usables", "multi", None),
 ("Materials", "items/images/materials", "all", None),
 ("Gear", "items/images/gear", "multi", None),
 ("Pets", "items/images/pets", "multi", None),
 ("Currencies", "items/images", "top", None),
 ("Talents", "bonuses/images/progression", "raw", None),
]
STOP = {"Gold", "Leaf", "Ash", "Glass", "Gem", "Ghost", "Coal", "Goak", "Cactus", "Cryolite", "Idea"}
names, paths, T, groups = [], [], {}, []
def term(k, i):
    if k not in T and k not in STOP: T[k] = i
for gname, d, mode, _ in groups_def:
    start = len(names); TOP = (mode == 'top')
    for fn, p in files(d):
        if fn in GENERIC or fn == "runeword": continue
        nm = fn if mode == "raw" else (REN.get(fn) or (fn.upper() if mode == "rune" else title(fn)))
        i = len(names); names.append(nm); paths.append(p)
        if mode in ("all", "rune") or (mode == "multi" and " " in nm) or mode == "curated": term(nm, i)
    if groups and groups[-1][0] == gname: groups[-1][2] = len(names)
    else: groups.append([gname, start, len(names)])
idx = {n_: i for i, n_ in reversed(list(enumerate(names)))}
alias = {"Damage Abuse": "Damage Abuse Training", "More Damage": "More Damage Training", "Dice": "Dice Training",
 "Boars": "Boar", "Pebbles": "Pebble", "Stumps": "Stump", "Plants": "Plant", "Wolves": "Wolf", "Crabs": "Crab Miner", "crab miners": "Crab Miner",
 "Weird Books": "Weird Book", "Slime Cubes": "Slime Cube", "Fire Elementals": "Fire Elemental", "Watches": "Watch", "Snowmen": "Snowman",
 "Helmets": "Helmet", "Mammoth": "Ice Mammoth", "Jötunn": "Jotunn", "Red Dragon": "Yrsainir", "Wish for Wisdom": "Wish for Wizdom",
 "Owl Wisdom": "Owl Wizdom", "Fiery Weapons": "Fiery Weapon", "Double Crits": "Double Crit", "Slymes": "Slyme", "Ironwood": "Ironwood Log",
 "Thorium": "Thorium Ore", "Mini Plant": "Mini Plants", "Icy Needle": "Icy Needles", "Humble Sacrifice": "Humble Sacrifices",
 "Golden Piggy": "Golden Piggy", "Leaf Spirit": "Leaf Spirit", "Basic Bat": "Basic Bat", "Slyme": "Slyme", "Chadcoal": "Chadcoal",
 "Palm Face": "Palm Face", "Enhance stones": "Enhance Stone 1", "Smelter Patterns": "Smelting Patterns", "Jotunn's Eye": "Jotunn Eye",
 "Fate Spiral": "Daily Fate Spiral", "Premium Runes": "Premium Rune", "Engineer Slot Upgrades": "Engineer Slot Upgrade", "Cost Cruncher": "Hunter Cost Cruncher"}
for k, v in alias.items():
    if v in idx: T[k] = idx[v]
    else: print("alias target missing:", k, "->", v)
SYSICON = {"Hunter": "Power Training", "Bonfire": "Fiery Weapon", "Ash": "Ash", "Sacrifice": "Attack Wish", "Pusher gear": "Thorium Sword", "Gatherer gear": "Thorium Pickaxe",
 "Gathering": "Ironwood Log", "Gems": "Gem", "Pets": "Basic Bat", "Cards": "Act 1 Hard card", "Runes": "PRE", "Engineer": "Blueprint",
 "Curio": "Curio Coin", "Hourglass": "8 Hour Hourglass", "Characters": "Straw Hat", "Trinkets": "Anomalous Ring"}
for s_ in data["systems"]: s_["icon"] = idx[SYSICON[s_["name"]]]

# ---------------------------------------------------------------- talent trees (Piwu's guides, 2026-08-06)
def tree(nodes, edges, names=None):
    out = []
    for ln in nodes.strip().split(";"):
        o, c, y, k, m = [x.strip() for x in ln.split(",")]
        out.append({"o": int(o), "c": int(c), "y": float(y), "k": k, "m": int(m)})
    for n_ in out:
        if names and n_["o"] in names: n_["n"] = names[n_["o"]]
    ed = [[int(a), int(b)] for a, b in (e.split("-") for e in edges.split())]
    assert sorted(n_["o"] for n_ in out) == list(range(1, len(out) + 1))
    return {"nodes": out, "edges": ed}
TREES = {
 "Warrior": tree("""1,0,1.5,skill,1; 7,1,0,xp,3; 5,1,1,def,3; 2,1,2,atk,2; 25,1,3,move,2;
 6,2,0,skill,1; 26,2,1,mf,5; 8,2,2,mregen,1; 3,2,3,mana,2;
 22,3,0,atk,3; 9,3,1,mana,3; 4,3,2,skill,1; 39,3,3,def,5;
 27,4,0,mf,5; 10,4,1,mregen,1; 32,4,2,def,5; 21,4,3,crit,5;
 11,5,.5,def,2; 31,5,1.5,aspd,5; 33,5,2.5,critd,5;
 14,6,0,atk,5; 28,6,1,mf,5; 12,6,2,hp,4; 38,6,3,def,5;
 16,7,0,skill,1; 15,7,1,crit,5; 24,7,2,move,2; 13,7,3,skill,1;
 29,8,0,critd,10; 23,8,1,xp,7; 34,8,2,hp,5; 17,8,3,mregen,3;
 35,9,0,atkp,5; 36,9,1,def,5; 30,9,2,aspd,10; 18,9,3,atkp,5;
 37,10,.5,def,10; 20,10,1.5,crit,5; 19,10,2.5,skill,1""",
 "1-7 1-5 1-2 2-25 5-6 5-26 2-8 2-3 6-22 8-9 3-4 3-39 22-27 9-10 4-32 4-21 10-11 10-31 32-33 11-14 11-28 11-12 11-38 14-15 12-15 12-13 15-16 15-24 15-29 15-23 15-34 15-17 34-35 17-36 17-30 17-18 35-37 36-37 18-20 18-19",
 {1: "Cleave", 6: "Last Stand", 4: "Improved Cleave", 16: "Blade Strike", 13: "Dragon Soul", 19: "Improved Cleave II"}),
 "Rogue": tree("""1,0,1.5,skill,1; 26,1,0,crit,2; 2,1,1,atk,2; 3,1,2,def,2; 32,1,3,aspd,3;
 8,2,.5,mana,2; 9,2,1.5,hp,2; 4,2,2.5,atk,2;
 35,3,0,mf,5; 10,3,1,def,3; 27,3,2,crit,3; 5,3,3,mregen,1;
 11,4,.5,def,2; 25,4,1.5,move,3; 6,4,2.5,skill,1;
 31,5,0,aspd,7; 12,5,1,atk,5; 33,5,2,critd,10; 7,5,3,skill,1;
 17,6,0,mregen,1; 36,6,1,atk,5; 13,6,2,mana,3; 34,6,3,mf,5;
 18,7,0,hp,5; 37,7,1,crit,5; 15,7,2,def,5; 14,7,3,skill,1;
 19,8,0,atkp,5; 20,8,1,def,5; 30,8,2,aspd,10; 16,8,3,skill,1;
 38,9,.5,mf,10; 21,9,1.5,mregen,3; 23,9,2.5,crit,10;
 28,10,0,atkp,10; 29,10,1,critd,10; 22,10,2,skill,1; 24,10,3,move,2""",
 "1-26 1-2 1-3 1-32 2-8 2-9 3-9 3-4 8-35 8-10 9-10 9-27 4-27 4-5 10-11 5-11 5-6 11-25 11-31 11-12 11-33 6-7 12-17 12-36 12-13 33-34 17-18 36-37 13-37 13-15 13-14 18-19 18-20 15-20 15-30 15-16 19-38 19-21 20-21 20-23 21-28 21-29 21-22 23-24"),
 "Mage": tree("""1,0,1.5,skill,1; 4,1,.5,mana,1; 3,1,1.5,atk,2; 2,1,2.5,xp,5;
 5,2,1,mf,5; 6,2,2,move,2;
 8,3,0,atk,5; 10,3,1,mana,2; 9,3,2,mf,5; 7,3,3,skill,1;
 27,4,0,critd,5; 11,4,1,mregen,2; 13,4,2,hp,5; 12,4,3,def,3;
 15,5,1,skill,1; 14,5,2,mana,5;
 18,6,0,xp,10; 31,6,1,aspd,10; 19,6,2,def,4; 16,6,3,skill,1;
 20,7,0,atk,5; 32,7,1,crit,5; 22,7,2,mregen,5; 17,7,3,skill,1;
 21,8,0,atkp,5; 28,8,1,mf,10; 23,8,2,mana,5; 26,8,3,critd,5;
 24,9,.5,crit,5; 29,9,1.5,def,10; 33,9,2.5,mregen,7;
 25,10,.5,skill,1; 30,10,1.5,mf,10; 34,10,2.5,atkp,5""",
 "1-4 1-3 1-2 4-5 3-5 5-6 5-8 5-10 5-9 6-7 8-27 8-11 8-13 8-12 10-13 11-14 13-14 12-14 14-15 14-18 14-31 14-19 14-16 16-17 19-20 19-32 19-22 20-21 20-28 22-28 22-23 22-26 21-24 23-24 23-29 23-33 24-25 24-30 29-30 29-34 33-34"),
}
KFILE = {"atk": "attack", "atkp": "attack_percent", "aspd": "attack_speed", "crit": "crit_chance", "critd": "crit_damage", "def": "defence",
         "mf": "magicfind", "xp": "bonus_xp", "move": "movespeed", "hp": "max_hp", "mana": "maximum_mana", "mregen": "mana_regen"}
for cls, t in TREES.items():
    for n_ in t["nodes"]:
        if n_["k"] == "skill": continue
        f = cls.lower() + "_" + KFILE[n_["k"]]
        if f not in idx: f = f.replace("max_hp", "maximum_hp")
        n_["i"] = idx[f]
SKILLO = {"Warrior": [1, 6, 4, 16, 13, 19], "Rogue": [1, 6, 7, 14, 16, 22], "Mage": [1, 7, 15, 16, 17, 25]}
for cls, orders in SKILLO.items():
    by = {n_["o"]: n_ for n_ in TREES[cls]["nodes"]}
    for j, o in enumerate(orders):
        assert by[o]["k"] == "skill"
        by[o]["i"] = len(names); names.append(cls + " skill"); paths.append(os.path.join(HERE, "icons", "skills", "sk_%s_%d.png" % (cls.lower(), j)))
data["trees"] = TREES
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
