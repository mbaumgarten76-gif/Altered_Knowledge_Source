from raw_githubusercontent_com__jit_plugin import get_file

# Beispiel: Manifest wird beim Start einmal geladen
manifest = load_json("manifest.json")

# Optionaler Zwischenspeicher (Performance)
_card_cache = {}

def load_card_by_name(name: str, manifest: dict):
    """
    Lädt eine Karte anhand ihres Namens (Teilstring oder genau).
    Unterstützt reguläre Karten (CARDS/) und Unique-Karten (UNIQUES/).
    """

    search_term = name.lower().strip()
    found_path = None

    # Suche in regulären Karten (DE + EN)
    for lang in ["DE", "EN"]:
        card_patterns = manifest.get("cards", {}).get("patterns", [])
        for pattern in card_patterns:
            if not pattern.startswith("CARDS/"):
                continue
            # Beispiel: Pfad enthält den Namen oder die Set-/Fraktionsstruktur
            if search_term in pattern.lower():
                found_path = pattern
                break
        if found_path:
            break

    # 2 Suche in Unique-Karten, falls noch nichts gefunden
    if not found_path:
        for pattern in manifest.get("cards", {}).get("patterns", []):
            if "UNIQUES" in pattern.upper():
                # Uniques werden einzeln durchsucht
                if search_term in pattern.lower():
                    found_path = pattern
                    break

    # 3 Wenn nichts gefunden dann klare Fehlermeldung
    if not found_path:
        return f"Diese Karte ('{name}') ist im Datensatz nicht enthalten."

    # 4 Lazy Loading mit Cache
    if found_path in _card_cache:
        return _card_cache[found_path]

    try:
        card_data = get_file({"filepath": found_path})
        _card_cache[found_path] = card_data
        return card_data
    except Exception as e:
        return f"Fehler beim Laden der Karte '{name}': {str(e)}"
