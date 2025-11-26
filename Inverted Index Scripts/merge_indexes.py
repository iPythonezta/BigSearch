import json 

inverted_index = {}

for i in range(1, 6):
    with open(f'..\\Inverted Index\\inverted_index_part_{i}.json', 'r', encoding='utf-8') as f:
        part_index = json.load(f)
    for word_id, postings in part_index.items():
        if word_id not in inverted_index:
            inverted_index[word_id] = []
        inverted_index[word_id].extend(postings)
    del part_index
    print(f"Merged part {i}")

with open('..\\Inverted Index\\inverted_index.json', 'w', encoding='utf-8') as f:
    json.dump(inverted_index, f)
