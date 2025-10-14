# <img src="https://www.altered.gg/apple-touch-icon.png" width="32" alt="Altered.gg Logo"/> Altered TCG Card Database

## 🎯 Goal
This project aims to provide a **community-driven repository** of all **non-unique cards** from the **Altered TCG**,  
available in every supported language.  

The purpose is to reduce unnecessary load on the official Altered API servers.  
Since repeated API calls may trigger throttling or overload, we recommend using this local JSON database first  
before sending new HTTP requests to the official API.

---

## 📂 Folder Structure

Files are stored using the following path pattern :
```bash
./
├── SETS/                        # All sets grouped here
│ ├── CORE/                      # Set folder (set code as name)
│ │ ├── CORE_EN.json             # JSON file per language
│ │ └── ...
│ └── ...
│
├── META/                        # Metadata about cards & filters
│ ├── card_sets_en.json
│ ├── filter_data_en.json
│ └── ...
│
└── HISTORY/                     # English-only history of card changes
├── cards_history_CORE.json
├── cards_history_COREKS.json
└── ...
```

- **SETS/** → Contains all card data grouped by set code, each set has its own folder, and inside, one file per language.  
- **META/** → Contains only metadata (types, sets, factions, rarities, etc.).  
- **HISTORY/** → Contains versioned history of card changes (English only, per set).

---

## 🌍 Supported Languages
- English (`EN`)
- French (`FR`)
- Spanish (`ES`)
- Italian (`IT`)
- German (`DE`)

---

## 📜 Data Format
Each file inside `SETS/` contains the exact JSON structure returned by the official **Altered API**,  
with no modification to the schema (only separated by set and language).

---

## 📖 License
MIT License – feel free to use, share, and improve.  
Please credit the community and the Altered TCG project.  
