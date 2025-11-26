# This file contains code for converting our forward index into an inverted index.
"""
    The inverted index would be stored as a json file with the following structure:
    {
        "word_1_id" : [
            {
                "document_id" : "doc_1_id",
                "positions" : [pos_1, pos_2, ...],
                "hit_counter": [
                    int title_occurrences, // Number of times the word appears in the title
                    int meta_desc_occurrences, // Number of times the word appears in the meta description
                    int heading_occurrences, // Number of times the word appears in headings [h1-h6]
                    int total_occurrences, // Total number of times the word appears in the document
                    int href_occurrences, // Number of times the word appears in the href text when another document links to this document
                    bool in_domain, // Whether the word appears in the domain (1/0)
                    bool in_url, // Whether the word appears in the URL (1/0)
                    int doc_length // Length of the document
                ]
            }, ...
        ],
        "word_2_id" : [
            {
                "doc_id" : "doc_2_id",
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
        ], ...
    }
"""
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import pandas as pd
import json
import re

doc_id_to_url = {}
with open('..\\Data\\ind_to_url.json', 'r', encoding='utf-8') as f:
    doc_id_to_url = json.load(f)


def normalize_and_tokenize(text):
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'(?<!\d)[^\w\s]|[^\w\s](?!\d)', ' ', text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower().split(' ')

from collections import Counter, defaultdict
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

def process_file_for_word(args):
    file_path, words, anchors_used = args
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')  
    text = soup.get_text()
    tokens = normalize_and_tokenize(text)
    doc_length = len(tokens)
    
    tokens_counter = Counter(tokens)
    
    positions_map = defaultdict(list)
    for i, tok in enumerate(tokens):
        if len(positions_map[tok]) < 15:
            positions_map[tok].append(i)
    
    title_text = []
    if soup.title:
        title_text = normalize_and_tokenize(soup.title.text)
    title_counter = Counter(title_text)
    
    meta_desc_text = []
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag and 'content' in meta_tag.attrs:
        meta_desc_text = normalize_and_tokenize(meta_tag['content'])
    meta_counter = Counter(meta_desc_text)
    
    headings = []
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            headings.extend(normalize_and_tokenize(heading.text))
    headings_counter = Counter(headings)
    
    anchors_tokens = normalize_and_tokenize(anchors_used)
    anchors_counter = Counter(anchors_tokens)
    
    document_id = "H" + file_path.split('\\')[-1].split('.')[0]
    url = doc_id_to_url.get(document_id.replace("H", ""), "")
    url_path = urlparse(url).path
    domain = urlparse(url).netloc

    hit_lists = {}
    for word in words:
        hit_list = {}
        hit_list['document_id'] = document_id
        hit_list['positions'] = positions_map.get(word, [])
        hit_list['hit_counter'] = [
            title_counter[word],
            meta_counter[word],
            headings_counter[word],
            tokens_counter[word],
            anchors_counter[word],
            1 if word in domain else 0,
            1 if word in url_path else 0,
            doc_length
        ]
        hit_lists[word] = hit_list
    
    return hit_lists

def main():    
    lexicon = {}
    with open('..\\Lexicon\\lexicons_ids.json', 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
    
    inverse_lexicon = {v: k for k, v in lexicon.items()}

    forward_index_path = '..\\Forward Index\\forward_index_html_files.json'
    with open(forward_index_path, 'r', encoding='utf-8') as f:
        forward_index = json.load(f)
    
    # page_rank_links = pd.read_csv('..\\Data\\Page_rank_files\\url_to_anchor_text.csv')
    url_to_anchor = {}
    with open('..\\Data\\Page_rank_files\\url_to_anchor_text.json', 'r', encoding='utf-8') as f:
        url_to_anchor = json.load(f)
    print(f"Loaded Links Data")
    
    args = []

    
    def prepare_args(file_id):
        words = forward_index[file_id]
        words = [inverse_lexicon[word_id] for word_id in words]
        file_path = f"..\\Data\\Files\\raw\\{file_id}.html"
        anchors = url_to_anchor.get(doc_id_to_url.get(file_id, ""), "")
        return (file_path, words, anchors)

    file_ids_list = list(forward_index.keys())
    args = []

    for file_id in tqdm(file_ids_list, desc="Preparing arguments", unit="files", total=len(file_ids_list)):
        args.append(prepare_args(file_id))

    args = args

    del forward_index
    del url_to_anchor

    batch_size = 10000
    for i in range(0, len(args), batch_size):
        inverted_index = {}
        for word, word_id in lexicon.items(): 
            inverted_index[word_id] = []
        batch_args = args[i:i + batch_size]
        with Pool(processes=cpu_count()) as pool:
            results = list(tqdm(pool.imap(process_file_for_word, batch_args), 
                                total=len(batch_args), 
                                desc=f"Processing files {i+1} to {min(i+batch_size, len(args))}", 
                                unit="files"))
        
        for hit_lists in results:
            for word, hit_list in hit_lists.items():
                word_id = lexicon[word]
                inverted_index[word_id].append(hit_list)

        with open(f'..\\Inverted Index\\inverted_index_part_{i//batch_size + 1}.json', 'w', encoding='utf-8') as f:
            json.dump(inverted_index, f)
        
        del results
        del batch_args

    del args
    del lexicon


if __name__ == "__main__":
    main()