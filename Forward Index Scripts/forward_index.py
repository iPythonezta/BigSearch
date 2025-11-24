import os
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import re
import json

def init_worker(index_to_url_arg, lexicon_arg):
    # Initializes our global variables for each worker process
    # Helps us avoid passing large data structures repeatedly
    global index_to_url
    global lexicon
    index_to_url = index_to_url_arg
    lexicon = lexicon_arg

def process_file(file_path):
    global index_to_url
    global lexicon
    url = index_to_url[os.path.basename(file_path).split('.')[0]]
    url_tokens = set(re.findall(r'\w+', url.lower()))
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    soup = BeautifulSoup(file_content, 'html.parser')
    text = re.sub(r'\n', ' ', soup.get_text())
    text = re.sub(r'(?<!\d)[^\w\s]|[^\w\s](?!\d)', ' ', text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lower()
    tokens = text.split(' ')
    words = set()
    for word in tokens:
        word = re.sub(r",", "", word)
        if word in lexicon:
            words.add(lexicon[word])
    
    for word in url_tokens:
        if word == 'www' or word == 'http' or word == 'https':
            continue
        
        if word in lexicon:
            words.add(lexicon[word])
    
    return words, file_path

def main():
    html_files_path = "../Data/Files/raw/"
    ind_to_url_path = "../Data/ind_to_url.json"
    lexicon_path = "../Lexicon/lexicons_ids.json"

    with open(ind_to_url_path, 'r', encoding='utf-8') as f:
        index_to_url = json.load(f)

    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    forward_index = {}
    html_files = [os.path.join(html_files_path, f) for f in os.listdir(html_files_path) if f.endswith('.html')]
    with Pool(cpu_count(), initializer=init_worker, initargs=(index_to_url, lexicon)) as pool:
        for words, file_path in tqdm(pool.imap_unordered(process_file, html_files), total=len(html_files)):
            file_id = os.path.basename(file_path).split('.')[0]
            forward_index[file_id] = list(words)

    with open("../Forward Index/forward_index_html_files.json", 'w', encoding='utf-8') as f:
        json.dump(forward_index, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()