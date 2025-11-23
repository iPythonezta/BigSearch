import re
import json

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def remove_long_words(lex_words, lex_domains, max_len=20):
    to_delete = [w for w in lex_words if len(w) > max_len]
    for w in to_delete:
        lex_words.pop(w, None)
        lex_domains.pop(w, None)



def initial_filter(lex_words, lex_domains, final_set):
    keys = list(lex_words.keys())

    for word in keys:
        freq = lex_words[word]
        dcount = lex_domains.get(word, 0)

        if not word.isalnum():
            continue

        if (
            freq >= 50
            or (freq >= 5 and dcount >= 2)
            or (freq >= 3 and len(word) < 8)
        ):
            final_set.add(word)

        lex_words.pop(word, None)
        lex_domains.pop(word, None)


def cleanup_words(lex_words, lex_domains):
    keys = list(lex_words.keys())

    for word in keys:

        if word.startswith(("www", "http")):
            lex_words.pop(word, None)
            lex_domains.pop(word, None)
            continue

        if "(" in word or ")" in word:
            lex_words.pop(word, None)
            lex_domains.pop(word, None)
            continue

        if len(word) > 10:
            lex_words.pop(word, None)
            lex_domains.pop(word, None)
            continue

        if lex_domains.get(word, 0) <= 1:
            lex_words.pop(word, None)
            lex_domains.pop(word, None)
            continue


def add_remaining_words(lex_words, lex_domains, final_set):
    for word, freq in lex_words.items():
        dcount = lex_domains.get(word, 0)
        cleaned = re.sub(r",", "", word)

        if freq >= 10:
            final_set.add(cleaned)

        elif freq >= 5 and dcount >= 2:
            final_set.add(cleaned)



def save_lexicon(final_set, output_path, assign_id=True):
    if assign_id:
        word_to_id = {
            word: idx for idx, word in enumerate(sorted(final_set))
        }
        output_path = output_path + ".json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(word_to_id, f, ensure_ascii=False, indent=4)
    else:
        output_path = output_path + ".txt"
        with open(output_path, "w", encoding="utf-8") as f:
            for word in sorted(final_set):
                f.write(word + "\n")
        


def build_lexicon():
    lex_domains = load_json("lexicon_word_domains.json")
    lex_words = load_json("lexicon_words.json")
    final_set = set()

    remove_long_words(lex_words, lex_domains, max_len=20)
    initial_filter(lex_words, lex_domains, final_set)
    cleanup_words(lex_words, lex_domains)
    add_remaining_words(lex_words, lex_domains, final_set)
    save_lexicon(final_set, "final_lexicon", assign_id=False)


if __name__ == "__main__":
    build_lexicon()
