import json
import pathlib

# === Pfade ===
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]  # eine Ebene über /UTILS/
MANIFEST_PATH = REPO_ROOT / "manifest.json"

# === Suchmuster für Kartenverzeichnisse ===
CARD_DIRS = [
    "CARDS/DE",
    "CARDS/EN",
    "UNIQUES/cards"
]

# === Hilfsfunktion ===
def list_json_files(base_path: pathlib.Path):
    """Ermittle alle JSON-Dateien rekursiv unterhalb eines Pfades (relativ zum Repo-Root)."""
    return [
        str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        for path in base_path.rglob("*.json")
    ]

# === Hauptfunktion ===
def update_manifest():
    # Aktuelles Manifest laden oder neues Grundgerüst erstellen
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {}

    # Karten-Dateien sammeln
    all_cards = []
    for card_dir in CARD_DIRS:
        folder = REPO_ROOT / card_dir
        if folder.exists():
            all_cards.extend(list_json_files(folder))

    # Manifest-Eintrag für Karten aktualisieren
    manifest.setdefault("cards", {})
    manifest["cards"]["patterns"] = [f"{d}/*.json" for d in CARD_DIRS]
    manifest["cards"]["files"] = sorted(all_cards)

    # Manifest speichern
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✅ Manifest aktualisiert ({len(all_cards)} Karten eingetragen).")

# === Ausführung ===
if __name__ == "__main__":
    update_manifest()
