import re
from bs4 import BeautifulSoup
import os
from collections import Counter, defaultdict
import math
import orjson
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import random 

random.seed(67)

def process_file(file_name):
    file_path = os.path.join('..\\Data', 'Files', 'raw', file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        text = BeautifulSoup(content, 'html.parser').get_text()
    return text

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    tokens = text.split()
    return tokens

def extract_text_from_json(file_name):
    json_file_path = os.path.join('..\\Data', 'Cord 19', 'document_parses\\pdf_json', file_name)   
    def recurse(obj, texts):
        if isinstance(obj, dict):
            for value in obj.values():
                recurse(value, texts)
        elif isinstance(obj, list):
            for item in obj:
                recurse(item, texts)
        elif isinstance(obj, str):
            texts.append(obj)

    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = orjson.loads(f.read())

    texts = []
    recurse(data, texts)
    

    return " ".join(texts)

def process_document(file_name):
    tokens = preprocess_text(process_file(file_name)) if file_name.endswith('.html') else preprocess_text(extract_text_from_json(file_name))
    term_counts = Counter(tokens)
    total_terms = sum(term_counts.values())

    tf_map = {
        term: count / total_terms
        for term, count in term_counts.items()
    }

    return file_name, tf_map, set(term_counts.keys())

# def compute_tf_idf(files):
#     N = len(files)

#     tf_maps = {}
#     df_map = defaultdict(int)

#     for file_name in files:
#         tf_map, unique_terms = process_document(file_name)
#         tf_maps[file_name] = tf_map

#         for term in unique_terms:
#             df_map[term] += 1

#     idf_map = {
#         term: math.log((N+1) / (df + 1)) + 1
#         for term, df in df_map.items()
#     }

#     tf_idf_maps = {}

#     for file_name, tf_map in tf_maps.items():
#         tf_idf_maps[file_name] = {
#             term: tf * idf_map.get(term, 0.0)
#             for term, tf in tf_map.items()
#         }

#     with open("../Semantic Search Data/tf_idf_maps.json", "wb") as f:
#         f.write(orjson.dumps(tf_idf_maps))

#     return tf_idf_maps


def compute_tf_idf_in_paralell(corpus):
    N = len(corpus)
    tf_maps = {}
    df_map = defaultdict(int)

    with Pool(cpu_count()) as pool:
        for filename, tf_map, unique_terms in tqdm(pool.imap_unordered(process_document, corpus), total=N):
            tf_maps[filename] = tf_map

            for term in unique_terms:
                df_map[term] += 1
        
    idf_map = {
        term: math.log((N+1) / (df + 1)) + 1
        for term, df in df_map.items()
    }

    tf_idf_maps = {}
    for file_name, tf_map in tf_maps.items():
        tf_idf_maps[file_name] = {
            term: tf * idf_map.get(term, 0.0)
            for term, tf in tf_map.items()
        }
    os.makedirs("../Semantic Search Data", exist_ok=True)
    with open("../Semantic Search Data/tf_idf_maps.json", "wb") as f:
        f.write(orjson.dumps(tf_idf_maps))
    
    with open("../Semantic Search Data/idf_map.json", "wb") as f:
        f.write(orjson.dumps(idf_map))
    
    with open("../Semantic Search Data/tf_maps.json", "wb") as f:
        f.write(orjson.dumps(tf_maps))
        


def main():
    corpus_html = os.listdir(os.path.join('..\\Data', 'Files', 'raw'))
    corpus_html.remove("sample")
    corpus_json = os.listdir(os.path.join('..\\Data', 'Cord 19', 'document_parses\\pdf_json'))
    corpus_json.remove("sample")
    corpus = corpus_html + corpus_json
    random.shuffle(corpus)
    compute_tf_idf_in_paralell(corpus)

if __name__ == "__main__":
    main()