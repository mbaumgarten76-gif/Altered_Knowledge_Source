# 🧠 Altered DeckBuilder – Knowledge Module Overview

Dieses Verzeichnis enthält die **Wissensmodule** des *Altered DeckBuilder GPT*.  
Die Module bilden gemeinsam die vollständige Funktionslogik des Chatbots und werden 
bei jeder Unterhaltung automatisch geladen.

---

## ⚙️ Funktionsweise

Beim Start des GPT lädt der Chatbot automatisch alle `.md`-Dateien in diesem Verzeichnis, 
um sein internes Wissen aufzubauen.  
Jedes Modul deckt einen klar definierten Themenbereich ab (z. B. Regeln, Kartensuche, 
Lazy Loading oder Verhalten).

Die Module sind miteinander verknüpft und ergänzen sich zu einer einheitlichen Wissensbasis.

---

## 📁 Modulübersicht

| Datei | Beschreibung |
|--------|---------------|
| **System_Main.md** | Hauptmodul – Rolle, Zweck und Initialisierung des GPT |
| **Knowledge_GitHubAccess.md** | Zugriff auf das Repository und Lazy-Loading-Verhalten |
| **Knowledge_CardSearch.md** | Regeln zur Kartensuche, Fraktionslogik und Unique-Verarbeitung |
| **Knowledge_Rules.md** | Constructed-Regeln, Keyword-Definitionen und Regelverweise |
| **Knowledge_Sources.md** | Quellenpriorität und offizielle Referenzen |
| **Knowledge_Behavior.md** | Verhalten, Sprachregeln, Deckbau-Unterstützung |
| **Knowledge_Technical.md** | Fehlerbehandlung, Transparenz, Systemziele |

---

## 🔄 Aktualisierung

Wenn ein Modul geändert oder erweitert werden soll:

1. Öffne die entsprechende Datei in diesem Verzeichnis.  
2. Passe den Text oder die Logik an (Markdown-Format beibehalten).  
3. Committe die Änderungen direkt in den `main`-Branch.  
4. Der GPT lädt beim nächsten Start automatisch die aktualisierte Version.

> 💡 **Hinweis:**  
> Du musst im GPT-Store nichts neu hochladen.  
> Alle Knowledge-Dateien werden direkt aus GitHub geladen.

---

## 🔐 Datenquellen

Die Knowledge-Module verweisen dynamisch auf:
- `CARDS/` – alle Karten und Sets (DE/EN)
- `UNIQUES/` – alle Unique-Karten
- `COLLECTION/` – Sammlungsdateien (Kartenbesitz)
- `RULES/` – Regelwerke und Keyword-Definitionen
- `HISTORY/` – Versions- und Änderungsprotokolle

Diese Verzeichnisse werden automatisch über die `manifest.json` eingebunden.

---

## 🧩 Prioritäten & Quellenordnung

1. Offizielle Repository-Daten (`Altered_Knowledge_Source`)
2. Offizielle Website ([altered.gg](https://www.altered.gg/en-us))
3. Community-Quellen ([alteredtcg.blog](https://alteredtcg.blog))

Community-Informationen werden nur ergänzend genutzt und stets gekennzeichnet.

---

## 🧰 Beispiel für Erweiterungen

Du kannst weitere Module hinzufügen, indem du neue Dateien im gleichen Format anlegst, z. B.:

- `Knowledge_MetaDecks.md` – Analyse starker Community-Decks  
- `Knowledge_Statistics.md` – Auswertung von Karten- und Fraktionswerten  
- `Knowledge_Combos.md` – Synergie- und Kombo-Analysen  

Jede Datei mit Präfix `Knowledge_` wird automatisch erkannt und geladen.

---

## 🏁 Fazit

Dieses Verzeichnis stellt das zentrale Wissensfundament für den **Altered DeckBuilder GPT** dar.  
Alle hier enthaltenen Module sind modular aufgebaut, versionierbar und können unabhängig gepflegt werden.  
Damit bleibt der Chatbot erweiterbar, wartbar und dauerhaft mit dem Repository synchron.
