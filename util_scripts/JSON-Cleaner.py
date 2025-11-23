This code Converts and removes the unwanted data from the JSON files and converts them into the desired schema.

import json
import re
import sys
import os


def extract_clean_title(text):
    """Return longest substring without comma or period."""
    parts = re.split(r"[.,]", text)
    return max(parts, key=len).strip() if parts else text


def process_single_file(input_json_path):
    """Converts one JSON file and writes formatted output."""

    output_json_path = os.path.join(
        os.path.dirname(input_json_path),
        "formatted_" + os.path.basename(input_json_path)
    )

    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("metadata", {})

    # NEW SCHEMA
    new_json = {
        "paper_id": data.get("paper_id", ""),
        "metadata": {
            "title": metadata.get("title", "")
        },
        "body_text": [],
        "bib_entries": {}
    }

    # PROCESS ABSTRACT
    abstract_blocks = metadata.get("abstract") or data.get("abstract") or []
    if abstract_blocks:
        new_json["body_text"].append({"text": "%Abstract%"})
        for block in abstract_blocks:
            text = block.get("text", "").strip()
            if text:
                new_json["body_text"].append({"text": text})


    # PROCESS BODY TEXT WITH SECTIONS
    body_blocks = metadata.get("body_text") or data.get("body_text") or []
    last_section = None
    for block in body_blocks:
        section = block.get("section", "").strip()
        text = block.get("text", "").strip()
        if not text:
            continue

        if section and section != last_section:
            new_json["body_text"].append({"text": f"%{section}%"})
            last_section = section

        new_json["body_text"].append({"text": text})


    # PROCESS BIB ENTRIES
    original_bib = metadata.get("bib_entries") or data.get("bib_entries") or {}
    for ref_id, ref_data in original_bib.items():
        raw_title = ref_data.get("title", "").strip()
        clean_title = extract_clean_title(raw_title) if raw_title else ""
        other_ids = ref_data.get("other_ids", {})

        new_json["bib_entries"][ref_id] = {
            "title": clean_title,
            "other_ids": other_ids
        }


    # SAVE NEW JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(new_json, f, indent=4)

    print(f"✔ Saved: {output_json_path}")

    # DELETE ORIGINAL FILE
    os.remove(input_json_path)
    print(f"🗑️ Deleted original: {input_json_path}")



def process_folder(folder_path):
    """Process all JSON files in the directory."""
    folder_path = os.path.abspath(folder_path)

    if not os.path.isdir(folder_path):
        print("❌ Error: Provided path is not a folder.")
        sys.exit(1)

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".json")]

    if not files:
        print("No .json files found in the folder.")
        return

    print(f"Found {len(files)} JSON files.\n")

    for filename in files:
        print(f"➡ Processing {filename} ...")
        full_path = os.path.join(folder_path, filename)
        process_single_file(full_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python JSON-Cleaner.py <folder_path>")
        sys.exit(1)

    process_folder(sys.argv[1])
