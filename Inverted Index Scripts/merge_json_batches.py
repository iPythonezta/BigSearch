"""
Merge all JSON inverted index batches into a single file.
Simply combines posting lists for each term across all batches.
"""

import json
import os
from tqdm import tqdm


def main():
    batch_dir = r"..\Inverted Index\JsonBatches"
    output_file = r"..\Inverted Index\JsonBatches\inverted_index_json.json"
    num_batches = 4

    inverted_index = {}

    for i in range(1, num_batches + 1):
        batch_file = os.path.join(batch_dir, f"inverted_index_json_part_{i}.json")
        
        print(f"Loading batch {i}...")
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_index = json.load(f)
        
        for word_id, postings in tqdm(batch_index.items(), desc=f"Merging batch {i}"):
            if word_id not in inverted_index:
                inverted_index[word_id] = []
            inverted_index[word_id].extend(postings)
        
        del batch_index
        print(f"Merged batch {i}\n")

    print("Writing merged index...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(inverted_index, f)

    print(f"Done! Merged index saved to: {output_file}")


if __name__ == "__main__":
    main()
