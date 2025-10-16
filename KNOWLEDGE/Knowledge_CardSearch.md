# Knowledge Modul – Kartensuche und Unique-Handling
## Namenssuche in Karteninhalten
1. Öffne jede Datei aus den Pfaden:
   CARDS/DE/*/*/*.json, CARDS/EN/*/*/*.json, UNIQUES/cards/*.json
2. Prüfe, ob im Feld "name" oder "name_en" der angegebene Kartenname steht.
3. Wenn eine Übereinstimmung gefunden wird, lade genau diese Datei.
4. Wenn mehrere Dateien denselben Namen enthalten, gib alle Varianten aus.
5. Wenn keine Übereinstimmung gefunden wird, antworte: „Diese Karte ist im Datensatz nicht enthalten.“
