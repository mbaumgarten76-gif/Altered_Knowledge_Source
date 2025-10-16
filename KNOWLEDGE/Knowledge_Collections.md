# Modul: Collection-Integration & Deckbauprüfung

## 🧠 Besitzprüfung
- Lade automatisch `/COLLECTION/*.json`.
- Jede Datei enthält `card_id` und `count`.
- Nur Karten mit `count > 0` gelten als im Besitz befindlich.
- Karten mit `count = 0` oder ohne Eintrag gelten als „nicht besessen“.

## ⚙️ Deckbauvalidierung
Beim Erstellen oder Analysieren von Decks:
- Prüfe, ob jede Karte im Besitz ist.
- Nur besessene Karten dürfen empfohlen werden.
- Nicht-besessene Karten markieren mit:
  „Diese Karte befindet sich nicht in deiner Sammlung.“
- Collection-Daten beeinflussen keine Regeln oder Effekte.

## 🔄 Erweiterte Collection-Verarbeitung

Beim Abruf von Sammlungsdaten (z. B. „Zeige mir alle Axiom-Karten“):

1. Lade **alle JSON-Dateien** aus dem Verzeichnis `/COLLECTION/`.
2. Kombiniere alle Karteneinträge zu einer Gesamtliste.
3. Filtere diese Liste nach der angeforderten Fraktion (z. B. AX für Axiom).
4. Summiere Duplikate (gleiche Karten-ID) und gib die Gesamtzahl (`count`) aus.
5. Gib die Ergebnisse als Tabelle mit `Name`, `Rarität`, `Anzahl` zurück.

### Beispielausgabe
| Name | Rarität | Anzahl |
|------|----------|--------|
| Daring Porter | Common | 3 |
| Thoughtful Navigator | Rare | 1 |
| Determined Scholar | Common | 2 |
| Arcane Mechanist | Unique | 1 |

Diese Methode gewährleistet, dass Karten aus **allen Sets** berücksichtigt werden,
nicht nur aus einem einzelnen Collection-File.
