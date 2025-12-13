"""
BigSearch Hybrid Search Engine
==============================
Combines keyword-based search (inverted index) with semantic search (word embeddings)
for improved search results.

Usage:
    python hybrid_search.py
    
    Or import and use:
    from hybrid_search import HybridSearchEngine
    
    engine = HybridSearchEngine()
    results = engine.search("machine learning algorithms", top_k=10)
"""

import pandas as pd
import ormsgpack
import orjson
import re
import os
import math
import numpy as np
from urllib.parse import urlparse
from collections import Counter

print("Loading BigSearch Hybrid Search Engine...")

# ==================== DATA LOADING ====================
print("  → Loading page rank data...")
page_rank_results = pd.read_csv("..\\Page Rank Results\\page_rank_results_with_urls.csv")
domain_rank_results = pd.read_csv("..\\Page Rank Results\\domain_rank_results_with_domain_nm.csv")
citation_rank = pd.read_csv("..\\Page Rank Results\\citation_ranks_with_scores.csv")
rps_info = pd.read_csv("..\\Data\\Cord 19\\metadata_cleaned.csv")

print("  → Loading URL mappings...")
doc_id_to_url = {}
with open("..\\Data\\ind_to_url.json", "r") as f:
    doc_id_to_url = orjson.loads(f.read())

print("  → Creating rank dictionaries...")
citation_dict = dict(zip(citation_rank["paper_title"], citation_rank["Score"]))
rps_info_dict = dict(zip(rps_info["id"], zip(rps_info["title"], rps_info["url"])))
page_rank_dict = dict(zip(page_rank_results["URL"], page_rank_results["Score"]))
domain_rank_dict = dict(zip(domain_rank_results["Domain"], domain_rank_results["Score"]))

print("  → Loading barrel index...")
with open("..\\Barrels\\barrels_index.json", "r", encoding="utf-8") as f:
    barrels_index = orjson.loads(f.read())

print("  → Loading semantic search data...")
try:
    html_embeddings = orjson.loads(open('..\\Semantic Search Data\\html_embeddings.json', 'rb').read())
    json_embeddings = orjson.loads(open('..\\Semantic Search Data\\json_embeddings.json', 'rb').read())
    idf_map = orjson.loads(open('..\\Semantic Search Data\\idf_map.json', 'rb').read())
    
    from gensim.models import KeyedVectors
    word2vec_model = KeyedVectors.load_word2vec_format('glove.6B.50d.word2vec.txt', binary=False)
    
    merged_embeddings = html_embeddings + json_embeddings
    html_docs_count = len(html_embeddings)
    json_docs_count = len(json_embeddings)
    merged_embeddings_np = np.array(merged_embeddings)
    
    SEMANTIC_AVAILABLE = True
    print("  ✓ Semantic search enabled")
except Exception as e:
    print(f"  ⚠ Semantic search unavailable: {e}")
    SEMANTIC_AVAILABLE = False

print("✓ BigSearch Hybrid Engine loaded successfully!\n")


# ==================== HELPER FUNCTIONS ====================

def word_lookup(indices):
    """Load a word's posting list from barrel."""
    barrel_id = indices[0]
    word_index = indices[1]
    with open(f"..\\Barrels\\{barrel_id}.msgpack", "rb") as f:
        barrel_data = ormsgpack.unpackb(f.read())
    return barrel_data[word_index]


