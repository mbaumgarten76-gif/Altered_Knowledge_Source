import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SETS_DIR = REPO_ROOT / "SETS"
UNIQUES_DIR = REPO_ROOT / "UNIQUES" / "cards"
COLLECTION_DIR = REPO_ROOT / "COLLECTION"
RULES_DIR = REPO_ROOT / "RULES"
HISTORY_DIR = REPO_ROOT / "HISTORY"
MANIFEST_PATH = REPO_ROOT / "manifest.json"

def build_manifest():
    manifest = {
        "sets": {},
        "cards": [],
        "uniques": {"files": []},
        "collections": {"files": []},
        "rules": {"files": []},
        "history": {"files": []}
    }

    for set_dir in sorted(SETS_DIR.glob("*")):
        if not set_dir.is_dir():
            continue

        set_name = set_dir.name
        manifest["sets"].setdefault(set_name, {})

        for lang_file in sorted(set_dir.glob("*.json")):
            lang = lang_file.stem.split("_")[-1].upper()
            manifest["sets"][set_name][lang] = str(lang_file.relative_to(REPO_ROOT))

            try:
                data = json.loads(lang_file.read_text(encoding="utf-8"))
                for card in data:
                    manifest["cards"].append({
                        "name": card.get("name"),
                        "reference": card.get("reference"),
                        "collectorNumber": card.get("collectorNumber"),
                        "set": set_name,
                        "language": lang,
                        "path": str(lang_file.relative_to(REPO_ROOT))
                    })
            except Exception as e:
                print(f"⚠️ Fehler beim Lesen von {lang_file}: {e}")

    if UNIQUES_DIR.exists():
        for unique_file in sorted(UNIQUES_DIR.glob("*.json")):
            manifest["uniques"]["files"].append(str(unique_file.relative_to(REPO_ROOT)).replace("\\", "/"))

    if COLLECTION_DIR.exists():
        for col_file in sorted(COLLECTION_DIR.glob("*.json")):
            manifest["collections"]["files"].append(str(col_file.relative_to(REPO_ROOT)).replace("\\", "/"))

    if RULES_DIR.exists():
        for rule_file in sorted(RULES_DIR.iterdir()):
            if rule_file.suffix.lower() in [".json", ".pdf"]:
                manifest["rules"]["files"].append(str(rule_file.relative_to(REPO_ROOT)).replace("\\", "/"))

    if HISTORY_DIR.exists():
        for hist_file in sorted(HISTORY_DIR.glob("*.json")):
            manifest["history"]["files"].append(str(hist_file.relative_to(REPO_ROOT)).replace("\\", "/"))

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✅ Manifest erfolgreich aktualisiert.")
    print(f"   {len(manifest['cards'])} Karten aus {len(manifest['sets'])} Sets eingelesen.")
    print(f"   {len(manifest['uniques']['files'])} Unique-Dateien gefunden.")

if __name__ == "__main__":
    build_manifest()
