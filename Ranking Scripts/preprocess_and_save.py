import os
import re
from gensim.utils import simple_preprocess
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup
from tqdm import tqdm
import orjson

RAW_HTML_DIR = '..\\Data\\Files\\raw'
RAW_JSON_DIR = '..\\Data\\Cord 19\\document_parses\\pdf_json'
TOKEN_DIR = '..\\Data\\preprocessed_tokens'

os.makedirs(TOKEN_DIR, exist_ok=True)


def process_file(file_name):
    file_path = os.path.join('..\\Data', 'Files', 'raw', file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        text = BeautifulSoup(content, 'html.parser').get_text()
    return text


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


def preprocess_file(file):
    if file.endswith('.html'):
        text = process_file(file)
    else:
        text = extract_text_from_json(file)
    # clean text
    text = re.sub(r'[^a-z0-9\s]', '', text.lower())
    tokens = simple_preprocess(text)
    
    # save tokens to file
    token_file = os.path.join(TOKEN_DIR, f"{file}.tokens")
    with open(token_file, 'w', encoding='utf-8') as f:
        f.write(" ".join(tokens))
    return token_file


if __name__ == "__main__":
# Preprocess in parallel
    # Get all files
    html_files = [f for f in os.listdir(RAW_HTML_DIR) if f.endswith('.html')]
    json_files = [f for f in os.listdir(RAW_JSON_DIR) if f.endswith('.json')]
    all_files = html_files + json_files
    with Pool(cpu_count()) as p:
        for _ in tqdm(p.imap(preprocess_file, all_files), total=len(all_files), desc="Preprocessing files"):
            pass
