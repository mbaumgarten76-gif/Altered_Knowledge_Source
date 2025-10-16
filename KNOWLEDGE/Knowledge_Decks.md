# Modul: Deck-Verwaltung und Analyse

## 📘 Speicherort
Alle Decks liegen unter `/DECKS/` mit zwei Unterordnern:
- `/DECKS/MYSELF/` → Eigene Decklisten
- `/DECKS/OTHERS/` → Decklisten anderer Spieler (z. B. Turnierdecks)

## 🔍 Zugriff
Beim Laden von Deckdaten:
1. Durchsuche `/DECKS/MYSELF/*.json` und `/DECKS/OTHERS/*.json`.
2. Lade bei Bedarf über `raw_githubusercontent_com__jit_plugin.get_file`.
3. Verarbeite Karteninhalte analog zur Collection-Logik (Lazy Loading aktiv).

## 🧠 Funktionen
- Deckvalidierung nach Constructed-Regeln
- Vergleich eigener Decks mit „OTHERS“-Decks
- Statistische Auswertung (Kosten, Rarität, Fraktionsverteilung)
- Vorschläge zur Verbesserung basierend auf Sammlung und Meta-Decks
