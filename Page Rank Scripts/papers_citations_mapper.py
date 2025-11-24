import os
import json
import re
import string
import pandas as pd
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


def normalize_title(title):
    title = title.lower()
    title = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}|<.*?>', ' ', title)
    title = re.sub(r'[^a-z\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()



def process_one(args):
    idx, title, json_path = args
    refs = []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            paper = json.load(f)
    except Exception as e:
        print(f"[ERR] Failed loading {json_path}: {e}")
        return refs

    if paper.get("metadata", {}).get("title", "") == "":
        if "metadata" not in paper:
            paper["metadata"] = {}
        paper["metadata"]["title"] = title

    norm_parent = normalize_title(paper["metadata"]["title"])

    bib_entries = paper.get("bib_entries", {})
    for entry in bib_entries.values():
        if "title" in entry:
            refs.append((norm_parent, normalize_title(entry["title"])))

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(paper, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERR] Failed writing {json_path}: {e}")

    return refs


def build_reference_map_mp(metadata_cleaned, json_dir):

    jobs = []
    for idx, row in metadata_cleaned.iterrows():

        paper_id = row["id"]
        title = row["title"]
        json_path = os.path.join(json_dir, f"{paper_id}.json")

        if os.path.isfile(json_path):
            jobs.append((idx, title, json_path))


    print(f"Total JSON files to process: {len(jobs)}")

    all_refs = []
    with Pool(cpu_count()) as pool:
        for results in tqdm(
            pool.imap_unordered(process_one, jobs),
            total=len(jobs),
            desc="Processing JSON files",
        ):
            all_refs.extend(results)

    return all_refs

if __name__ == "__main__":
    metadata_cleaned = pd.read_csv("../Data/Cord 19/metadata_cleaned.csv")
    json_files_dir_path = "../Data/Cord 19/document_parses/pdf_json/"
    refs = build_reference_map_mp(
        metadata_cleaned,
        json_files_dir_path,
    )

    df = pd.DataFrame(refs, columns=["from_paper", "to_paper"])
    df.to_csv("../Data/PageRankCord19/references_map.csv", index=False)

    print("Done! Total mappings:", len(refs))
