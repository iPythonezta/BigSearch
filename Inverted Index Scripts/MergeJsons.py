import json
import os
from tqdm import tqdm
from collections import defaultdict

inverted_index_dir = r"C:\Users\windows10\Lexicon\BigSearch\Data\Inverted Index"
final_index_path = os.path.join(inverted_index_dir, "final_inverted_index.json")

all_batches = [f for f in os.listdir(inverted_index_dir) if f.startswith("inverted_index_batch_") and f.endswith(".json")]

final_index = defaultdict(list)

for batch_file in tqdm(all_batches, desc="Merging batches"):
    batch_path = os.path.join(inverted_index_dir, batch_file)
    with open(batch_path, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
    for word, hits in batch_data.items():
        final_index[word].extend(hits)

# Save final index
with open(final_index_path, 'w', encoding='utf-8') as f:
    json.dump(final_index, f)

print(f"Final inverted index saved to {final_index_path}")
