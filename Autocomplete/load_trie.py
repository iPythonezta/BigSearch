import msgpack

class TrieNode:
    __slots__ = ("children", "word", "tf")

    def __init__(self):
        self.children = {}
        self.word = None
        self.tf = 0

TRIE_PATH = "../Autocomplete/autocomplete_trie.msgpack"

def deserialize(data):
    node = TrieNode()
    node.word = data["w"]
    node.tf = data["t"]
    for ch, child in data["c"].items():
        node.children[ch] = deserialize(child)
    return node

with open(TRIE_PATH, "rb") as f:
    packed = msgpack.unpackb(f.read(), raw=False)

root = deserialize(packed)

print("Autocomplete trie loaded into memory")
