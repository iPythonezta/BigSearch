# DSA Search Engine — Milestone Report

**Project Name:** BigSearch  
**Course:** Data Structures and Algorithms  
**Semester:** Fall 2025  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
   - [1.1 Introduction](#11-introduction)
   - [1.2 Project Structure](#12-project-structure)
   - [1.3 Datasets](#13-datasets)
   - [1.4 Pipeline Architecture](#14-pipeline-architecture)
2. [Lexicon Construction](#2-lexicon-construction)
   - [2.1 Tokenization](#21-tokenization)
   - [2.2 Normalization](#22-normalization)
   - [2.3 Filtering and Stopword Handling](#23-filtering-and-stopword-handling)
   - [2.4 Lexicon Merging](#24-lexicon-merging)
   - [2.5 Term ID Assignment](#25-term-id-assignment)
3. [Forward Index](#3-forward-index)
   - [3.1 Data Structures](#31-data-structures)
   - [3.2 Algorithm](#32-algorithm)
   - [3.3 Implementation Details](#33-implementation-details)
   - [3.4 Sample Output](#34-sample-output)
   - [3.5 Final Forward Index Merger](#35-final-forward-index-merger)
   - [3.6 Workflow Summary](#36-workflow-summary)
4. [Inverted Index](#4-inverted-index)
   - [4.1 Data Structures](#41-data-structures)
   - [4.2 Algorithm](#42-algorithm)
   - [4.3 Hit List Structure](#43-hit-list-structure)
   - [4.4 Memory Optimization Iterations](#44-memory-optimization-iterations)
5. [Sample Outputs](#5-sample-outputs)
6. [What's Working & Future Improvements](#6-whats-working--future-improvements)
   - [6.1 Current Working Functionality](#61-current-working-functionality)
   - [6.2 Limitations](#62-limitations)
   - [6.3 Future Improvements](#63-future-improvements)

---

## 1. Project Overview

### 1.1 Introduction

BigSearch is a comprehensive search engine developed as part of the Data Structures and Algorithms course. The project implements a full-text search system capable of indexing and querying two distinct types of document collections:

1. **Web Pages (HTML files)** — crawled from various technology-focused websites
2. **Research Papers (PDF/JSON files)** — sourced from the CORD-19 dataset containing scientific literature

The search engine implements industry-standard information retrieval techniques including lexicon construction, forward indexing, inverted indexing, and PageRank-based relevance scoring.

### 1.2 Project Structure

The project follows a modular directory structure to separate concerns:

```
BigSearch/
├── Data/                           # Raw data and mappings
│   ├── Files/raw/                  # HTML files from web crawling
│   ├── Cord 19/                    # Research paper dataset
│   │   ├── metadata.csv            # Paper metadata
│   │   ├── metadata_cleaned.csv    # Paper metadata (cleaned to leave required 
│   │   │                           # columns and remove docs with nonexistent urls)
│   │   └── document_parses/        # Parsed JSON documents
│   ├── Page_rank_files/            # PageRank computation data
│   ├── ind_to_url.json             # Document ID to URL mapping
│   └── url_map.json                # URL encodings (simhash/crawling)
│
├── Lexicon/                        # Generated lexicon files
│   ├── lexicons_ids.json           # Final merged lexicon with term IDs
│   ├── final_lexicon.txt           # HTML lexicon (text format)
│   └── words.txt                   # Research paper lexicon
│
├── Forward Index/                  # Forward index outputs
│   ├── forward_index_html_files.json
│   └── forward_index_pdf_files.json
│
├── Inverted Index/                 # Inverted index outputs
│   ├── inverted_index.json         # Raw inverted index (HTML)
│   ├── inverted_index_dropped_keys.json  # Cleaned version with keys dropped
│   └── JsonBatches/                # Inverted index batches (Research papers)
│        └── inverted_index_dropped_keys.json  # Research papers inverted index
│
├── Page Rank Results/              # PageRank computation results
│   ├── page_rank_results_with_urls.csv
│   ├── domain_rank_results_with_domain_nm.csv
│   └── citation_rank_output.csv
│
├── Lexicon scripts/                # Lexicon generation code
├── Forward Index Scripts/          # Forward index generation code
├── Inverted Index Scripts/         # Inverted index generation code
├── Page Rank Scripts/              # PageRank algorithm implementation
└── Notebooks/                      # Jupyter notebooks for exploration
```

### 1.3 Datasets

#### Dataset 1: Web Pages (HTML Files)

| Property | Details |
|----------|---------|
| **Source** | Technology websites (edX, NPR, BBC, GeeksforGeeks, Coursera, etc.) using our own crawler |
| **Format** | HTML files |
| **Count** | ~48,000 documents |
| **Storage** | `Data/Files/raw/` directory |
| **ID Prefix** | `H` (e.g., `H0`, `H123`) |

**Sample URL Mapping:**
```json
{
  "0": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s...",
  "1": "https://www.npr.org/sections/technology/",
  "2": "https://www.theverge.com/tech",
  "3": "https://www.geeksforgeeks.org/questions/..."
}
```

> **Note:** The numbers like 0, 1 and 2 in the URL mapping refer to the files `0.html`, `1.html`, `2.html`, etc. respectively.

#### Dataset 2: Research Papers (CORD-19)

| Property | Details |
|----------|---------|
| **Source** | COVID-19 Open Research Dataset (CORD-19) |
| **Format** | JSON files with structured paper content |
| **Content** | Scientific papers with metadata, abstracts, body text, bibliographic entries, and other info |
| **Storage** | `Data/Cord 19/document_parses/` directory |
| **ID Prefix** | `P` (e.g., `P0`, `P1`, `P29876`) |

> **Note:** The file names were SHA-256 hashes by default, which we replaced with numeric IDs for efficiency.

The CORD-19 dataset provides structured JSON files containing:
- Paper metadata (title, authors)
- Abstract sections
- Body text paragraphs
- Bibliographic entries (references)
- Reference entries (figures, tables)

### 1.4 Pipeline Architecture

The indexing pipeline processes both datasets through the following stages:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
├─────────────────────────────┬───────────────────────────────────────┤
│      HTML Web Pages         │        CORD-19 Research Papers        │
│    (Data/Files/raw/)        │    (Data/Cord 19/document_parses/)    │
└─────────────┬───────────────┴───────────────────┬───────────────────┘
              │                                   │
              ▼                                   ▼
┌─────────────────────────────┐   ┌───────────────────────────────────┐
│   HTML Lexicon Generator    │   │    JSON/PDF Lexicon Generator     │
│    (lexicon_gen.py)         │   │      (jsonParser.cpp)             │
└─────────────┬───────────────┘   └───────────────────┬───────────────┘
              │                                       │
              └───────────────┬───────────────────────┘
                              ▼
              ┌───────────────────────────────┐
              │      Lexicon Merger           │
              │    (merge_lexicons.py)        │
              │     + ID Assignment           │
              │    (assign_ids.py)            │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │     Final Unified Lexicon     │
              │    (lexicons_ids.json)        │
              │      ~1.4 million terms       │
              └───────────────┬───────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   HTML Forward Index    │       │   PDF Forward Index     │
│   (forward_index.py)    │       │   (forwardIndex.cpp)    │
└───────────┬─────────────┘       └───────────┬─────────────┘
            │                                 │
            ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   HTML Inverted Index   │       │   PDF Inverted Index    │
│   (inverted_index.py)   │       │  (JSONinvertedIndex.py) │
└───────────┬─────────────┘       └───────────┬─────────────┘
            │                                 │
            └───────────────┬─────────────────┘
                            ▼
              ┌───────────────────────────────┐
              │    Merged Inverted Index      │
              │   (Barrel-based storage)      │
              └───────────────────────────────┘
```

**Why Separate Processing?**

The two datasets are processed separately before merging for several critical reasons:

1. **Structural Differences**: HTML files have DOM structure (title tags, meta descriptions, headings), while research papers have academic structure (abstract, body text, bibliography).

2. **Metadata Extraction**: Different hit counters are computed:
   - HTML: title, meta description, headings (h1-h6), anchor text
   - PDF: title, author/abstract, body text, bibliographic entries, and other sections

3. **Scoring Algorithms**: Web pages use PageRank + anchor text analysis, while research papers use citation rank.

4. **Memory Management**: Processing datasets separately allows efficient batch processing without exceeding system memory limits.

5. **Task Division**: Processing the 2 datasets separately allowed for better task division between our team members.

---

## 2. Lexicon Construction

The lexicon serves as the vocabulary mapping between human-readable terms and their integer identifiers (term IDs). This mapping is essential for efficient storage and fast lookup during indexing and querying.

### 2.1 Tokenization

Tokenization converts raw document text into discrete tokens (words). Our implementation uses a consistent approach across both datasets.

**Tokenization Algorithm (for HTML files):**

```python
def normalize_and_tokenize(text):
    # Step 1: Replace newlines with spaces
    text = re.sub(r'\n', ' ', text)
    
    # Step 2: Remove punctuation except when surrounded by digits
    # This preserves numbers like "3.14" or "2-3" but removes punctuation
    text = re.sub(r'(?<!\d)[^\w\s]|[^\w\s](?!\d)', ' ', text)
    
    # Step 3: Collapse multiple whitespaces into single space
    text = re.sub(r"\s+", " ", text).strip()
    
    # Step 4: Convert to lowercase and split
    return text.lower().split(' ')
```

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Preserve numbers with decimals/hyphens | Important for technical content (e.g., "COVID-19", "0.05") |
| Lowercase conversion | Enables case-insensitive matching |
| Whitespace normalization | Ensures consistent token boundaries |

### 2.2 Normalization

Both pipelines preserve UTF-8 characters to retain scientific symbols, accented names, and non-English terms.
Text normalization ensures consistent representation of terms across all documents.

**Normalization Steps:**

1. **Case Folding**: All text converted to lowercase
2. **Punctuation Handling**:
   - Remove standalone punctuation
   - Preserve punctuation within numeric sequences
3. **Whitespace Normalization**: Multiple spaces collapsed to single space
4. **Unicode Handling**: UTF-8 encoding preserved for international characters

**For HTML Documents:**
```python
soup = BeautifulSoup(file_content, 'html.parser')
text = soup.get_text()  # Extract visible text only
tokens = normalize_and_tokenize(text)
```

**For Research Papers (C++ Implementation):**
```cpp
void extractWords(const string &text, unordered_set<string> &wordsSet) {
    string word;
    for (unsigned char c : text) {
        if (isalnum(c) || c >= 128) {  // Include unicode chars
            word.push_back(tolower(c));
        } else {
            if (!word.empty()) {
                wordsSet.insert(word);
                word.clear();
            }
        }
    }
}
```

### 2.3 Filtering and Stopword Handling

Rather than using a static stopword list, we employ a frequency-based filtering approach that adapts to the corpus.

**Filtering Criteria:**

```python
def initial_filter(lex_words, lex_domains, final_set):
    for word in keys:
        freq = lex_words[word]           # Total frequency
        dcount = lex_domains.get(word, 0)  # Domain count
        
        # Inclusion rules:
        if not word.isalnum():
            continue  # Skip non-alphanumeric
            
        if (
            freq >= 50  # High frequency terms
            or (freq >= 5 and dcount >= 2)  # Medium freq, multi-domain
            or (freq >= 3 and len(word) < 8)  # Low freq short words
        ):
            final_set.add(word)
```

**Additional Cleanup Rules:**

| Rule | Purpose |
|------|---------|
| Remove words starting with `www`, `http` | Filter URL fragments |
| Remove words containing parentheses | Filter code artifacts |
| Remove words > 20 characters | Filter concatenated tokens |
| Require appearance in ≥ 2 domains | Ensure term significance |

### 2.4 Lexicon Merging

The final lexicon is created by merging vocabulary from both datasets:

```python
def main():
    # Load both lexicons
    with open(json_files_lexicon, 'r', encoding='utf-8') as f:
        json_words = f.readlines()  # Research paper terms
    
    with open(html_files_lexicon, 'r', encoding='utf-8') as f:
        html_words = f.readlines()  # Web page terms
    
    # Merge using set union (automatic deduplication)
    final = set()
    final.update(json_words)
    final.update(html_words)
    
    # Write sorted final lexicon
    with open("final_words_lexicon.txt", 'w', encoding='utf-8') as f:
        f.writelines(sorted(final))
```

**Merging Strategy:**
- Use Python `set` for automatic deduplication
- Sort terms alphabetically for consistent ID assignment
- No stemming/lemmatization applied (preserves exact word forms)

### 2.5 Term ID Assignment

Each unique term receives a sequential integer ID:

```python
def save_lexicon(final_set, output_path, assign_id=True):
    if assign_id:
        word_to_id = {
            word: idx for idx, word in enumerate(sorted(final_set))
        }
        with open(output_path + ".json", "w", encoding="utf-8") as f:
            json.dump(word_to_id, f, ensure_ascii=False, indent=4)
```

**Final Lexicon Statistics:**

| Metric | Value |
|--------|-------|
| Total unique terms | ~1,404,321 |
| Storage format | JSON dictionary |
| ID range | 0 to 1,404,320 |

---

## 3. Forward Index

The forward index maps each document to the list of terms it contains. This structure is essential for efficient inverted index construction.

### 3.1 Data Structures

**Primary Structure:**
```
Forward Index = {
    document_id: [term_id_1, term_id_2, ..., term_id_n]
}
```

| Component | Type | Description |
|-----------|------|-------------|
| `document_id` | String | Unique document identifier (e.g., "0", "1", "123") |
| `term_ids` | List[int] | Array of term IDs present in document |

### 3.2 Algorithm

The forward index construction follows these steps:

```
1. LOAD lexicon mapping (word → term_id)
2. LOAD document-to-URL mapping
3. FOR each document in corpus:
   a. Parse document content
   b. Extract and tokenize text
   c. Map tokens to term IDs using lexicon
   d. Store document_id → [term_ids] mapping
4. SAVE forward index to JSON file
```

### 3.3 Implementation Details

**For HTML Files (Python with Multiprocessing):**

```python
def process_file(file_path):
    global index_to_url, lexicon
    
    # Get URL for additional token extraction
    url = index_to_url[os.path.basename(file_path).split('.')[0]]
    url_tokens = set(re.findall(r'\w+', url.lower()))
    
    # Parse HTML content
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    soup = BeautifulSoup(file_content, 'html.parser')
    
    # Tokenize and normalize
    text = soup.get_text()
    tokens = normalize_and_tokenize(text)
    
    # Map to term IDs
    words = set()
    for word in tokens:
        if word in lexicon:
            words.add(lexicon[word])
    
    # Include URL tokens
    for word in url_tokens:
        if word in lexicon:
            words.add(lexicon[word])
    
    return words, file_path

# Parallel processing
with Pool(cpu_count(), initializer=init_worker,
          initargs=(index_to_url, lexicon)) as pool:
    for words, file_path in pool.imap_unordered(process_file, html_files):
        file_id = os.path.basename(file_path).split('.')[0]
        forward_index[file_id] = list(words)
```

**For Research Papers (C++ for Performance):**

```cpp
unordered_set<string> parseJsonFile(const fs::path &path) {
    unordered_set<string> words;
    json j;
    ifstream(path) >> j;
    
    // Extract from all relevant JSON fields
    if (j.contains("metadata") && j["metadata"].contains("title"))
        extractWords(j["metadata"]["title"].get<string>(), words);
    
    if (j.contains("abstract"))
        for (auto &obj : j["abstract"])
            extractWords(obj["text"].get<string>(), words);
    
    if (j.contains("body_text"))
        for (auto &obj : j["body_text"])
            extractWords(obj["text"].get<string>(), words);
    
    // ... additional sections
    return words;
}
```

**Key Implementation Features:**

*Python implementation for HTML files:*

| Feature | Purpose |
|---------|---------|
| Multiprocessing (Python) | Parallel document processing |
| Worker initialization | Avoid repeated data serialization |
| URL token inclusion | Capture domain/path keywords |

*C++ implementation for Research Papers:*

| Feature | Purpose |
|---------|---------|
| Character-level tokenization | Fast extraction without regex overhead |
| Unicode-safe parsing | Preserves scientific + non-ASCII terms |
| Full JSON field coverage | Extracts title, authors, abstract, body, refs, back-matter |
| Set-based word collection | Ensures each term is counted once per document |
| Lexicon lookup via hash map | Constant-time word→ID resolution |
| Batch-wise index writing | Prevents RAM overflow on large corpora |
| Deterministic file ordering | Output consistent across runs |
| Exception-safe JSON parsing | Skips corrupt documents cleanly |

### 3.4 Sample Output

**Sample Forward Index Structure:**

```json
{
  "0": [189543, 195108, 397621, 641823, 1023456, 1056789, 1122667, 1178934],
  "1": [195108, 261923, 721456, 811234, 1201567, 1225317, 1356789],
  "2": [361087, 397621, 576791, 653421, 811234, 1023456, 1122667],
  "3": [189543, 261923, 361087, 1056789, 1178934, 1201567],
  "4": [195108, 576791, 641823, 721456, 1225317, 1356789],
  "5": [397621, 653421, 811234, 1023456, 1122667, 1178934]
}
```

**Interpretation:**
- Document `"0"` contains terms with IDs: 189543, 195108, 397621, etc.
- Each term ID maps back to a word via the lexicon (e.g., 195108 → "and")

### 3.5 Final Forward Index Merger

**Purpose:**
Combines all batch-level forward index files into one globally sorted JSON index.

**Key Features:**

| Feature | Purpose |
|---------|---------|
| Sorted std::map storage | Ensures docIDs stored in increasing order |
| Batch auto-discovery | Loads every `forward_index_batch_*.json` file |
| Low-memory merging | Processes batches one by one and frees memory |
| JSON array → object conversion | Produces consistent final lookup format |
| Stable final output | Guarantees deterministic ordering for later search stages |

### 3.6 Workflow Summary

1. Scan the forward-index folder for all batch JSON files
2. Load each batch and insert entries into a sorted map
3. Transform sorted results into a final JSON object
4. Write `forward_index_json.json` as the unified index

---

## 4. Inverted Index

The inverted index is the core data structure enabling efficient full-text search. It maps each term to the list of documents containing that term, along with detailed hit information for relevance scoring.

### 4.1 Data Structures

**Conceptual Structure:**
```
Inverted Index = {
    term_id: [
        (document_id, positions, hit_counter),
        (document_id, positions, hit_counter),
        ...
    ]
}
```

**Hit Counter Array (HTML Documents):**
```
hit_counter = [
    title_occurrences,      # Index 0: Count in <title> tag
    meta_desc_occurrences,  # Index 1: Count in meta description
    heading_occurrences,    # Index 2: Count in h1-h6 tags
    total_occurrences,      # Index 3: Total count in document
    href_occurrences,       # Index 4: Count in anchor text from linking pages
    in_domain,              # Index 5: 1 if term in domain, 0 otherwise
    in_url,                 # Index 6: 1 if term in URL path, 0 otherwise
    doc_length              # Index 7: Total tokens in document
]
```

**Hit Counter Array (Research Papers):**
```
hit_counter = [
    title_author_abstract_count,  # Index 0: Count in title/author/abstract
    body_text_count,              # Index 1: Count in body paragraphs
    other_section_count,          # Index 2: Count in other sections
    total_count,                  # Index 3: Total occurrences
    doc_length                    # Index 4: Document length
]
```

### 4.2 Algorithm

**Inverted Index Construction:**

```
1. LOAD lexicon and forward index
2. LOAD anchor text mappings (for HTML)
3. INITIALIZE inverted_index = {term_id: [] for all terms}
4. FOR each (document_id, term_ids) in forward_index:
   a. Parse original document
   b. FOR each term in term_ids:
      - Compute positions (up to 15)
      - Compute hit_counter metrics
      - APPEND (doc_id, positions, hit_counter) to inverted_index[term_id]
5. SAVE inverted index to JSON
```

### 4.3 Hit List Structure

The hit list captures where and how frequently a term appears in a document.

#### HTML Files Implementation

```python
def process_file_for_word(args):
    file_path, words, anchors_used = args
    
    # Parse document
    soup = BeautifulSoup(html, 'lxml')
    tokens = normalize_and_tokenize(soup.get_text())
    
    # Build position map (max 15 positions per term)
    positions_map = defaultdict(list)
    for i, tok in enumerate(tokens):
        if len(positions_map[tok]) < 15:
            positions_map[tok].append(i)
    
    # Count occurrences in special sections
    title_counter = Counter(normalize_and_tokenize(soup.title.text))
    meta_counter = Counter(meta_description_tokens)
    headings_counter = Counter(heading_tokens)
    anchors_counter = Counter(normalize_and_tokenize(anchors_used))
    
    # Build hit list for each word
    for word in words:
        hit_list = {
            'document_id': "H" + file_id,
            'positions': positions_map.get(word, []),
            'hit_counter': [
                title_counter[word],
                meta_counter[word],
                headings_counter[word],
                tokens_counter[word],
                anchors_counter[word],
                1 if word in domain else 0,
                1 if word in url_path else 0,
                len(tokens)
            ]
        }
```

#### Research Papers Implementation

For research papers, we extract tokens from multiple document sections and group them for hit counting:

```python
# ----- TITLE -----
title = doc.get("metadata", {}).get("title", "")
for tok in normalize_and_tokenize(title):
    if len(positions_map[tok]) < MAX_POS:
        positions_map[tok].append(pos)
    group1[tok] += 1
    pos += 1

# ----- ABSTRACT -----
for item in doc.get("abstract", []):
    for tok in normalize_and_tokenize(item.get("text", "")):
        if len(positions_map[tok]) < MAX_POS:
            positions_map[tok].append(pos)
        group1[tok] += 1
        pos += 1

# ----- AUTHORS -----
# Handle both string and dictionary author entries
for author in doc.get("metadata", {}).get("authors", []):
    if isinstance(author, str):
        for tok in normalize_and_tokenize(author):
            if len(positions_map[tok]) < MAX_POS:
                positions_map[tok].append(pos)
            group1[tok] += 1
            pos += 1
    elif isinstance(author, dict):
        # Extract all string fields from author object
        for key, value in author.items():
            if isinstance(value, str):
                for tok in normalize_and_tokenize(value):
                    if len(positions_map[tok]) < MAX_POS:
                        positions_map[tok].append(pos)
                    group1[tok] += 1
                    pos += 1

# ----- BODY TEXT -----
for item in doc.get("body_text", []):
    for tok in normalize_and_tokenize(item.get("text", "")):
        if len(positions_map[tok]) < MAX_POS:
            positions_map[tok].append(pos)
        group2[tok] += 1
        pos += 1

# ----- BIB ENTRIES, REF ENTRIES, BACK MATTER -----
# (Similar pattern for group3 - references and supplementary content)

# ------------------ BUILD HITLISTS ------------------
hitlists = {}
for word in words:
    g1, g2, g3 = group1[word], group2[word], group3[word]
    total = g1 + g2 + g3

    if total == 0:
        continue  # Skip words not in document

    hitlists[word] = [
        docid,
        positions_map[word],
        [g1, g2, g3, total, pos]  # [title+abstract+authors, body, refs, total, doc_length]
    ]

return hitlists
```

#### Tokenization Consistency

PDF/JSON tokens must match the lexicon extracted via C++ to ensure correct term ID lookups:

```python
def normalize_and_tokenize(text):
    """C++-compatible tokenization: alphanumeric or unicode"""
    tokens = []
    word = []
    for c in text:
        if c.isalnum() or ord(c) >= 128:  # Matches C++: isalnum(c) || c >= 128
            word.append(c.lower())
        else:
            if word:
                tokens.append(''.join(word))
                word = []
    if word:
        tokens.append(''.join(word))
    return tokens
```

#### Hit Counter Grouping

| Group | Contents | Purpose |
|-------|----------|---------|
| **G1** | Title, abstract, authors | High-relevance metadata |
| **G2** | Body text | Main content |
| **G3** | Bib entries, ref entries, back matter | Supporting references |

**Position Limiting Rationale:**
- Storing all positions would explode storage requirements
- First 15 positions are sufficient for proximity scoring
- Reduces memory footprint by ~90% for high-frequency terms

### 4.4 Memory Optimization Iterations

Developing the inverted index required multiple optimization iterations to handle the large corpus within memory constraints.

#### Iteration 1: Naive Implementation

**Problem:** Loading entire forward index + computing full inverted index crashed due to memory exhaustion.

```python
# Initial approach - caused memory overflow
inverted_index = {}
for term_id in lexicon.values():
    inverted_index[term_id] = []

for doc_id, terms in forward_index.items():
    # Process each document...
```

**Memory Usage:** >32 GB (exceeded available RAM)

#### Iteration 2: Batch Processing

**Solution:** Process documents in batches of 10,000, writing partial results to disk.

```python
batch_size = 10000
for i in range(0, len(args), batch_size):
    inverted_index = {word_id: [] for word_id in lexicon.values()}
    batch_args = args[i:i + batch_size]
   
    # Process batch
    with Pool(processes=cpu_count()) as pool:
        results = list(pool.imap(process_file_for_word, batch_args))
   
    # Save batch result
    with open(f'inverted_index_part_{i//batch_size + 1}.json', 'w') as f:
        json.dump(inverted_index, f)
   
    # Clear memory
    del results, batch_args
```

**Memory Usage:** ~8 GB peak per batch

#### Iteration 3: Key Dropping Optimization

**Problem:** JSON structure with named keys consumed excessive storage.

**Before (with keys):**
```json
{
  "term_id": [
    {
      "document_id": "H0",
      "positions": [12, 45, 89],
      "hit_counter": [2, 0, 1, 5, 0, 1, 0, 1245]
    }
  ]
}
```

**After (array format):**
```json
[
  [
    ["H0", [12, 45, 89], [2, 0, 1, 5, 0, 1, 0, 1245]]
  ]
]
```

**Implementation:**
```python
def drop_keys_to_list(input_file, output_file):
    with open(input_file, "rb") as f_in, open(output_file, "w") as f_out:
        f_out.write("[")
        first = True
       
        for word_id_str, postings in ijson.kvitems(f_in, ""):
            new_postings = [
                [p["document_id"], p["positions"], p["hit_counter"]]
                for p in postings
            ]
           
            if not first:
                f_out.write(",")
            first = False
            json.dump(new_postings, f_out)
       
        f_out.write("]")
```

**Storage Reduction:** ~40% smaller file size

#### Iteration 4: Streaming JSON Processing

**Problem:** Standard `json.load()` requires full file in memory.

**Solution:** Use `ijson` library for streaming JSON parsing:

```python
import ijson

index_file = 'inverted_index_dropped_keys.json'
word_index = lexicon['search']  # Get term ID for "search"

with open(index_file, 'rb') as f:
    for i, word_list in enumerate(ijson.items(f, 'item')):
        if i == word_index:
            # word_list is now loaded for just this term
            return word_list
```

**Benefit:** Query-time memory usage reduced to O(posting list size) instead of O(index size)

#### Batch Output Format (Research Papers)

Each batch stores a JSON structure indexed by term ID:

```json
{
  "12345": [
    ["P0", [12, 45], [5, 12, 3, 20, 482]],
    ["P7", [4, 8], [0, 7, 0, 7, 298]]
  ],
  "12346": [...]
}
```

Batch files are named sequentially: `inverted_index_json_part_1.json`, `inverted_index_json_part_2.json`, etc.

#### Final Batch Merge

A simple merging step combines all partial batches into one unified index:

```python
for word_id, postings in batch_index.items():
    if word_id not in inverted_index:
        inverted_index[word_id] = []
    inverted_index[word_id].extend(postings)
```

---

## 5. Sample Outputs

### Sample Lexicon

```json
{
    "algorithm": 189543,
    "and": 195108,
    "binary": 261923,
    "computer": 361087,
    "data": 397621,
    "google": 576791,
    "index": 641823,
    "information": 653421,
    "machine": 721456,
    "network": 811234,
    "programming": 1023456,
    "python": 1056789,
    "search": 1122667,
    "structure": 1178934,
    "technology": 1201567,
    "the": 1225317,
    "web": 1356789
}
```

### Sample Forward Index

```json
{
  "0": [189543, 195108, 397621, 641823, 1023456, 1056789, 1122667, 1178934],
  "1": [195108, 261923, 721456, 811234, 1201567, 1225317, 1356789],
  "2": [361087, 397621, 576791, 653421, 811234, 1023456, 1122667]
}
```

### Sample Inverted Index (Optimized Format)

```json
[
  [
    ["H0", [12, 45, 89, 134, 201], [2, 0, 1, 5, 0, 1, 0, 1245]],
    ["P0", [5, 78, 156, 234], [1, 0, 2, 4, 567]]
  ]
]
```

---

## 6. What's Working & Future Improvements

### 6.1 Current Working Functionality

| Component | Status | Description |
|-----------|--------|-------------|
| **Lexicon Construction** | ✅ Complete | Unified lexicon with ~1.4M terms |
| **Forward Index (HTML)** | ✅ Complete | All ~48K web pages indexed |
| **Forward Index (PDF)** | ✅ Complete | All research papers indexed |
| **Inverted Index (HTML)** | ✅ Complete | Full inverted index with hit counters |
| **Inverted Index (PDF)** | ✅ Complete | Inverted index with paper-specific metrics |
| **PageRank (Web)** | ✅ Complete | URL and domain rankings computed |
| **Citation Rank** | ✅ Complete | Research paper rankings computed |
| **Memory Optimization** | ✅ Complete | Key-dropped format + streaming parsing |

**Working Features:**
- Multi-threaded document processing (Python multiprocessing)
- Batch-based index construction to manage memory
- Streaming JSON parsing for query-time efficiency
- Anchor text extraction for relevance scoring
- Domain-based term occurrence tracking for lexicon filtering
- Hit counter computation for multiple document zones

### 6.2 Limitations

| Limitation | Impact | Potential Solution |
|------------|--------|-------------------|
| No real-time indexing | New documents require full re-index | Incremental index updates |
| Single-machine processing | Limited by local RAM/CPU | Distributed processing (Spark) |
| JSON storage format | Larger than binary formats | Protocol Buffers or custom binary |
| No spell correction | Exact match only | Edit distance / n-gram index |
| No stemming applied | "running" ≠ "run" | Porter/Snowball stemmer |
| No phrase queries | Only bag-of-words | Position-based proximity scoring |
| Limited to English | No multilingual support | Language detection + stemmers |

### 6.3 Future Improvements: Multi-Barrel Index Architecture

A major improvement planned for the next milestone is the transition to a **multi-barrel inverted index architecture**, similar to the early Google indexing system.

Instead of storing the entire inverted index in a single large structure, the index will be **divided into multiple barrels**, each responsible for a fixed range of term IDs. This design enhances scalability, query efficiency, and update flexibility.

---

#### 1. Barrel Partitioning

The unified lexicon assigns each term a unique `term_id`. These IDs will be partitioned into **K contiguous ranges**:

```
Barrel 0 → terms 0 – 49,999
Barrel 1 → terms 50,000 – 99,999
Barrel 2 → terms 100,000 – 149,999
...
Barrel K
```

Each barrel will contain only the postings belonging to the terms within its assigned range. This reduces memory usage and allows loading or rebuilding a single barrel without affecting the others.

---

#### 2. Dataset-Aware Document Identifiers

Our system currently includes two datasets:

- HTML Web Pages
- Research Papers (CORD-19)

To prevent collisions and keep storage compact, each document is represented internally using:

```
dataset_id     → small integer (0 = HTML, 1 = Papers)
local_doc_id   → numeric ID assigned sequentially within the dataset
```

This ensures fast comparisons and efficient storage.

For external display (UI, debugging), we may still show:

```
H123   → HTML document with ID 123
P45    → Research paper with ID 45
```

But internally only the numeric tuple is stored.

---

#### 3. Dataset-level Merging Process

Each dataset first builds its **own barrels**:

```
HTML Inverted Index:
    word_id_1_hitlists,
    word_id_2_hitlists,
    ...

Research Papers Inverted Index:
    word_id_1_hitlists,
    word_id_2_hitlists,
    ...
```

In the merge phase:

1. For each index `i` from 0 to `len(lexicon) - 1`
2. Load the HTML hitlists for word `i`
3. Load the Paper hitlists for word `i`
4. Merge their postings
5. Save them as unified
6. At query/search time they can be differentiated by their prefix (i.e., `P` for research papers and `H` for HTML files)

---

## Appendix: File Reference

### Key Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `lexicon_gen.py` | Lexicon scripts/ | Generate lexicon from HTML files |
| `lexicon_main.py` | Lexicon scripts/ | Lexicon filtering and processing |
| `merge_lexicons.py` | Lexicon scripts/ | Merge HTML and PDF lexicons |
| `assign_ids.py` | Lexicon scripts/ | Assign term IDs to lexicon |
| `jsonParser.cpp` | Lexicon scripts/ | Generate lexicon from JSON files (C++) |
| `forward_index.py` | Forward Index Scripts/ | HTML forward index generation |
| `forwardIndex.cpp` | Forward Index Scripts/ | PDF forward index generation (C++) |
| `mergeJSONs.cpp` | Forward Index Scripts/ | Merge forward index batches (C++) |
| `inverted_index.py` | Inverted Index Scripts/ | HTML inverted index generation |
| `JSONinvertedIndex.py` | Inverted Index Scripts/ | PDF inverted index generation |
| `merge_indexes.py` | Inverted Index Scripts/ | Merge HTML batch index files |
| `merge_json_batches.py` | Inverted Index Scripts/ | Merge JSON batch index files |
| `drop_keys.py` | Inverted Index Scripts/ | Optimize index JSON format |
| `page_rank.cpp` | Page Rank Scripts/ | PageRank algorithm (C++) |

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `lexicons_ids.json` | Lexicon/ | Final merged lexicon (~1.4M terms) |
| `forward_index_html_files.json` | Forward Index/ | HTML document forward index |
| `forward_index_pdf_files.json` | Forward Index/ | PDF document forward index |
| `inverted_index_dropped_keys.json` | Inverted Index/ | Optimized HTML inverted index |
| `inverted_index_dropped_keys.json` | Inverted Index/JsonBatches/ | Optimized PDF inverted index |
| `page_rank_results_with_urls.csv` | Page Rank Results/ | URL PageRank scores |
| `domain_rank_results_with_domain_nm.csv` | Page Rank Results/ | Domain PageRank scores |
| `citation_rank_output.csv` | Page Rank Results/ | Paper citation scores |

---
