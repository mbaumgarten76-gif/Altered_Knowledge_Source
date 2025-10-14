#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_repo.py
Prüft die Dateien im Altered-Knowledge-Repo gegen UTILS/validation_schema.json.

Nutzt nur die Python-Standardbibliothek.
- Validiert Karten-Dateien (CARDS/*/*/*/*.json)
- Validiert Collection-Dateien (COLLECTION/*.json)
- Validiert Deck-Dateien (DECKS/**/*.json)
- Validiert Rules-Dateien (RULES/*.json / *.pdf)
Gibt eine zusammengefasste Übersicht aus und beendet sich mit Exitcode 0 (OK) oder 1 (Fehler).

Aufruf:
    python UTILS/validate_repo.py                # prüft ab Repo-Wurzel
    python UTILS/validate_repo.py --root .       # expliziter Root
    python UTILS/validate_repo.py --strict       # bricht bei WARN auch als Fehler ab
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# ---------- Hilfsstrukturen ----------
@dataclass
class Finding:
    path: Path
    level: str   # 'ERROR' oder 'WARN'
    message: str

@dataclass
class Context:
    root: Path
    schema: dict
    findings: List[Finding] = field(default_factory=list)
    # Cache für Karten-Metadaten: card_id -> meta
    card_index: Dict[str, dict] = field(default_factory=dict)

    def add(self, path: Path, level: str, message: str):
        self.findings.append(Finding(path=path, level=level, message=message))

    @property
    def has_errors(self) -> bool:
        return any(f.level == "ERROR" for f in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(f.level == "WARN" for f in self.findings)


# ---------- Utilities ----------
def load_json(path: Path) -> Optional[Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"__load_error__": str(e)}

def is_json(path: Path) -> bool:
    return path.suffix.lower() == ".json"

def looks_like_card_file(path: Path) -> bool:
    # CARDS/<LANG>/<SET>/<FACTION>/<file>.json
    parts = path.parts
    try:
        i = parts.index("CARDS")
        return len(parts) >= i + 5 and path.suffix.lower() == ".json"
    except ValueError:
        return False

def looks_like_collection_file(path: Path) -> bool:
    return "COLLECTION" in path.parts and is_json(path)

def looks_like_deck_file(path: Path) -> bool:
    return "DECKS" in path.parts and is_json(path)

def looks_like_rules_file(path: Path) -> bool:
    return "RULES" in path.parts and (is_json(path) or path.suffix.lower() == ".pdf")

def norm_type(value: str) -> str:
    # Tolerant: engl./dt. Schreibweise abgleichen
    v = (value or "").strip().lower()
    mapping = {
        "hero": "hero", "held": "hero",
        "companion": "companion", "begleiter": "companion",
        "character": "character", "charakter": "character",
        "spell": "spell", "zauber": "spell",
        "permanent": "permanent", "permanent/landmark": "permanent", "landmark": "permanent",
        "token": "token", "spielstein": "token",
    }
    return mapping.get(v, v)

def rarity_flags(card_obj: dict) -> Tuple[bool, bool]:
    """(is_rare, is_unique) anhand 'rarity' oder 'unique' Feld"""
    r = (card_obj.get("rarity") or "").upper()
    is_unique = bool(card_obj.get("unique")) or r == "U"
    is_rare = r == "R"
    return is_rare, is_unique

def get_schema_rule(schema: dict, key: str, default=None):
    return schema.get("rules", {}).get(key, default or {})

# ---------- Validatoren ----------
def validate_card_file(ctx: Context, path: Path):
    rule = get_schema_rule(ctx.schema, "card_file", {})
    data = load_json(path)
    if isinstance(data, dict) and "__load_error__" in data:
        ctx.add(path, "ERROR", f"JSON load failed: {data['__load_error__']}")
        return

    # Karten-Dateien können einzelne Karte (dict) ODER arrays enthalten
    items = data if isinstance(data, list) else [data]
    id_re = re.compile(rule.get("id_pattern", r".+"))
    allowed_rarities = set(rule.get("allowed_rarities", []))

    for i, obj in enumerate(items):
        if not isinstance(obj, dict):
            ctx.add(path, "ERROR", f"[#{i}] Not a JSON object")
            continue

        # required fields
        for field_name in rule.get("required_fields", []):
            if field_name not in obj:
                ctx.add(path, "ERROR", f"[#{i}] Missing required field '{field_name}'")

        cid = obj.get("id")
        if cid:
            if not id_re.match(cid):
                ctx.add(path, "WARN", f"[#{i}] id '{cid}' does not match pattern")
            # Indexieren (nur die erste Variante gewinnt)
            ctx.card_index.setdefault(cid, obj)

        rarity = obj.get("rarity")
        if allowed_rarities and rarity and rarity.upper() not in allowed_rarities:
            ctx.add(path, "WARN", f"[#{i}] rarity '{rarity}' not in {sorted(allowed_rarities)}")

        t = norm_type(obj.get("type", ""))
        if not t:
            ctx.add(path, "WARN", f"[#{i}] empty/unknown type")

def validate_collection_file(ctx: Context, path: Path):
    rule = get_schema_rule(ctx.schema, "collection_file", {})
    data = load_json(path)
    if isinstance(data, dict) and "__load_error__" in data:
        ctx.add(path, "ERROR", f"JSON load failed: {data['__load_error__']}")
        return
    items = data if isinstance(data, list) else [data]
    min_c = rule.get("count_min", 0)
    max_c = rule.get("count_max", 99)

    for i, obj in enumerate(items):
        if not isinstance(obj, dict):
            ctx.add(path, "ERROR", f"[#{i}] Not a JSON object")
            continue

        for f in rule.get("required_fields", []):
            if f not in obj:
                ctx.add(path, "ERROR", f"[#{i}] Missing required field '{f}'")

        cnt = obj.get("count")
        if isinstance(cnt, int):
            if cnt < min_c or cnt > max_c:
                ctx.add(path, "WARN", f"[#{i}] count {cnt} out of range [{min_c}, {max_c}]")
        else:
            ctx.add(path, "ERROR", f"[#{i}] count is not an integer")

def validate_rules_file(ctx: Context, path: Path):
    rule = get_schema_rule(ctx.schema, "rules_file", {})
    if path.suffix.lower() == ".pdf":
        # Existiert = OK (optional: später PDF-Textauszug prüfen)
        return
    data = load_json(path)
    if isinstance(data, dict) and "__load_error__" in data:
        ctx.add(path, "ERROR", f"JSON load failed: {data['__load_error__']}")
        return

    # Minimalprüfung: enthaltene Schlüsselwörter?
    required_keywords = set(k.lower() for k in rule.get("required_keywords", []))
    blob = json.dumps(data).lower()
    missing = [kw for kw in required_keywords if kw not in blob]
    if missing:
        ctx.add(path, "WARN", f"Missing indicative keywords in rules JSON: {missing}")

def _load_card_meta(ctx: Context, card_id: str) -> Optional[dict]:
    if card_id in ctx.card_index:
        return ctx.card_index[card_id]
    # Optional: Lazy-Suche nach Datei durch CARDS-Baum (teurer, daher nur fallback)
    for p in ctx.root.rglob("CARDS/**/*.json"):
        if not looks_like_card_file(p):
            continue
        data = load_json(p)
        if isinstance(data, dict) and data.get("id") == card_id:
            ctx.card_index[card_id] = data
            return data
        if isinstance(data, list):
            for obj in data:
                if isinstance(obj, dict) and obj.get("id") == card_id:
                    ctx.card_index[card_id] = obj
                    return obj
    return None

def validate_deck_file(ctx: Context, path: Path):
    rule = get_schema_rule(ctx.schema, "deck_file", {})
    data = load_json(path)
    if isinstance(data, dict) and "__load_error__" in data:
        ctx.add(path, "ERROR", f"JSON load failed: {data['__load_error__']}")
        return
    if not isinstance(data, dict):
        ctx.add(path, "ERROR", "Deck file must be a JSON object")
        return

    # required fields
    for f in rule.get("required_fields", []):
        if f not in data:
            ctx.add(path, "ERROR", f"Missing required field '{f}'")

    deck_name = data.get("deck_name", "(unnamed)")
    hero_id = data.get("hero_id")
    deck_faction = (data.get("faction") or "").upper()
    cards = data.get("cards") or []

    # Basic structure check
    if not isinstance(cards, list):
        ctx.add(path, "ERROR", "cards must be a list of {card_id, qty}")
        return

    # Constraints
    cons = rule.get("constraints", {})
    min_cards = cons.get("min_cards", 40)
    max_cards = cons.get("max_cards", 60)
    unique_hero = cons.get("unique_hero", True)
    max_same = cons.get("max_same_card", 3)
    max_rare = cons.get("max_rare_cards", 15)
    max_unique = cons.get("max_unique_cards", 3)
    same_faction_as_hero = cons.get("same_faction_as_hero", True)

    # Index & counters
    total_qty = 0
    name_counts: Dict[str, int] = {}
    rare_count = 0
    unique_count = 0
    hero_seen = 0
    hero_faction = None

    # Hero check
    if not hero_id:
        ctx.add(path, "ERROR", "hero_id is missing")
    else:
        hero_meta = _load_card_meta(ctx, hero_id)
        if not hero_meta:
            ctx.add(path, "ERROR", f"hero_id '{hero_id}' not found in CARDS")
        else:
            t = norm_type(hero_meta.get("type", ""))
            if t != "hero":
                ctx.add(path, "ERROR", f"hero_id '{hero_id}' is not a Hero (type='{hero_meta.get('type')}')")
            hero_faction = (hero_meta.get("faction") or "").upper()
            if deck_faction and hero_faction and deck_faction != hero_faction:
                ctx.add(path, "ERROR", f"Deck faction '{deck_faction}' != hero faction '{hero_faction}'")

    # Iterate cards
    for i, entry in enumerate(cards):
        if not isinstance(entry, dict):
            ctx.add(path, "ERROR", f"[cards][{i}] must be object with card_id, qty")
            continue
        cid = entry.get("card_id")
        qty = entry.get("qty")
        if not cid or not isinstance(qty, int):
            ctx.add(path, "ERROR", f"[cards][{i}] missing/invalid card_id or qty")
            continue

        total_qty += qty

        meta = _load_card_meta(ctx, cid)
        if not meta:
            ctx.add(path, "ERROR", f"[cards][{i}] card_id '{cid}' not found in CARDS")
            continue

        # Name-Zusammenlegung: identische Namen (über Sprachen/Printings) zusammenfassen
        name = meta.get("name") or meta.get("title") or cid
        name_counts[name] = name_counts.get(name, 0) + qty

        # Rarity/Unique zählen
        is_rare, is_unique = rarity_flags(meta)
        if is_rare:
            rare_count += qty
        if is_unique:
            unique_count += qty

        # Hero in Liste?
        if hero_id and cid == hero_id:
            hero_seen += qty

        # Fraktionsregel
        if same_faction_as_hero and hero_faction:
            cf = (meta.get("faction") or "").upper()
            if cf and cf != hero_faction:
                ctx.add(path, "ERROR", f"[cards][{i}] '{name}' faction '{cf}' != hero faction '{hero_faction}'")

        # Token/Spielsteine nicht im Deck
        if norm_type(meta.get("type", "")) == "token":
            ctx.add(path, "ERROR", f"[cards][{i}] '{name}' appears to be a token")

    # Mengen-Checks
    if total_qty < min_cards or total_qty > max_cards:
        ctx.add(path, "ERROR", f"Deck size {total_qty} not in [{min_cards}, {max_cards}]")

    for nm, cnt in name_counts.items():
        if cnt > max_same:
            ctx.add(path, "ERROR", f"More than {max_same} copies of '{nm}' ({cnt})")

    if rare_count > max_rare:
        ctx.add(path, "ERROR", f"Too many rare cards: {rare_count} > {max_rare}")

    if unique_count > max_unique:
        ctx.add(path, "ERROR", f"Too many unique cards: {unique_count} > {max_unique}")

    if unique_hero and hero_seen != 1:
        ctx.add(path, "ERROR", f"Hero copies must be exactly 1 (found {hero_seen})")

def scan_and_validate(ctx: Context):
    # 1) Zuerst Karten indexieren (bessere Deck-Validierung)
    for p in ctx.root.rglob("CARDS/**/*.json"):
        if looks_like_card_file(p):
            validate_card_file(ctx, p)

    # 2) Collections
    for p in ctx.root.rglob("COLLECTION/*.json"):
        if looks_like_collection_file(p):
            validate_collection_file(ctx, p)

    # 3) Rules
    for p in ctx.root.rglob("RULES/*"):
        if looks_like_rules_file(p):
            validate_rules_file(ctx, p)

    # 4) Decks
    for p in ctx.root.rglob("DECKS/**/*.json"):
        if looks_like_deck_file(p):
            validate_deck_file(ctx, p)

def print_summary(ctx: Context, strict: bool):
    # Gruppiert ausgeben
    errs = [f for f in ctx.findings if f.level == "ERROR"]
    warns = [f for f in ctx.findings if f.level == "WARN"]

    def rel(p: Path) -> str:
        try:
            return str(p.relative_to(ctx.root))
        except Exception:
            return str(p)

    if errs:
        print("\n ERRORS:")
        for f in errs:
            print(f"  - {rel(f.path)} :: {f.message}")
    if warns:
        print("\n  WARNINGS:")
        for f in warns:
            print(f"  - {rel(f.path)} :: {f.message}")

    print("\n—" * 40)
    print(f"Scanned root: {ctx.root}")
    print(f"Indexed cards: {len(ctx.card_index)}")
    print(f"Findings: {len(errs)} errors, {len(warns)} warnings")
    print("Result:", "FAIL" if (errs or (strict and warns)) else "OK")

def main():
    ap = argparse.ArgumentParser(description="Validate Altered Knowledge Repository")
    ap.add_argument("--root", default=".", help="Repo root directory")
    ap.add_argument("--schema", default="UTILS/validation_schema.json", help="Path to validation schema JSON")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    schema_path = (root / args.schema).resolve()

    if not schema_path.exists():
        print(f"ERROR: Schema file not found at {schema_path}", file=sys.stderr)
        sys.exit(1)

    schema = load_json(schema_path)
    if isinstance(schema, dict) and "__load_error__" in schema:
        print(f"ERROR: Failed to load schema: {schema['__load_error__']}", file=sys.stderr)
        sys.exit(1)

    ctx = Context(root=root, schema=schema)
    scan_and_validate(ctx)
    print_summary(ctx, strict=args.strict)
    sys.exit(1 if (ctx.has_errors or (args.strict and ctx.has_warnings)) else 0)

if __name__ == "__main__":
    main()
