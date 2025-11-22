"""
    This file calculates the links between pages in the dataset.
    Page-to-page links are stored in page_rank_links.csv (from_url,to_url,anchor_text).
    Domain-to-domain links are stored in domain_rank_links.csv (from_domain,to_domain).
    Later used for PageRank and Domain Rank calculations.
"""

import os
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs, urlencode, urlunparse
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import csv

def clean_url(url):
    """Remove tracking params, strip fragments, and normalize the URL."""
    url, _ = urldefrag(url)
    parsed = urlparse(url)

    qs = parse_qs(parsed.query)
    blacklist = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term",
        "utm_content", "fbclid", "gclid", "ref", "referrer", "external_link"
    }
    qs = {k: v for k, v in qs.items() if k not in blacklist and not k.startswith('_')}
    clean_qs = urlencode(qs, doseq=True)

    return urlunparse(parsed._replace(query=clean_qs))

def extract_links_for_page(args):
    html_files_dir, page_id, base_url = args
    page_to_page_links = []
    domain_to_domain_links = []
    try:
        html_file = os.path.join(html_files_dir, f"{page_id}.html")
        if not os.path.exists(html_file):
            return page_to_page_links, domain_to_domain_links

        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, 'lxml')
    except Exception as e:
        with open(os.path.join(os.getcwd(), "logs", "htmL_file_processing_errors.log"), "a", encoding="utf-8") as log_file:
            log_file.write(f"Error processing {html_file}: {e}\n")
        return page_to_page_links, domain_to_domain_links

    try:
        base_url = clean_url(base_url)
        from_domain = urlparse(base_url).netloc
    except Exception as e:
        with open(os.path.join(os.getcwd(), "logs", "page_rank_link_parser_errors.log"), "a", encoding="utf-8") as log_file:
            log_file.write(f"Error cleaning base URL {base_url} for {html_file}: {e}\n")
        return page_to_page_links, domain_to_domain_links

    for a in soup.find_all('a'):
        try:
            href = a.get('href')
            if not href:
                continue
            href = urljoin(base_url, href)
            cleaned_href = clean_url(href)
        except Exception as e:
            with open(os.path.join(os.getcwd(), "logs", "page_rank_link_parser_errors.log"), "a", encoding="utf-8") as log_file:
                log_file.write(f"Error processing link in {html_file}: {e}\n")
            continue
        if cleaned_href == base_url:  
            continue

        page_to_page_links.append({
            "from_url": base_url,
            "to_url": cleaned_href,
            "anchor_text": a.get_text(strip=True)
        })

        to_domain = urlparse(cleaned_href).netloc
        if to_domain != from_domain:
            domain_to_domain_links.append({
                "from_domain": from_domain,
                "to_domain": to_domain
            })

    # Images need a lot of cleaning; skipping for now
    # for img in soup.find_all('img'):
    #     try:
    #         src = img.get('src')
    #         if not src:
    #             continue
    #         src = urljoin(base_url, src)
    #         cleaned_src = clean_url(src)
    #     except Exception as e:
    #         with open(os.path.join(os.getcwd(), "logs", "page_rank_link_parser_errors.log"), "a", encoding="utf-8") as log_file:
    #             log_file.write(f"Error processing image in {html_file}: {e}\n")
    #         continue
    #     if cleaned_src != base_url:
    #         page_to_page_links.append({
    #             "from_url": base_url,
    #             "to_url": cleaned_src,
    #             "anchor_text": img.get('alt', '')
    #         })
    #         if urlparse(cleaned_src).netloc != from_domain:
    #             domain_to_domain_links.append({
    #                 "from_domain": from_domain,
    #                 "to_domain": urlparse(cleaned_src).netloc
    #             })

    return page_to_page_links, domain_to_domain_links

def main():
    data_dir = os.path.join("..\\Data")
    html_files_dir = os.path.join(data_dir, "Files", "raw")
    page_rank_data_dir = os.path.join(data_dir, "Page_rank_files")
    os.makedirs(page_rank_data_dir, exist_ok=True)

    page_rank_csv = os.path.join(page_rank_data_dir, "page_rank_links.csv")
    domain_rank_csv = os.path.join(page_rank_data_dir, "domain_rank_links.csv")
    id_to_url_path = os.path.join(data_dir, "ind_to_url.json")

    with open(id_to_url_path, "r", encoding="utf-8") as f:
        id_to_url_map = json.load(f)

    page_ids = list(id_to_url_map.keys())

    pool_args = [(html_files_dir, pid, id_to_url_map[pid]) for pid in page_ids]
    page_links_all = []
    domain_links_all = []

    with Pool(processes=cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(extract_links_for_page, pool_args), total=len(pool_args)):
            page_links, domain_links = result
            page_links_all.extend(page_links)
            domain_links_all.extend(domain_links)

    with open(page_rank_csv, "w", newline="", encoding="utf-8") as pr_file:
        writer = csv.DictWriter(pr_file, fieldnames=["from_url", "to_url", "anchor_text"])
        writer.writeheader()
        writer.writerows(page_links_all)

    with open(domain_rank_csv, "w", newline="", encoding="utf-8") as dr_file:
        writer = csv.DictWriter(dr_file, fieldnames=["from_domain", "to_domain"])
        writer.writeheader()
        writer.writerows(domain_links_all)

    print(f"Page-to-page links saved to {page_rank_csv}")
    print(f"Domain-to-domain links saved to {domain_rank_csv}")

if __name__ == "__main__":
    main()
