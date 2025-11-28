import json
from pathlib import Path
from tqdm import tqdm

# ---------------- CONFIG ----------------
INPUT_FOLDER = Path("C:/Users/windows10/Lexicon/BigSearch/Inverted Index")
OUTPUT_FILE = Path("C:/Users/windows10/Lexicon/BigSearch/Inverted Index/inverted_index_final.json")

# Grab all batch files sorted numerically by batch number
BATCH_FILES = sorted(INPUT_FOLDER.glob("inverted_index_batch_*.json"),
                     key=lambda x: int(x.stem.split("_")[-1]))

# ---------------- MERGE FUNCTION ----------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
    out_f.write("{\n")  # start of JSON object
    first = True

    for batch_file in tqdm(BATCH_FILES, desc="Merging batches"):
        with open(batch_file, "r", encoding="utf-8") as f:
            batch_data = json.load(f)

        for word_id, postings in batch_data.items():
            if not first:
                out_f.write(",\n")
            first = False
            json.dump(word_id, out_f)
            out_f.write(": ")
            json.dump(postings, out_f)
        del batch_data  # free memory

    out_f.write("\n}")  # end of JSON object

print(f"[INFO] All batches merged. Final inverted index saved to {OUTPUT_FILE.name}")
