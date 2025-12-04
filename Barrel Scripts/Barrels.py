import ijson
import json
import os

# === Input files ===
pdf_index_file = r"..\Inverted Index\JsonBatches\inverted_index_dropped_keys_json.json"
html_index_file = r"..\Inverted Index\inverted_index_dropped_keys.json"
current_lexicon_file = r"..\Lexicon\lexicons_ids.json"

# === Output directory ===
parent_barrels_folder = "..\\Barrels"
os.makedirs(parent_barrels_folder, exist_ok=True)
new_lexicon_file = os.path.join(parent_barrels_folder, "lexicon-Of-Barrels.json")

# === Barrel size limit (approximate in MB) ===
BARREL_SIZE_MB = 90
BARREL_SIZE_BYTES = BARREL_SIZE_MB * 1024 * 1024

# ================== FUNCTIONS ==================
def estimate_size_in_bytes(obj):
    return len(json.dumps(obj).encode('utf-8'))

# ================== LOAD CURRENT LEXICON ==================
with open(current_lexicon_file, 'r', encoding='utf-8') as f:
    old_lexicon = json.load(f)

# Sort words by wordid to match inverted index order
words_sorted = sorted(old_lexicon.items(), key=lambda x: x[1])  # (word, wordid)

# ================== OPEN STREAMS ==================
pdf_f = open(pdf_index_file, 'rb')
html_f = open(html_index_file, 'rb')
pdf_stream = ijson.items(pdf_f, 'item')
html_stream = ijson.items(html_f, 'item')

# ================== INITIALIZE ==================
current_barrel = []
current_barrel_size = 0
barrel_number = 0
new_lexicon = {}

# ================== PROCESS ==================
try:
    for word, wordid in words_sorted:
        # Get postings from both indexes
        try:
            pdf_obj = next(pdf_stream)
        except StopIteration:
            pdf_obj = []

        try:
            html_obj = next(html_stream)
        except StopIteration:
            html_obj = []

        # Merge postings (PDF first)
        merged_postings = pdf_obj + html_obj

        # Record offset inside barrel
        offset_in_barrel = len(current_barrel)
        new_lexicon[word] = [barrel_number, offset_in_barrel]

        # Estimate size of this word
        word_size = estimate_size_in_bytes(merged_postings)

        # Check if adding this word exceeds barrel size
        if current_barrel_size + word_size >= BARREL_SIZE_BYTES:
            # Write current barrel to disk
            barrel_file_path = os.path.join(parent_barrels_folder, f"barrel_{barrel_number}.json")
            with open(barrel_file_path, 'w', encoding='utf-8') as bf:
                json.dump(current_barrel, bf, separators=(',', ':'))
            print(
                f"Written barrel_{barrel_number}.json with {len(current_barrel)} words (~{current_barrel_size / 1024 / 1024:.2f} MB)")

            # Start a new barrel
            barrel_number += 1
            current_barrel = []
            current_barrel_size = 0
            offset_in_barrel = 0  # reset offset in new barrel
            new_lexicon[word] = [barrel_number, offset_in_barrel]

        # Add the word to the current barrel
        current_barrel.append(merged_postings)
        current_barrel_size += word_size


        # Print the wordid just appended
        print(f"Appended wordid {wordid} to barrel_{barrel_number}.json")

finally:
    pdf_f.close()
    html_f.close()


# Write the last barrel if it has any words
if current_barrel:
    barrel_file_path = os.path.join(parent_barrels_folder, f"barrel_{barrel_number}.json")
    with open(barrel_file_path, 'w', encoding='utf-8') as bf:
        json.dump(current_barrel, bf)
    print(f"Written final barrel_{barrel_number}.json with {len(current_barrel)} words (~{current_barrel_size/1024/1024:.2f} MB)")

# Write new lexicon to disk
with open(new_lexicon_file, 'w', encoding='utf-8') as lf:
    json.dump(new_lexicon, lf, indent=2)

print(f"New lexicon saved to {new_lexicon_file}")
print(f"Total barrels created: {barrel_number + 1}")

