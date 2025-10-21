cat > UTILS/build_manifest_v2.py << 'PY'
import json, os, hashlib, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(".")
CATEGORIES = ("CARDS", "COLLECTION", "RULES")

def sha1_of_file(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def norm_slug(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def infer_from_path(rel: str):
    parts = rel.split("/")
    out = {}
    if parts[0] == "CARDS":
        out["kind"] = "CARD"
        if len(parts) >= 5:
            out["lang"] = parts[1]
            out["set"] = parts[2]
            out["faction"] = parts[3]
        fn = parts[-1].rsplit(".", 1)[0]
        out["reference"] = fn
        m = re.search(r"_([CRU])(?:\d+)?$", fn)
        if m:
            out["rarity"] = m.group(1)
    elif parts[0] == "COLLECTION":
        out["kind"] = "COLLECTION"
    elif parts[0] == "RULES":
        out["kind"] = "RULES"
    else:
        out["kind"] = "OTHER"
    return out

def safe_load_json(p: Path):
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def extract_card_fields(data: dict):
    name = data.get("name") or data.get("cardName") or data.get("title")
    rarity = data.get("rarity") or data.get("rar")
    ctype = data.get("type") or data.get("cardType")
    ref   = data.get("reference") or data.get("ref") or data.get("id")
    faction = data.get("faction") or data.get("affinity")
    lang = data.get("lang") or data.get("language") or data.get("locale")
    set_ = data.get("set") or data.get("setCode") or data.get("expansion")
    unique = bool(data.get("unique", False))
    keywords = data.get("keywords") or data.get("keyword") or []
    if isinstance(keywords, str): keywords = [keywords]
    hand_cost = data.get("hand_cost") or data.get("cost") or data.get("handCost")
    power = data.get("power") or data.get("attack") or data.get("atk")
    life = data.get("life") or data.get("health") or data.get("hp")
    return {
        "name": name, "rarity": rarity, "type": ctype, "reference": ref,
        "faction": faction, "lang": lang, "set": set_, "unique": unique,
        "keywords": keywords, "hand_cost": hand_cost, "power": power, "life": life
    }

def build_manifest_v2(root: Path) -> dict:
    entries = {}
    idx_name = {}
    idx_ref = {}
    idx_kw = {}
    idx_set = {}
    idx_faction = {}
    idx_rarity = {}
    counts = {"ALL": 0, "CARDS": 0, "COLLECTION": 0, "RULES": 0, "OTHER": 0}

    for base in CATEGORIES:
        base_dir = root / base
        if not base_dir.exists():
            continue
        for p in base_dir.rglob("*.json"):
            rel = p.relative_to(root).as_posix()
            meta = infer_from_path(rel)
            stat = p.stat()
            meta.update({
                "path": rel,
                "size": stat.st_size,
                "sha1": sha1_of_file(p),
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            })

            data = safe_load_json(p)
            if data and meta.get("kind") == "CARD":
                card = extract_card_fields(data)
                for k, v in card.items():
                    if v is not None:
                        meta[k] = v
                if meta.get("name"):
                    meta["name_slug"] = norm_slug(meta["name"])

                # Indizes
                if meta.get("name_slug"):
                    idx_name.setdefault(meta["name_slug"], []).append(rel)
                if meta.get("reference"):
                    idx_ref[meta["reference"]] = rel
                for kw in (meta.get("keywords") or []):
                    if kw:
                        idx_kw.setdefault(norm_slug(str(kw)), []).append(rel)
                if meta.get("set"):
                    idx_set.setdefault(str(meta["set"]), []).append(rel)
                if meta.get("faction"):
                    idx_faction.setdefault(str(meta["faction"]), []).append(rel)
                if meta.get("rarity"):
                    idx_rarity.setdefault(str(meta["rarity"]), []).append(rel)

            entries[rel] = meta
            counts["ALL"] += 1
            counts[meta["kind"]] = counts.get(meta["kind"], 0) + 1

    return {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "entries": entries,
        "_index": {
            "by_name": idx_name,
            "by_reference": idx_ref,
            "by_keyword": idx_kw,
            "by_set": idx_set,
            "by_faction": idx_faction,
            "by_rarity": idx_rarity
        }
    }

if __name__ == "__main__":
    m = build_manifest_v2(ROOT)
    with open("manifest.v2.json", "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
    print("✅ manifest.v2.json geschrieben")
    print("📊 Counts:", m["counts"])
    print("🔎 Beispiel 'Daring Porter':", m["_index"]["by_name"].get("daring-porter"))
PY
