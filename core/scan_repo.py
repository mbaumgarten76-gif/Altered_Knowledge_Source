Nachfolgend findest du ein komplettes, lauffähiges Erstsetup, um dein Git-Repository (mit den Ordnern `CARDS`, `COLLECTION`, `RULES`, `SETS`, `DECKS`, `HISTORY`) automatisch zu **scannen**, **validieren** und daraus **`manifest.json`** und hilfreiche **Index-Dateien** zu erzeugen. Außerdem ist ein optionaler GitHub-Action-Workflow dabei, der bei jedem Push die Manifest-Generierung ausführt und als Pull Request bereitstellt.

---

## ✅ Ziele

* Ordnerstruktur automatisch scannen
* JSON-Dateien syntaktisch prüfen
* Metadaten extrahieren (z. B. Sprache, Set, Fraktion, Seltenheit)
* `manifest.json` und thematische Indexe erzeugen
* Checksums (SHA-256) und Dateigrößen mitschreiben
* Optional: GitHub Action, die alles bei jedem Push ausführt

---

## 📦 Verzeichnisstruktur (Ist-Zustand)

```
CARDS/
COLLECTION/
RULES/
SETS/
DECKS/
HISTORY/
```

> Du kannst den nachfolgenden Code 1:1 in dein Repo übernehmen. Lege zusätzlich den Ordner `core/` und `.github/workflows/` an.

---

## 🧠 `core/scan_repo.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scannt das Repo (CARDS, COLLECTION, RULES, SETS, DECKS, HISTORY) und erzeugt:
- manifest.json (alle Dateien mit Metadaten)
- indexes/cards_index.json
- indexes/sets_index.json
- indexes/collection_index.json
- indexes/rules_index.json
- indexes/decks_index.json
- indexes/history_index.json

Nutzung:
    python -m core.scan_repo

oder
    python core/scan_repo.py
