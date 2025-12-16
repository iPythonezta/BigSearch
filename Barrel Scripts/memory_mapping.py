import os
import ormsgpack
import json

BARRELS_DIR = "..\\Barrels"         # existing msgpack barrels
MMAP_DIR = "..\\MemoryMapBarrels"  # new memory-mapped barrels
os.makedirs(MMAP_DIR, exist_ok=True)

def convert_msgpack_to_mmap(barrel_file):
    barrel_id = os.path.splitext(os.path.basename(barrel_file))[0]
    out_dir = os.path.join(MMAP_DIR, f"barrel_{barrel_id}")
    os.makedirs(out_dir, exist_ok=True)

    # Load existing MSGPACK barrel
    with open(barrel_file, "rb") as f:
        barrel_data = ormsgpack.unpackb(f.read())

    postings_file = os.path.join(out_dir, "postings.bin")
    offsets_file = os.path.join(out_dir, "offsets.json")

    offsets = {}
    cursor = 0

    with open(postings_file, "wb") as bf:
        for idx, posting_list in enumerate(barrel_data):
            blob = ormsgpack.packb(posting_list)
            bf.write(blob)
            offsets[idx] = (cursor, len(blob))
            cursor += len(blob)

    # Save offsets
    with open(offsets_file, "w") as f:
        json.dump(offsets, f)

    print(f"Barrel {barrel_id} converted → {len(barrel_data)} postings")

# Convert all MSGPACK barrels
for fname in os.listdir(BARRELS_DIR):
    if fname.endswith(".msgpack"):
        convert_msgpack_to_mmap(os.path.join(BARRELS_DIR, fname))

print("All barrels converted to memory-mapped format.")