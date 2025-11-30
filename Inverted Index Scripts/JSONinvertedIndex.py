"""
Build Inverted Index from JSON documents using multiprocessing.
"word_id": [
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
    ]
]
"""


import json
from collections import defaultdict, Counter
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import re
import os

MAX_POS = 15
BATCH_SIZE = 5000  # Adjustable

# ------------------ Utilities ------------------
def normalize_and_tokenize(text):
    """Lowercase, remove excess whitespace, and split into words."""
    text = re.sub(r"\s+", " ", text).strip()
    return [w.lower() for w in text.split() if w]

import json
from collections import defaultdict, Counter
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import re
import os

MAX_POS = 15
BATCH_SIZE = 5000   # you asked to reduce from 10k → 5k


# ------------------ Utilities ------------------
def normalize_and_tokenize(text):
    if not isinstance(text, str):
        return []
    text = re.sub(r"\s+", " ", text).strip()
    return [w.lower() for w in text.split() if w]


# ------------------ Process One File ------------------
def process_json_file(args):
    file_path, words = args

    with open(file_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # Fix docid source
    docid = os.path.basename(file_path).replace(".json", "")
    positions_map = defaultdict(list)

    # Section group counters:
    group1 = Counter()  # title + abstract + authors
    group2 = Counter()  # body_text
    group3 = Counter()  # references + ref_entries + back_matter

    pos = 0

    # ----- TITLE -----
    title = doc.get("metadata", {}).get("title", "")
    for tok in normalize_and_tokenize(title):
        if len(positions_map[tok]) < MAX_POS:
            positions_map[tok].append(pos)
        group1[tok] += 1
        pos += 1

    # ----- ABSTRACT -----
    for item in doc.get("abstract", []):
        for tok in normalize_and_tokenize(item.get("text", "")):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group1[tok] += 1
            pos += 1

    # ----- AUTHORS -----
    for author in doc.get("metadata", {}).get("authors", []):
        fullname = f"{author.get('first', '')} {author.get('last', '')}"
        for tok in normalize_and_tokenize(fullname):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group1[tok] += 1
            pos += 1

    # ----- BODY TEXT -----
    for item in doc.get("body_text", []):
        for tok in normalize_and_tokenize(item.get("text", "")):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group2[tok] += 1
            pos += 1

    # ----- BIB ENTRIES (titles only) -----
    for ref in doc.get("bib_entries", {}).values():
        for tok in normalize_and_tokenize(ref.get("title", "")):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group3[tok] += 1
            pos += 1

    # ----- REF ENTRIES (FIGREF, TABREF...) -----
    for ref in doc.get("ref_entries", {}).values():
        for tok in normalize_and_tokenize(ref.get("text", "")):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group3[tok] += 1
            pos += 1

    # ----- BACK MATTER -----
    for item in doc.get("back_matter", []):
        for tok in normalize_and_tokenize(item.get("text", "")):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group3[tok] += 1
            pos += 1


    # ------------------ BUILD HITLISTS ------------------
    hitlists = {}
    for word in words:

        g1 = group1[word]
        g2 = group2[word]
        g3 = group3[word]
        total = g1 + g2 + g3

        # DROP empty words
        if total == 0:
            continue

        hitlists[word] = [
            docid,
            positions_map[word],
            [
                g1,     # title + abstract + authors
                g2,     # body
                g3,     # references + ref_entries + back_matter
                total,  # total
                pos     # doc length
            ]
        ]

    return hitlists


# ------------------ MAIN ------------------
def main():
    lexicon_path = r"C:\Users\windows10\Lexicon\BigSearch\Data\Lexicon\lexicons_ids.json"
    forward_index_path = r"C:\Users\windows10\Lexicon\BigSearch\Data\Forward Index\forward_index_json.json"
    json_files_dir = r"C:\Users\windows10\Lexicon\BigSearch\Data\Cord 19\document_parses\pdf_json"
    inverted_index_dir = r"C:\Users\windows10\Lexicon\BigSearch\Data\Inverted Index"

    os.makedirs(inverted_index_dir, exist_ok=True)

    # Load lexicon
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    inverse_lexicon = {v: k for k, v in lexicon.items()}

    # Load forward index
    with open(forward_index_path, 'r', encoding='utf-8') as f:
        forward_index = json.load(f)

    # Prepare args
    args = []
    for file_id, word_ids in tqdm(forward_index.items(), desc="Preparing args"):
        words = [inverse_lexicon[w] for w in word_ids]
        file_path = os.path.join(json_files_dir, f"{file_id}.json")
        args.append((file_path, words))

    # Process in batches
    for i in range(0, len(args), BATCH_SIZE):
        batch_args = args[i:i+BATCH_SIZE]

        inverted_index = {word_id: [] for word_id in lexicon.values()}

        with Pool(cpu_count()) as pool:
            results = list(
                tqdm(
                    pool.imap(process_json_file, batch_args),
                    total=len(batch_args),
                    desc=f"Batch {i//BATCH_SIZE + 1}"
                )
            )

        # Merge
        for hitlists in results:
            for word, entry in hitlists.items():
                wid = lexicon[word]
                inverted_index[wid].append(entry)

        # Output file
        out_file = os.path.join(
            inverted_index_dir,
            f"inverted_index_batch_{i//BATCH_SIZE + 1}.json"
        )

        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(inverted_index, f)

        del inverted_index
        del results
        del batch_args

    print("✔ DONE building inverted index!")


if __name__ == "__main__":
    main()