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

# ------------------ Utilities ------------------
def normalize_and_tokenize(text):
    """
    Tokenize text to match the C++ lexicon extraction logic.
    Extracts alphanumeric tokens, preserving unicode characters.
    """
    if not isinstance(text, str):
        return []
    
    tokens = []
    word = []
    
    for c in text:
        # Match C++ logic: isalnum(c) || c >= 128 (unicode)
        if c.isalnum() or ord(c) >= 128:
            word.append(c.lower())
        else:
            if word:
                tokens.append(''.join(word))
                word = []
    
    # Don't forget the last word
    if word:
        tokens.append(''.join(word))
    
    return tokens


# ------------------ Process One File ------------------
def process_json_file(args):
    file_path, words = args

    with open(file_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # Fix docid source - add P prefix for research papers
    docid = "P" + os.path.basename(file_path).replace(".json", "")
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
    # Match C++ logic: extract ALL fields from author objects
    for author in doc.get("metadata", {}).get("authors", []):
        if isinstance(author, str):
            # If author is a plain string
            for tok in normalize_and_tokenize(author):
                if len(positions_map[tok]) < MAX_POS:
                    positions_map[tok].append(pos)
                group1[tok] += 1
                pos += 1
        elif isinstance(author, dict):
            # Extract all string fields from author object (first, last, middle, suffix, affiliation, email, etc.)
            for key, value in author.items():
                if isinstance(value, str):
                    for tok in normalize_and_tokenize(value):
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
    lexicon_path = r"..\Lexicon\lexicons_ids.json"
    forward_index_path = r"..\Forward Index\forward_index_pdf_files.json"
    json_files_dir = r"..\Data\Cord 19\document_parses\pdf_json"
    inverted_index_dir = r"..\Inverted Index\JsonBatches"

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

    # Free memory before processing
    del forward_index

    # Process in batches (similar to HTML inverted index)
    batch_size = 10000
    for i in range(0, len(args), batch_size):
        inverted_index = {}
        for word, word_id in lexicon.items():
            inverted_index[word_id] = []
        
        batch_args = args[i:i + batch_size]
        
        with Pool(cpu_count()) as pool:
            results = list(
                tqdm(
                    pool.imap(process_json_file, batch_args),
                    total=len(batch_args),
                    desc=f"Processing files {i+1} to {min(i+batch_size, len(args))}"
                )
            )

        # Merge batch results
        for hitlists in results:
            for word, entry in hitlists.items():
                word_id = lexicon[word]
                inverted_index[word_id].append(entry)

        # Output batch file
        out_file = os.path.join(
            inverted_index_dir,
            f"inverted_index_json_part_{i//batch_size + 1}.json"
        )

        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(inverted_index, f)

        del inverted_index
        del results
        del batch_args

    del args
    del lexicon

    print("Done building inverted index")


if __name__ == "__main__":
    main()