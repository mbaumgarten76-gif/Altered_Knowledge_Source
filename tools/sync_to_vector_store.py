# tools/sync_to_vector_store.py
import os, glob
from typing import List
from openai import OpenAI

# --- Konfiguration ---
VECTOR_STORE_NAME = os.environ.get("VECTOR_STORE_NAME", "Altered Knowledge")
VECTOR_STORE_ID   = os.environ.get("VECTOR_STORE_ID")  # optional vordefiniert (vs_...)
INCLUDE_GLOBS     = [
    "SETS/**/*.json",
    "COLLECTION/**/*.json",
    "RULES/**/*.*",         # pdf/md/json/txt ...
    "WEB_KB/**/*.json",     # optional: Keywords/Rulings/Archetypen
]
EXCLUDE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}  # Bilder weglassen

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def find_files() -> List[str]:
    files = []
    for pat in INCLUDE_GLOBS:
        files.extend(glob.glob(pat, recursive=True))
    final = []
    for f in files:
        if os.path.isdir(f):
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext in EXCLUDE_EXT:
            continue
        final.append(f)
    return sorted(set(final))

def ensure_vector_store() -> str:
    """Erstellt einen Vector Store, falls keine ID vorgegeben ist."""
    global VECTOR_STORE_ID
    if VECTOR_STORE_ID:
        return VECTOR_STORE_ID
    vs = client.vector_stores.create(name=VECTOR_STORE_NAME)
    VECTOR_STORE_ID = vs.id
    print(f"[info] Created vector store: {VECTOR_STORE_ID}")
    return VECTOR_STORE_ID

def upload_files(vs_id: str, paths: List[str]):
    """Lädt Dateien hoch und stößt die Ingestion an (blockierend bis fertig)."""
    if not paths:
        print("[warn] No files found for upload.")
        return
    uploaded_ids = []
    for p in paths:
        with open(p, "rb") as fh:
            f = client.files.create(file=fh, purpose="assistants")
        uploaded_ids.append(f.id)
        print(f"[up] {p} -> {f.id}")

    batch = client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vs_id,
        file_ids=uploaded_ids
    )
    print(f"[done] Ingestion: {batch.status}; counts={batch.file_counts}")

if __name__ == "__main__":
    vs_id = ensure_vector_store()
    files = find_files()
    if not files:
        print("[warn] keine Upload-Dateien gefunden – prüfe Include-Pfade.")
    else:
        upload_files(vs_id, files)
    # immer die ID am Ende ausgeben (für Logs/Outputs)
    print(f"VECTOR_STORE_ID={vs_id}")
