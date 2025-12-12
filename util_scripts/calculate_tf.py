import orjson
import msgpack

barrels_index = {}
with open("../Barrels/barrels_index.json", "rb") as f:
    barrels_index = orjson.loads(f.read())

tf_map = {}
cache_barrels = {}
cache_additions = []

for word, barrels_index in barrels_index.items():
    tf_map[word] = 0
    barrel_id, index = barrels_index
    if barrel_id not in cache_barrels:
        with open(f"../Barrels/{barrel_id}.msgpack", "rb") as f:
            cache_barrels[barrel_id] = msgpack.unpackb(f.read(), raw=False)
            cache_additions.append(barrel_id)
    
    tf_map[word] = len(cache_barrels[barrel_id][index])
    print(f"Calculated TF for word '{word}': {tf_map[word]}")
    if len(cache_barrels) > 2:
        to_remove = cache_additions.pop(0)
        del cache_barrels[to_remove]

with open("../Barrels/term_frequencies.json", "wb") as f:
    f.write(orjson.dumps(tf_map))