"""
Inverted Index Generator from Forward Index JSON
(in_url removed from hit_counter)

Output JSON Structure:

{
    "word_id_1": [
        [
            "document_id",
            [pos1, pos2, ...],
            [
                title_author_abstract_count,
                body_text_count,
                other_section_count,
                total_count,
                doc_length
            ]
        ],
        ...
    ],
    ...
}
"""

import json
import csv
from pathlib import Path
from collections import Counter, defaultdict
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

# -------------------- CONFIG PATHS --------------------
FWD_INDEX_FILE  = Path("C:/Users/windows10/Lexicon/BigSearch/Forward Index/forward_index_json.json")
LEXICON_FILE    = Path("C:/Users/windows10/Lexicon/BigSearch/Lexicon/lexicons_ids.json")
OUTPUT_FOLDER   = Path("C:/Users/windows10/Lexicon/BigSearch/Inverted Index")
DOC_METADATA_CSV = Path("C:/Users/windows10/Lexicon/BigSearch/Data/Cord 19/metadata_cleaned.csv")

CHUNK_SIZE = 2500
MAX_POSITIONS_STORED = 15

# -------------------- LOAD LEXICON --------------------
with open(LEXICON_FILE.as_posix(), "r", encoding="utf-8") as f:
    lexicon = json.load(f)

inverse_lexicon = {v: k for k, v in lexicon.items()}

# -------------------- LOAD DOC_ID → URL FROM CSV --------------------
def load_doc_urls(csv_path):
    mapping = {}
    with open(csv_path.as_posix(), newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get("id"):
                mapping[row["id"]] = row.get("url", "")
    return mapping

doc_id_to_url = load_doc_urls(DOC_METADATA_CSV)
print("[INFO] Loaded document URLs from CSV")

# -------------------- PROCESS ONE DOC --------------------
def process_doc(doc_tuple):
    doc_id, word_ids_list = doc_tuple
    doc_length = len(word_ids_list)
    positions_map = defaultdict(list)

    for idx, wid in enumerate(word_ids_list):
        if len(positions_map[wid]) < MAX_POSITIONS_STORED:
            positions_map[wid].append(idx)

    counts = Counter(word_ids_list)

    doc_inv = {}
    for wid, pos_list in positions_map.items():
        total = counts.get(wid, 0)

        hit_counter = [
            0,        # title_author_abstract_count
            total,    # body_text_count
            0,        # other_section_count
            total,    # total_count
            doc_length
        ]

        doc_inv[wid] = [[doc_id, pos_list, hit_counter]]

    return doc_inv

# -------------------- BUILD INVERTED INDEX IN CHUNKS --------------------
def build_inverted_index_batched():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    with open(FWD_INDEX_FILE.as_posix(), "r", encoding="utf-8") as f:
        fwd = json.load(f)

    doc_tuples = list(fwd.items())
    del fwd

    batch_num = 1
    for i in range(0, len(doc_tuples), CHUNK_SIZE):
        chunk = doc_tuples[i:i + CHUNK_SIZE]
        print(f"[INFO] Processing batch {batch_num}, docs {i+1} to {i+len(chunk)}")

        batch_inverted = defaultdict(list)

        with Pool(processes=cpu_count()) as pool:
            results = list(
                tqdm(pool.imap(process_doc, chunk),
                     total=len(chunk),
                     desc="Indexing docs",
                     unit="docs")
            )

        for doc_inv in results:
            for wid, postings in doc_inv.items():
                batch_inverted[wid].extend(postings)

        out_path = OUTPUT_FOLDER / f"inverted_index_batch_{batch_num}.json"
        with open(out_path.as_posix(), "w", encoding="utf-8") as o:
            json.dump(batch_inverted, o)

        print(f"[INFO] Saved batch {batch_num} to {out_path}")

        batch_num += 1
        del results, chunk, batch_inverted

    del doc_tuples
    print("[INFO] All batches complete.")

if __name__ == "__main__":
    build_inverted_index_batched()