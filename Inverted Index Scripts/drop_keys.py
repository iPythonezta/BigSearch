"""
 We have a json file for the inverted index with the following format:
 [ 
    "word_1_id" : [
                {
                    "document_id" : "document_id",
                    "positions" : [pos_1, pos_2, ...],
                    "hit_counter": [
                        int title_occurrences,
                        int meta_desc_occurrences,
                        int heading_occurrences,
                        int total_occurrences,
                        int href_occurrences,
                        bool in_domain,
                        bool in_url,
                        int doc_length
                    ]
                }, ...
        ],..
 ]
 But as we can see the keys like document_id, positions and hit_counter are not needed for our use case.
 We can simply use an array to store these value like this
    [ 
        "word_1_id" : [
                    [
                        "document_id",
                        [pos_1, pos_2, ...],
                        [
                            int title_occurrences,
                            int meta_desc_occurrences,
                            int heading_occurrences,
                            int total_occurrences,
                            int href_occurrences,
                            bool in_domain,
                            bool in_url,
                            int doc_length
                        ]
                    ], ...
            ],..
    ]
    So this script will drop the keys from the inverted index json file and save the new format in a new json file.
    This will help in reducing the size of the inverted index json file and would also help in memory management.    
"""
import ijson
import json
from tqdm import tqdm

def drop_keys_to_list(input_file, output_file):
    with open(input_file, "rb") as f_in, open(output_file, "w", encoding="utf-8") as f_out:

        f_out.write("[")
        current_index = 0
        first = True

        for word_id_str, postings in tqdm(ijson.kvitems(f_in, ""), desc="Processing", total=1404321):
            word_id = int(word_id_str)

            if current_index < word_id:
                print(f"Error: Missing word_id {current_index}, it will ruin the structure of the inverted index.")
                break

            # new_postings = [
            #     [p["document_id"], p["positions"], p["hit_counter"]]
            #     for p in postings
            # ]

            new_postings = postings # Already in desired format for json

            if not first:
                f_out.write(",")
            first = False

            json.dump(new_postings, f_out)
            current_index = word_id + 1

        f_out.write("]")

if __name__ == "__main__":
    drop_keys_to_list(
        "../Inverted Index/JsonBatches/inverted_index_json.json",
        "../Inverted Index/JsonBatches/inverted_index_dropped_keys.json"
    )
