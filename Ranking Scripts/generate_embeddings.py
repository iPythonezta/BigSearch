import orjson
from collections import Counter, defaultdict
import numpy as np
from gensim.models import KeyedVectors
import os
from bs4 import BeautifulSoup
import re
import random
from multiprocessing import Pool, cpu_count

from tqdm import tqdm


model =None
idf_map = None


def initiaize_worker():
    global model
    global idf_map
    idf_map  = {}
    with open('..\\Semantic Search Data\\idf_map.json', 'rb') as f:
        idf_map = orjson.loads(f.read())
    model = KeyedVectors.load_word2vec_format('glove.6B.50d.word2vec.txt', binary=False)
    


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

    return " ".join(texts)

def process_document(file_name):
    tokens = preprocess_text(process_file(file_name)) if file_name.endswith('.html') else preprocess_text(extract_text_from_json(file_name))
    term_counts = Counter(tokens)
    total_terms = sum(term_counts.values())

    tf_map = {
        term: count / total_terms
        for term, count in term_counts.items()
    }

    return file_name, tf_map

def doc_to_embedding(file_name):
    file_name, tf_map = process_document(file_name)
    vecs, weights = [], []
    for w, tf in tf_map.items():
        if w in model:
            tfidf = tf * idf_map.get(w, 0)
            vecs.append(model[w] * tfidf)
            weights.append(tfidf)
    if not vecs:
        return file_name, np.zeros(model.vector_size)
    return file_name, np.sum(vecs, axis=0) / np.sum(weights)



def main():
    corpus_html = os.listdir(os.path.join('..\\Data', 'Files', 'raw'))
    corpus_html.remove("sample")
    
    print(f"Html Embeddings Generation Started for {len(corpus_html)} files")
    html_embeddings = [None]*len(corpus_html)
    with Pool(3, initializer=initiaize_worker) as p:
        for file_name, embedding in tqdm(p.imap_unordered(doc_to_embedding, corpus_html), total=len(corpus_html)):
            id = int(file_name.split('.')[0])
            html_embeddings[id] = embedding.tolist()
    # convert html_embeddings to a list

    with open('..\\Semantic Search Data\\html_embeddings.json', 'wb') as f:
        f.write(orjson.dumps(html_embeddings))
    del html_embeddings

    corpus_json = os.listdir(os.path.join('..\\Data', 'Cord 19', 'document_parses\\pdf_json'))
    corpus_json.remove("sample")
    print(f"JSON Embeddings Generation Started for {len(corpus_json)} files")
    json_embeddings = [None]*len(corpus_json)
    with Pool(3, initializer=initiaize_worker) as p:
        for file_name, embedding in tqdm(p.imap_unordered(doc_to_embedding, corpus_json), total=len(corpus_json)):
            id = int(file_name.split('.')[0])
            json_embeddings[id] = embedding.tolist()
    with open('..\\Semantic Search Data\\json_embeddings.json', 'wb') as f:
        f.write(orjson.dumps(json_embeddings))
    del json_embeddings

if __name__ == "__main__":
    main()