def normalize_title(title):
    """Normalize research paper titles for matching."""
    title = title.lower()
    title = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}|<.*?>', ' ', title)
    title = re.sub(r'[^a-z\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()


def process_query(word, rps=True):
    """Tokenize and normalize query text."""
    text = re.sub(r'\n', ' ', word)
    if rps:
        text = re.sub(r'(?<!\d)[^\w\s]|[^\w\s](?!\d)', '', text)
    else:
        text = re.sub(r'(?<!\d)[^\w\s]|[^\w\s](?!\d)', ' ', text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[,\(\)\[\]\{\}]", "", text)
    text = text.lower()
    tokens = text.split(' ')
    return tokens


# ==================== KEYWORD SCORING FUNCTIONS ====================

def score_html_files(hitlist):
    """Score HTML documents based on keyword occurrence."""
    doc_id = hitlist[0]
    positions = hitlist[1]
    hit_counter = hitlist[2]

    n_title = hit_counter[0]
    n_meta = hit_counter[1]
    n_heading = hit_counter[2]
    n_total = hit_counter[3]
    n_href = hit_counter[4]
    in_domain = hit_counter[5]
    in_url = hit_counter[6]
    doc_len = hit_counter[7] if hit_counter[7] > 0 else 1

    score = 0.0

    # Zone weighting
    score += min(n_title * 7.5, 15)
    if in_domain:
        score += 10
    if in_url:
        score += 5
    score += min(n_heading * 3, 9)
    score += min(n_meta * 2, 6)

    # Position bonus
    if positions:
        first_pos = positions[0]
        score += 15 - min(first_pos // 7, 15)

    # Frequency scoring with density penalty
    body_hits = max(0, n_total - (n_title + n_heading + n_meta))
    density = n_total / doc_len
    freq_score = math.log(1 + body_hits) * 7
    score += min(freq_score, 20)
    score *= (1 - density)

    # Final clamping
    final_score = max(1.0, min(80.0, score))

    # Add PageRank and DomainRank
    doc_url = doc_id_to_url.get(doc_id.replace("H", ""), "")
    page_rank_score = page_rank_dict.get(doc_url, 0)
    domain = urlparse(doc_url).netloc
    domain_rank_score = domain_rank_dict.get(domain, 0)

    return int(final_score + page_rank_score + domain_rank_score)


def rank_research_papers(hitlist):
    """Score research papers based on keyword occurrence."""
    doc_id = hitlist[0]
    positions = hitlist[1]
    hit_counter = hitlist[2]

    n_golden = hit_counter[0]
    n_body = hit_counter[1]
    n_other = hit_counter[2]
    n_total = hit_counter[3]
    doc_len = hit_counter[4]

    score = 0.0

    # Golden zone (title, author, abstract)
    score += min(n_golden * 5, 35)

    # Position bonus
    if positions:
        first_pos = positions[0]
        score += 15 - min(first_pos // 15, 10)

    # Body frequency with density penalty
    density = n_total / doc_len
    relevant_hits = n_body + (n_other * 0.1)
    freq_score = math.log(1 + relevant_hits) * 10
    score += min(freq_score, 40)
    score *= (1 - density)

    # Final clamping
    final_score = max(1.0, min(80.0, score))

    # Add citation rank
    title = rps_info_dict.get(int(doc_id.replace("P", "")), ("", ""))[0].strip()
    title = normalize_title(title)
    citation_rank_score = citation_dict.get(title, 0)

    return int(final_score + citation_rank_score)


# ==================== SEMANTIC SEARCH FUNCTIONS ====================

def compute_tf(tokens):
    """Compute term frequency for query tokens."""
    counts = Counter(tokens)
    total = sum(counts.values())
    tf_map = {word: count / total for word, count in counts.items()}
    return tf_map


def query_to_embedding(tokens, model, idf_map):
    """Convert query tokens to embedding vector using TF-IDF weighting."""
    tf_map = compute_tf(tokens)
    vecs, weights = [], []
    for word, tf in tf_map.items():
        if word in model:
            tfidf = tf * idf_map.get(word, 0)
            vecs.append(model[word] * tfidf)
            weights.append(tfidf)
    if not vecs:
        return np.zeros(model.vector_size)
    return np.sum(vecs, axis=0) / np.sum(weights)


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def convert_ind_to_doc_id(index):
    """Convert embedding index to document ID."""
    if index < html_docs_count:
        return f"H{index}"
    else:
        return f"P{index - html_docs_count}"


def get_semantic_scores(query):
    """Get semantic similarity scores for all documents."""
    if not SEMANTIC_AVAILABLE:
        return {}
    
    text = query.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    tokens = text.split()
    
    query_vec = query_to_embedding(tokens, word2vec_model, idf_map)
    
    # Calculate similarities for all documents
    similarities = {}
    for i, doc_vec in enumerate(merged_embeddings_np):
        sim = cosine_similarity(query_vec, doc_vec)
        doc_id = convert_ind_to_doc_id(i)
        similarities[doc_id] = sim
    
    return similarities


# ==================== HYBRID SEARCH FUNCTIONS ====================

def perform_single_word_search(query, use_semantic=True, semantic_weight=20):
    """
    Perform single-word search with optional semantic enhancement.
    
    Args:
        query: Search query string
        use_semantic: Whether to include semantic scores
        semantic_weight: Multiplier for semantic scores (default: 20)
    
    Returns:
        List of tuples: (doc_id, combined_score, url)
    """
    tokens = process_query(query, rps=False)
    if not tokens:
        return []
    
    token = tokens[0]
    
    if token not in barrels_index:
        return []
    
    indices = barrels_index[token]
    hitlist = word_lookup(indices)
    
    # Separate HTML and research paper hits
    html_hits = [hit for hit in hitlist if hit[0].startswith("H")]
    rps_hits = [hit for hit in hitlist if hit[0].startswith("P")]
    
    # Score HTML hits
    scored_html = []
    for hit in html_hits:
        score = score_html_files(hit)
        url = doc_id_to_url.get(hit[0].replace("H", ""), "")
        scored_html.append([hit[0], score, url])
    
    # Score RPS hits
    scored_rps = []
    for hit in rps_hits:
        score = rank_research_papers(hit)
        url = rps_info_dict.get(int(hit[0].replace("P", "")), ("", ""))[1]
        scored_rps.append([hit[0], score, url])
    
    combined_results = scored_html + scored_rps
    
    # Add semantic scores if enabled
    if use_semantic and SEMANTIC_AVAILABLE:
        semantic_scores = get_semantic_scores(query)
        
        for result in combined_results:
            doc_id = result[0]
            keyword_score = result[1]
            semantic_score = semantic_scores.get(doc_id, 0)
            
            # Combine scores: keyword_score + (semantic_weight * semantic_score)
            combined_score = keyword_score + (semantic_weight * semantic_score)
            result[1] = combined_score
    
    # Sort by score
    combined_results.sort(key=lambda x: x[1], reverse=True)
    
    return combined_results


def perform_multi_word_search(query, use_semantic=True, semantic_weight=20):
    """
    Perform multi-word search with optional semantic enhancement.
    
    Args:
        query: Search query string
        use_semantic: Whether to include semantic scores
        semantic_weight: Multiplier for semantic scores (default: 20)
    
    Returns:
        List of dictionaries with detailed result information
    """
    tokens = process_query(query, rps=True)
    hitlists = []
    
    for token in tokens:
        if token in barrels_index:
            barrel_indices = barrels_index[token]
            htl = word_lookup(barrel_indices)
            hitlists.append(htl)
    
    if not hitlists:
        return []
    
    # Perform intersection
    hitlists_sorted = sorted(hitlists, key=len)
    common_doc_ids = {hit[0] for hit in hitlists_sorted[0]}
    
    for i in range(1, len(hitlists_sorted)):
        next_doc_ids = {hit[0] for hit in hitlists_sorted[i]}
        common_doc_ids.intersection_update(next_doc_ids)
        if not common_doc_ids:
            return []
    
    # Reconstruct hit data
    intersected_data = {}
    for hitlist in hitlists:
        for hit in hitlist:
            doc_id = hit[0]
            if doc_id in common_doc_ids:
                if doc_id not in intersected_data:
                    intersected_data[doc_id] = []
                intersected_data[doc_id].append(hit)
    
    # Get semantic scores if enabled
    semantic_scores = {}
    if use_semantic and SEMANTIC_AVAILABLE:
        semantic_scores = get_semantic_scores(query)
    
    # Calculate scores
    ranked_results = []
    
    for doc_id in intersected_data:
        hits_for_doc = intersected_data[doc_id]
        
        # Calculate individual word scores
        word_scores = []
        position_vectors = []
        
        for hit in hits_for_doc:
            if doc_id.startswith("P"):
                word_score = rank_research_papers(hit)
            else:
                word_score = score_html_files(hit)
            
            word_scores.append(word_score)
            
            positions = hit[1]
            if isinstance(positions, list):
                position_vectors.extend(positions)
            else:
                position_vectors.append(positions)
        
        # Average word score
        avg_word_score = sum(word_scores) / len(word_scores) if word_scores else 0
        
        # Count close matches (words within 2 positions)
        close_count = 0
        if len(position_vectors) > 1:
            sorted_positions = sorted(position_vectors)
            for i in range(len(sorted_positions) - 1):
                if sorted_positions[i+1] - sorted_positions[i] <= 2:
                    close_count += 1
        
        cluster_range = max(position_vectors) - min(position_vectors) if position_vectors else 0
        
        # Calculate keyword-based combined score
        keyword_combined_score = close_count + avg_word_score
        
        # Add semantic score if available
        semantic_score = semantic_scores.get(doc_id, 0)
        final_score = keyword_combined_score + (semantic_weight * semantic_score)
        
        # Fetch URL
        if doc_id.startswith("P"):
            url = rps_info_dict.get(int(doc_id.replace("P", "")), ("", ""))[1]
        else:
            url = doc_id_to_url.get(doc_id.replace("H", ""), "")
        
        ranked_results.append({
            'doc_id': doc_id,
            'final_score': final_score,
            'keyword_score': keyword_combined_score,
            'semantic_score': semantic_score,
            'avg_word_score': avg_word_score,
            'close_matches': close_count,
            'cluster_range': cluster_range,
            'url': url,
            'positions': position_vectors
        })
    
    # Sort by final score
    ranked_results.sort(key=lambda x: x['final_score'], reverse=True)
    
    return ranked_results


# ==================== MAIN SEARCH CLASS ====================

class HybridSearchEngine:
    """
    Hybrid search engine combining keyword and semantic search.
    """
    
    def __init__(self):
        self.semantic_available = SEMANTIC_AVAILABLE
    
    def search(self, query, top_k=10, use_semantic=True, semantic_weight=20):
        """
        Perform hybrid search.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            use_semantic: Whether to include semantic scores
            semantic_weight: Multiplier for semantic scores (default: 20)
        
        Returns:
            List of results (format depends on query type)
        """
        tokens = process_query(query, rps=False)
        
        if len(tokens) == 1:
            results = perform_single_word_search(query, use_semantic, semantic_weight)
            return results[:top_k]
        else:
            results = perform_multi_word_search(query, use_semantic, semantic_weight)
            return results[:top_k]
    
    def display_results(self, results, query=""):
        """
        Display search results in a formatted way.
        """
        if not results:
            print("No results found.")
            return
        
        print(f"\n{'='*130}")
        if query:
            print(f"Search Results for: '{query}'")
        print(f"{'='*130}")
        
        # Check if single-word or multi-word results
        if isinstance(results[0], list):
            # Single-word results: (doc_id, score, url)
            print(f"{'Rank':<6} {'Doc ID':<10} {'Score':<12} {'URL':<100}")
            print(f"{'-'*130}")
            
            for rank, result in enumerate(results, 1):
                doc_id = result[0]
                score = result[1]
                url = result[2][:97] + "..." if len(result[2]) > 100 else result[2]
                print(f"{rank:<6} {doc_id:<10} {score:<12.2f} {url}")
        else:
            # Multi-word results: dictionaries
            print(f"{'Rank':<6} {'Doc ID':<10} {'Total':<10} {'Keyword':<10} {'Semantic':<10} {'Close':<7} {'URL':<70}")
            print(f"{'-'*130}")
            
            for rank, r in enumerate(results, 1):
                doc_id = r['doc_id']
                total = r['final_score']
                keyword = r['keyword_score']
                semantic = r['semantic_score']
                close = r['close_matches']
                url = r['url'][:67] + "..." if len(r['url']) > 70 else r['url']
                
                print(f"{rank:<6} {doc_id:<10} {total:<10.2f} {keyword:<10.2f} {semantic:<10.4f} {close:<7} {url}")
        
        print(f"{'='*130}\n")


# ==================== COMMAND LINE INTERFACE ====================

def main():
    """Interactive command-line search interface."""
    engine = HybridSearchEngine()
    
    print("="*70)
    print("BigSearch Hybrid Search Engine - Interactive Mode")
    print("="*70)
    print("Combines keyword-based search with semantic similarity")
    if engine.semantic_available:
        print("✓ Semantic search: ENABLED")
    else:
        print("⚠ Semantic search: DISABLED (keyword-only mode)")
    print("="*70)
    print("\nCommands:")
    print("  - Type your search query and press Enter")
    print("  - Type 'quit' or 'exit' to stop")
    print("  - Type 'nosem' to disable semantic search")
    print("  - Type 'sem' to enable semantic search")
    print("="*70)
    
    use_semantic = True
    
    while True:
        try:
            query = input("\nSearch query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if query.lower() == 'nosem':
                use_semantic = False
                print("✓ Semantic search disabled")
                continue
            
            if query.lower() == 'sem':
                use_semantic = True
                if engine.semantic_available:
                    print("✓ Semantic search enabled")
                else:
                    print("⚠ Semantic search unavailable (missing data files)")
                continue
            
            if not query:
                continue
            
            print(f"\nSearching for: '{query}'...")
            print(f"Mode: {'Hybrid (keyword + semantic)' if use_semantic else 'Keyword-only'}")
            
            results = engine.search(query, top_k=15, use_semantic=use_semantic)
            engine.display_results(results, query)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
