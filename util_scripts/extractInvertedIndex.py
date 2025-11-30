import ijson
import json

index_file = "Data/Inverted Index/inverted_index_dropped_keys.json" #change to JsonBatches/inverted_index_dropped_keys.json for PDF files
output_file = "Data/SampleOutputs/InvertedIndexHTMLs[1-100].json" #change to InvertedIndexPDFs[1-100].json for PDF files

max_objects = 100  # first 100 objects
count = 0
extracted = []

with open(index_file, 'rb') as f:
    for obj in ijson.items(f, 'item'):
        if obj:  # skip empty objects
            extracted.append(obj)
            count += 1
        if count >= max_objects:
            break

# Save to JSON
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(extracted, f, indent=2)

print(f"Extracted {count} non-empty objects from the top of the inverted index into {output_file}")