"""
from __future__ import annotations
import json
import os
import re
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "indexes"

# Welche Top-Level-Ordner wir scannen
TOP_LEVEL_FOLDERS = [
    "CARDS", "COLLECTION", "RULES", "SETS", "DECKS", "HISTORY"
]

# Heuristiken für Metadaten-Extraktion aus Pfaden/Dateinamen
LANG_PATTERN = re.compile(r"/(EN|DE|FR|ES|IT|PT|PL|RU|JA|ZH)/", re.IGNORECASE)
FACTION_PATTERN = re.compile(r"/(AXIOM|AX|BRAVOS|BR|LYRA|LY|OR|YZMIR|YZ|ALIZE|AZ|KAIJU|KJ)/", re.IGNORECASE)
SET_PATTERN = re.compile(r"/(CORE|COREKS|ALIZE|CYCLONE|BREEZE|TEMPEST|STORM|AXIOM|BRAVOS|LYRA|OR|YZMIR)/", re.IGNORECASE)
RARITY_PATTERN = re.compile(r"/(COMMON|C|RARE|R|EPIC|E|LEGENDARY|L|MYTHIC|M)/", re.IGNORECASE)

# JSON-Dekoder mit stabiler Fehlermeldung

def load_json_safely(p: Path) -> Tuple[Optional[Any], Optional[str]]:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def normpath(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT).as_posix())


def extract_meta_from_path(path: str) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    lang = LANG_PATTERN.search(path)
    faction = FACTION_PATTERN.search(path)
    setcode = SET_PATTERN.search(path)
    rarity = RARITY_PATTERN.search(path)

    if lang:
        meta["lang"] = lang.group(1).upper()
    if faction:
        meta["faction"] = faction.group(1).upper()
    if setcode:
        meta["set"] = setcode.group(1).upper()
    if rarity:
        # Normalisiere auf C/R/E/L/M, falls möglich
        r = rarity.group(1).upper()
        mapping = {
            "COMMON": "C", "C": "C",
            "RARE": "R", "R": "R",
            "EPIC": "E", "E": "E",
            "LEGENDARY": "L", "L": "L",
            "MYTHIC": "M", "M": "M",
        }
        meta["rarity"] = mapping.get(r, r)
    return meta


def file_kind_from_topdir(top: str) -> str:
    return {
        "CARDS": "card",
        "COLLECTION": "collection",
        "RULES": "rule",
        "SETS": "set",
        "DECKS": "deck",
        "HISTORY": "history",
    }.get(top, "other")


def scan_repo() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    manifest: Dict[str, Any] = {}
    problems: Dict[str, List[str]] = {}

    now_iso = datetime.now(timezone.utc).isoformat()

    for top in TOP_LEVEL_FOLDERS:
        base = REPO_ROOT / top
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_dir():
                continue
            rel = normpath(p)
            entry: Dict[str, Any] = {
                "path": rel,
                "size": p.stat().st_size,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
                "kind": file_kind_from_topdir(top),
                "sha256": sha256_of_file(p),
                "detected": extract_meta_from_path("/" + rel + "/"),
                "scanned_at": now_iso,
            }

            if p.suffix.lower() == ".json":
                data, err = load_json_safely(p)
                if err:
                    problems.setdefault(rel, []).append(f"JSON error: {err}")
                else:
                    entry["valid_json"] = True
                    # Optional: wichtige Felder extrahieren, falls vorhanden
                    if isinstance(data, dict):
                        # Kandidaten: id/ref, name, type, rarity, faction, set, lang
                        for k in ("id", "ref", "reference_id", "name", "type", "rarity", "faction", "set", "lang"):
                            if k in data:
                                entry.setdefault("meta", {})[k] = data[k]
            manifest[rel] = entry

    return manifest, problems


def build_indexes(manifest: Dict[str, Any]) -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _dump(obj: Any, name: str):
        (OUTPUT_DIR / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # Kartenindex
    cards = [v for v in manifest.values() if v.get("kind") == "card"]
    sets = [v for v in manifest.values() if v.get("kind") == "set"]
    rules = [v for v in manifest.values() if v.get("kind") == "rule"]
    decks = [v for v in manifest.values() if v.get("kind") == "deck"]
    history = [v for v in manifest.values() if v.get("kind") == "history"]
    collection = [v for v in manifest.values() if v.get("kind") == "collection"]

    # Karten sinnvoll gruppieren
    cards_index = {}
    for e in cards:
        d = e.get("detected", {})
        setcode = d.get("set", "UNKNOWN")
        cards_index.setdefault(setcode, []).append({
            "path": e["path"],
            "lang": d.get("lang"),
            "faction": d.get("faction"),
            "rarity": d.get("rarity") or (e.get("meta", {}).get("rarity")),
            "name": (e.get("meta", {}) or {}).get("name"),
            "id": (e.get("meta", {}) or {}).get("id") or (e.get("meta", {}) or {}).get("ref") or (e.get("meta", {}) or {}).get("reference_id"),
        })

    sets_index = {e["path"]: {"sha256": e["sha256"], "detected": e.get("detected", {})} for e in sets}
    rules_index = {e["path"]: {"sha256": e["sha256"], "detected": e.get("detected", {})} for e in rules}
    decks_index = {e["path"]: {"sha256": e["sha256"], "detected": e.get("detected", {})} for e in decks}
    history_index = {e["path"]: {"sha256": e["sha256"], "detected": e.get("detected", {})} for e in history}
    collection_index = {e["path"]: {"sha256": e["sha256"], "detected": e.get("detected", {}), "size": e["size"]} for e in collection}

    _dump(cards_index, "cards_index.json")
    _dump(sets_index, "sets_index.json")
    _dump(rules_index, "rules_index.json")
    _dump(decks_index, "decks_index.json")
    _dump(history_index, "history_index.json")
    _dump(collection_index, "collection_index.json")

    return {
        "cards_index": cards_index,
        "sets_index": sets_index,
        "rules_index": rules_index,
        "decks_index": decks_index,
        "history_index": history_index,
        "collection_index": collection_index,
    }


def main() -> int:
    manifest, problems = scan_repo()

    # manifest.json schreiben
    (REPO_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    idx = build_indexes(manifest)

    # Probleme reporten
    if problems:
        # Separate Datei für Fehlersammlung
        (REPO_ROOT / "scan_problems.json").write_text(
            json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"⚠️  Es wurden {sum(len(v) for v in problems.values())} Probleme gefunden. Siehe scan_problems.json")
    else:
        print("✅ Keine JSON-Fehler gefunden.")

    print("✅ manifest.json und Indexe wurden erzeugt.")
    print("   - manifest.json")
    print("   - indexes/cards_index.json")
    print("   - indexes/sets_index.json")
    print("   - indexes/rules_index.json")
    print("   - indexes/decks_index.json")
    print("   - indexes/history_index.json")
    print("   - indexes/collection_index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 🧩 `core/__init__.py`

```python
# leer, aber ermöglicht "python -m core.scan_repo"
```

---

## 📄 `.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtualenvs
.venv/
venv/
.env

# Build/Cache
*.log
*.tmp

# Artifacts
indexes/*.tmp
scan_problems.json

# OS
.DS_Store
Thumbs.db
```

---

## 📦 `requirements.txt`

```txt
# Keine externen Abhängigkeiten notwendig – Standardbibliothek reicht.
# Optional (für spätere Erweiterungen):
# pydantic>=2.7
# jsonschema>=4.22
```

---

## ▶️ Ausführen (lokal)

```bash
python -m core.scan_repo
```

Danach findest du in der Repo-Wurzel:

* `manifest.json`
* `indexes/` mit den generierten Teil-Indizes
* optional `scan_problems.json` falls JSON-Fehler gefunden wurden

Commit & Push:

```bash
git add manifest.json indexes/ scan_problems.json || true
git commit -m "Build manifest and indexes"
git push
```

---

## 🤖 Optional: GitHub Action (PR mit aktualisiertem Manifest)

Erzeugt bei jedem Push automatisch `manifest.json` + Indexe und öffnet einen Pull Request mit den Änderungen.

**Datei:** `.github/workflows/build-manifest.yml`

```yaml
name: Build Manifest

on:
  push:
    branches: [ main, master ]
  workflow_dispatch: {}

permissions:
  contents: write
  pull-requests: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run scanner
        run: |
          python -m pip install --upgrade pip
          # requirements optional
          # pip install -r requirements.txt
          python - <<'PY'
import sys, subprocess, pathlib
root = pathlib.Path('.').resolve()
(core := root/'core').mkdir(exist_ok=True)
if not (core/'scan_repo.py').exists():
    print('❌ core/scan_repo.py fehlt. Bitte Datei ins Repo committen.')
    sys.exit(1)
subprocess.check_call([sys.executable, '-m', 'core.scan_repo'])
PY

      - name: Commit changes
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: 'chore(manifest): auto-build manifest and indexes'
          file_pattern: |
            manifest.json
            indexes/**
            scan_problems.json

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v6
        with:
          title: "chore(manifest): update manifest & indexes"
          commit-message: "chore(manifest): auto-build manifest & indexes"
          branch: ci/manifest-update
          delete-branch: true
```

> Hinweis: Der Schritt „Commit changes“ pusht direkt auf den aktuellen Branch. Der PR-Schritt legt zusätzlich einen PR an. Du kannst auch nur einen der beiden Schritte nutzen.

---

## 🧾 Beispiel eines `manifest.json`-Eintrags

```json
{
  "CARDS/EN/ALIZE/AX/ALT_ALIZE_B_AX_37_C.json": {
    "path": "CARDS/EN/ALIZE/AX/ALT_ALIZE_B_AX_37_C.json",
    "size": 1234,
    "mtime": "2025-10-21T14:12:09.000000+00:00",
    "kind": "card",
    "sha256": "<sha256>",
    "detected": {"lang": "EN", "faction": "AX", "set": "ALIZE", "rarity": "C"},
    "scanned_at": "2025-10-21T16:00:00.000000+00:00",
    "valid_json": true,
    "meta": {
      "id": "ALT_ALIZE_B_AX_37_C",
      "name": "Daring Porter",
      "rarity": "C",
      "set": "ALIZE",
      "lang": "EN"
    }
  }
}
```

---

## 🔧 Erweiterungen (optional)

* **JSON-Schema-Validierung:** Hinterlege pro Ordner ein Schema (z. B. `SCHEMAS/cards.schema.json`) und prüfe mit `jsonschema`.
* **Striktere Metadaten:** Erzwinge `meta.id`, `meta.name`, `meta.rarity` usw. bei Karten.
* **Lazy Loading in Tools:** Die `indexes/*` Dateien sind kompakt, ideal zum schnellen Einlesen.

---

## 🆘 Nächste Schritte

1. Lege die oben gezeigten Dateien in deinem Repo an.
2. Führe lokal `python -m core.scan_repo` aus.
3. Prüfe `scan_problems.json` (falls vorhanden) und korrigiere fehlerhafte JSONs.
4. Aktiviere optional die GitHub Action.

Wenn du möchtest, passe ich die Heuristiken (`LANG/FACTION/SET/RARITY`) genauer an deine tatsächlichen Pfadmuster an. Teile mir dazu einfach Beispielpfade mit.
