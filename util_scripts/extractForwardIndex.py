import json
from itertools import islice

INPUT_FILE = "Data/Forward Index/forward_index_html_files.json" # change to  forward_index_pdf_files.json for PDF files
OUTPUT_FILE = "Data/SampleOutputs/ForwardIndexPDFs[1-100].json" #change to ForwardIndexHTMLs[1-100].json for HTML files

def copy_first_100():
    # Load the original forward index
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    # Take the first 100 docIDs in the SAME ORDER as in the file
    first_100_items = dict(islice(data.items(), 100))

    # Write these to a new file
    with open(OUTPUT_FILE, "w") as out:
        json.dump(first_100_items, out, indent=2)

    print(f"Saved first {len(first_100_items)} postings into {OUTPUT_FILE}")


if __name__ == "__main__":
    copy_first_100()
