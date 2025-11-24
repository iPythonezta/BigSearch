import json
def assign_ids_to_words(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        words = f.readlines()

    id_map = {idx: word.strip() for idx, word in enumerate(words)}

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(id_map, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    assign_ids_to_words('..\\Lexicon\\final_words_lexicon.txt', '..\\Lexicon\\lexicons_ids.json')

