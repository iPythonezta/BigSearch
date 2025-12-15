import orjson
import msgpack
import time

# =========================
# CONFIG
# =========================

LEXICON_PATH = "../Lexicon/lexicons_ids_new.json"
TF_PATH = "../Barrels/term_frequencies.json"
OUTPUT_PATH = "../Autocomplete/autocomplete_trie.msgpack"

MIN_TF = 5
MIN_LEN = 4
BAD_SUFFIXES = ("ed", "ing", "ive", "al", "ous")

# =========================
# TRIE NODE
# =========================

class TrieNode:
    __slots__ = ("children", "word", "tf", "priority")

    def __init__(self):
        self.children = {}
        self.word = None
        self.tf = 0
        self.priority = 0.0

# =========================
# LOAD DATA
# =========================

print("Loading lexicon...")
with open(LEXICON_PATH, "rb") as f:
    lexicon = orjson.loads(f.read())

print("Loading term frequencies...")
with open(TF_PATH, "rb") as f:
    tf_map = orjson.loads(f.read())

print(f"Lexicon size: {len(lexicon)}")
print(f"TF entries: {len(tf_map)}")

# =========================
# VALIDATION + PRIORITY LOGIC
# =========================

def is_valid_autocomplete_term(word, tf):
    """Decide if the word should be considered for autocomplete."""
    if tf < MIN_TF:
        return False
    if len(word) < MIN_LEN:
        return False
    if not word.isalpha():
        return False
    return True

def compute_priority(word, tf):
    """Apply suffix penalties to TF for ranking."""
    penalty = 0.0
    for suffix in BAD_SUFFIXES:
        if word.endswith(suffix):
            penalty += tf * 0.4
    return tf - penalty

# =========================
# BUILD AUTOCOMPLETE VOCAB
# =========================

autocomplete_vocab = []

for word in lexicon.keys():
    tf = tf_map.get(word, 0)
    if is_valid_autocomplete_term(word, tf):
        priority = compute_priority(word, tf)
        autocomplete_vocab.append((word, tf, priority))

print(f"Autocomplete candidate words: {len(autocomplete_vocab)}")

# =========================
# BUILD TRIE
# =========================

root = TrieNode()

def insert(word, tf, priority):
    node = root
    for ch in word:
        node = node.children.setdefault(ch, TrieNode())
    node.word = word
    node.tf = tf
    node.priority = priority

start = time.time()
for word, tf, priority in autocomplete_vocab:
    insert(word, tf, priority)

print(f"Trie built in {(time.time() - start):.2f} sec")

# =========================
# SERIALIZE TRIE TO DISK
# =========================

def serialize(node):
    return {
        "w": node.word,
        "tf": node.tf,
        "p": node.priority,
        "c": {ch: serialize(child) for ch, child in node.children.items()}
    }

with open(OUTPUT_PATH, "wb") as f:
    f.write(msgpack.packb(serialize(root), use_bin_type=True))

print(f"Autocomplete trie saved at: {OUTPUT_PATH}")
