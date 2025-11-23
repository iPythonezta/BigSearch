import os
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
from urllib.parse import urlparse
import re 
from tqdm import tqdm
import json

def process_file(data):
    file_path, domain = data
    alphanum = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    soup = BeautifulSoup(file_content, 'html.parser')
    text = re.sub(r'\n', ' ', soup.get_text())
    text = re.sub(r'(?<!\d)[^\w\s]|[^\w\s](?!\d)', ' ', text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.lower()
    tokens = text.split(' ')
    for word in tokens:
        alphanum[word] = alphanum.get(word, 0) + 1
    
    return alphanum, domain

def main():
    data_dir = os.path.join("..", "Data", "Files\\raw")
    file_id_to_url_map = {}
    with open(os.path.join("..", "Data", "ind_to_url.json"), 'r', encoding='utf-8') as f:
        file_id_to_url_map = json.load(f)


    files = [(os.path.join(data_dir, f), urlparse(file_id_to_url_map.get(f.split('.')[0])).netloc) for f in os.listdir(data_dir) if f.endswith('.html')]
    
    all_alphanum = {}
    domain_to_words = {}
    all_uniq_domain = {}
    with Pool(cpu_count()) as pool:

        for alphanum, domain in tqdm(pool.imap_unordered(process_file, files), total=len(files)):
            if domain not in domain_to_words:
                domain_to_words[domain] = set()
            for key, value in alphanum.items():
                all_alphanum[key] = all_alphanum.get(key, 0) + value
                if key not in domain_to_words[domain]:
                    domain_to_words[domain].add(key)
                    all_uniq_domain[key] = all_uniq_domain.get(key, 0) + 1


    with open('lexicon_words.json', 'w', encoding='utf-8') as f:
        json.dump(all_alphanum, f, ensure_ascii=False, indent=4)
    
    with open('lexicon_word_domains.json', 'w', encoding='utf-8') as f:
        json.dump(all_uniq_domain, f, ensure_ascii=False, indent=4)

    print(f"Total unique tokens: {len(all_alphanum)}")

if __name__ == "__main__":
    main()