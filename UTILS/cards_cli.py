cat > UTILS/cards_cli.py << 'PY'
import json, argparse, sys
from pathlib import Path

MFILE = Path("manifest.v2.json")

def load_manifest():
    if not MFILE.exists():
        print("❌ manifest.v2.json nicht gefunden. Bitte erst ausführen: python UTILS/build_manifest_v2.py")
        sys.exit(1)
    with MFILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def slugify(s: str) -> str:
    import re, unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def summarize(entry: dict):
    fields = ["name","reference","set","faction","rarity","type","lang","unique","keywords","hand_cost","power","life","path"]
    return {k: entry.get(k) for k in fields}

def cmd_stats(M):
    print("📊 Counts:", M["counts"])

def cmd_name(M, name: str):
    slug = slugify(name)
    paths = M["_index"]["by_name"].get(slug, [])
    if not paths:
        print(f"❌ Keine Karte gefunden für Name: {name!r}")
        return
    for p in paths:
        e = M["entries"][p]
        print(summarize(e))

def cmd_ref(M, ref: str):
    p = M["_index"]["by_reference"].get(ref)
    if not p:
        print(f"❌ Keine Karte gefunden für Reference: {ref!r}")
        return
    print(summarize(M["entries"][p]))

def main():
    ap = argparse.ArgumentParser(description="Altered TCG CLI (Manifest v2)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stats", action="store_true", help="Zeigt Zähler je Kategorie")
    g.add_argument("--name", type=str, help="Suche Karte nach Name")
    g.add_argument("--ref", type=str, help="Suche Karte nach Reference-ID")
    args = ap.parse_args()

    M = load_manifest()
    if args.stats:
        cmd_stats(M)
    elif args.name:
        cmd_name(M, args.name)
    elif args.ref:
        cmd_ref(M, args.ref)

if __name__ == "__main__":
    main()
PY
