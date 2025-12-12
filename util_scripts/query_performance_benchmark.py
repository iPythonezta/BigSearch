"""
Query Performance Benchmark Script
===================================
This script measures actual search query performance metrics:
- Single-word query response times
- Multi-word query response times
- Query parsing and processing times
- Result set sizes and ranking times
"""

import orjson
import ormsgpack
import time
import json
import sys
import tracemalloc
from pathlib import Path
from statistics import mean, stdev
from typing import List, Dict, Tuple
import re
import math
from urllib.parse import urlparse

# Path configuration
BASE_DIR = Path(__file__).parent.parent
BARRELS_DIR = BASE_DIR / "Barrels"
RESULTS_FILE = BASE_DIR / "Documentation" / "query_benchmark_results.json"

# Test configuration
NUM_RUNS = 3  # Number of iterations per query (reduced for speed)
WARMUP_RUNS = 1  # Minimal warmup

# Test queries (reduced set for faster benchmarking)
SINGLE_WORD_QUERIES = [
    "health", "cancer", "covid", "algorithm", "python"
]

MULTI_WORD_QUERIES = [
    "machine learning",
    "covid 19",
    "artificial intelligence",
    "cancer research",
    "data structure"
]


class QueryBenchmark:
    """Query benchmark executor"""
    
    def __init__(self):
        self.barrels_index = None
        self.doc_id_to_url = None
        self.page_rank_dict = {}
        self.domain_rank_dict = {}
        self.results = {
            "single_word": {},
            "multi_word": {},
            "summary": {}
        }
        
    def load_data(self):
        """Load all necessary data files"""
        print("Loading index and metadata...")
        start = time.perf_counter()
        
        # Load barrels index
        with open(BARRELS_DIR / "barrels_index.json", "rb") as f:
            self.barrels_index = orjson.loads(f.read())
        
        # Load document ID to URL mapping
        with open(BASE_DIR / "Data" / "ind_to_url.json", "r") as f:
            self.doc_id_to_url = orjson.loads(f.read())
        
        load_time = time.perf_counter() - start
        print(f"✓ Data loaded in {load_time:.2f}s")
        print(f"  - Lexicon size: {len(self.barrels_index):,} terms")
        print(f"  - Document mappings: {len(self.doc_id_to_url):,} URLs")
        
    def word_lookup(self, indices):
        """Load data from barrel"""
        barrel_id = indices[0]
        word_index = indices[1]
        with open(BARRELS_DIR / f"{barrel_id}.msgpack", "rb") as f:
            barrel_data = ormsgpack.unpackb(f.read())
        return barrel_data[word_index]
    
    def process_query(self, word, rps=True):
        """Process query text"""
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
    
    def score_html_files(self, hitlist):
        """Simple scoring for HTML files"""
        hit_counter = hitlist[2]
        n_title = hit_counter[0]
        n_meta = hit_counter[1]
        n_heading = hit_counter[2]
        n_total = hit_counter[3]
        
        score = 0.0
        score += min(n_title * 7.5, 15)
        score += min(n_heading * 3, 9)
        score += min(n_meta * 2, 6)
        
        body_hits = max(0, n_total - (n_title + n_heading + n_meta))
        freq_score = math.log(1 + body_hits) * 7
        score += min(freq_score, 20)
        
        return max(1.0, min(80.0, score))
    
    def perform_single_word_search(self, word):
        """Execute single-word search"""
        tokens = self.process_query(word, rps=False)
        if not tokens:
            return []
        
        token = tokens[0]
        if token not in self.barrels_index:
            return []
        
        indices = self.barrels_index[token]
        hitlist = self.word_lookup(indices)
        
        html_hits = []
        for hit in hitlist:
            doc_id = hit[0]
            if doc_id.startswith("H"):
                html_hits.append(hit)
        
        # Score hits
        scored_results = []
        for hit in html_hits:
            score = self.score_html_files(hit)
            scored_results.append((hit[0], score))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results
    
    def multi_word_queries(self, query):
        """Get hitlists for multi-word query"""
        tokens = self.process_query(query, rps=True)
        hitlists = []
        for token in tokens:
            if token in self.barrels_index:
                barrel_indices = self.barrels_index[token]
                htl = self.word_lookup(barrel_indices)
                hitlists.append(htl)
        return hitlists
    
    def get_intersected_results(self, hitlists):
        """Get intersection of results from multiple hitlists"""
        if not hitlists:
            return {}
        
        hitlists.sort(key=len)
        common_doc_ids = {hit[0] for hit in hitlists[0]}
        
        for i in range(1, len(hitlists)):
            next_doc_ids = {hit[0] for hit in hitlists[i]}
            common_doc_ids.intersection_update(next_doc_ids)
            
            if not common_doc_ids:
                return {}
        
        final_data = {}
        for hitlist in hitlists:
            for hit in hitlist:
                doc_id = hit[0]
                if doc_id in common_doc_ids:
                    if doc_id not in final_data:
                        final_data[doc_id] = []
                    final_data[doc_id].append(hit)
        
        return final_data
    
    def benchmark_single_word_query(self, query: str) -> Dict:
        """Benchmark a single-word query"""
        times = []
        result_counts = []
        
        # Warmup runs
        for _ in range(WARMUP_RUNS):
            self.perform_single_word_search(query)
        
        # Actual benchmark runs
        for _ in range(NUM_RUNS):
            start = time.perf_counter()
            results = self.perform_single_word_search(query)
            end = time.perf_counter()
            
            times.append((end - start) * 1000)  # Convert to ms
            result_counts.append(len(results))
        
        return {
            "query": query,
            "avg_time_ms": round(mean(times), 2),
            "min_time_ms": round(min(times), 2),
            "max_time_ms": round(max(times), 2),
            "std_dev_ms": round(stdev(times), 2) if len(times) > 1 else 0,
            "avg_results": int(mean(result_counts)),
            "result_range": f"{min(result_counts)}-{max(result_counts)}"
        }
    
    def benchmark_multi_word_query(self, query: str) -> Dict:
        """Benchmark a multi-word query"""
        times = []
        result_counts = []
        
        # Warmup runs
        for _ in range(WARMUP_RUNS):
            hitlists = self.multi_word_queries(query)
            self.get_intersected_results(hitlists)
        
        # Actual benchmark runs
        for _ in range(NUM_RUNS):
            start = time.perf_counter()
            hitlists = self.multi_word_queries(query)
            results = self.get_intersected_results(hitlists)
            end = time.perf_counter()
            
            times.append((end - start) * 1000)  # Convert to ms
            result_counts.append(len(results))
        
        return {
            "query": query,
            "avg_time_ms": round(mean(times), 2),
            "min_time_ms": round(min(times), 2),
            "max_time_ms": round(max(times), 2),
            "std_dev_ms": round(stdev(times), 2) if len(times) > 1 else 0,
            "avg_results": int(mean(result_counts)),
            "result_range": f"{min(result_counts)}-{max(result_counts)}"
        }
    
    def run_benchmarks(self):
        """Run all benchmarks"""
        print("\n" + "=" * 80)
        print("QUERY PERFORMANCE BENCHMARK")
        print("=" * 80)
        print(f"Configuration:")
        print(f"  - Warmup runs: {WARMUP_RUNS}")
        print(f"  - Benchmark runs: {NUM_RUNS}")
        print(f"  - Single-word queries: {len(SINGLE_WORD_QUERIES)}")
        print(f"  - Multi-word queries: {len(MULTI_WORD_QUERIES)}")
        print("=" * 80)
        
        # Benchmark single-word queries
        print("\nBenchmarking single-word queries...")
        print("-" * 80)
        single_word_times = []
        
        for query in SINGLE_WORD_QUERIES:
            result = self.benchmark_single_word_query(query)
            self.results["single_word"][query] = result
            single_word_times.append(result["avg_time_ms"])
            
            print(f"'{query:15s}' -> {result['avg_time_ms']:6.2f}ms "
                  f"(±{result['std_dev_ms']:.2f}ms) | "
                  f"{result['avg_results']:5d} results")
        
        # Benchmark multi-word queries
        print("\nBenchmarking multi-word queries...")
        print("-" * 80)
        multi_word_times = []
        
        for query in MULTI_WORD_QUERIES:
            result = self.benchmark_multi_word_query(query)
            self.results["multi_word"][query] = result
            multi_word_times.append(result["avg_time_ms"])
            
            print(f"'{query:25s}' -> {result['avg_time_ms']:6.2f}ms "
                  f"(±{result['std_dev_ms']:.2f}ms) | "
                  f"{result['avg_results']:5d} results")
        
        # Calculate summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        
        self.results["summary"] = {
            "single_word": {
                "avg_time_ms": round(mean(single_word_times), 2),
                "min_time_ms": round(min(single_word_times), 2),
                "max_time_ms": round(max(single_word_times), 2),
                "median_time_ms": round(sorted(single_word_times)[len(single_word_times)//2], 2),
                "queries_tested": len(SINGLE_WORD_QUERIES)
            },
            "multi_word": {
                "avg_time_ms": round(mean(multi_word_times), 2),
                "min_time_ms": round(min(multi_word_times), 2),
                "max_time_ms": round(max(multi_word_times), 2),
                "median_time_ms": round(sorted(multi_word_times)[len(multi_word_times)//2], 2),
                "queries_tested": len(MULTI_WORD_QUERIES)
            }
        }
        
        print(f"\nSingle-word queries:")
        print(f"  Average: {self.results['summary']['single_word']['avg_time_ms']:.2f}ms")
        print(f"  Median:  {self.results['summary']['single_word']['median_time_ms']:.2f}ms")
        print(f"  Range:   {self.results['summary']['single_word']['min_time_ms']:.2f}ms - "
              f"{self.results['summary']['single_word']['max_time_ms']:.2f}ms")
        
        print(f"\nMulti-word queries:")
        print(f"  Average: {self.results['summary']['multi_word']['avg_time_ms']:.2f}ms")
        print(f"  Median:  {self.results['summary']['multi_word']['median_time_ms']:.2f}ms")
        print(f"  Range:   {self.results['summary']['multi_word']['min_time_ms']:.2f}ms - "
              f"{self.results['summary']['multi_word']['max_time_ms']:.2f}ms")
        
        print("\n" + "=" * 80)
        print("BENCHMARK COMPLETE")
        print("=" * 80)
    
    def save_results(self):
        """Save results to JSON file"""
        output = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": {
                "warmup_runs": WARMUP_RUNS,
                "benchmark_runs": NUM_RUNS,
                "single_word_queries": SINGLE_WORD_QUERIES,
                "multi_word_queries": MULTI_WORD_QUERIES
            },
            "results": self.results
        }
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Results saved to: {RESULTS_FILE}")


def main():
    try:
        benchmark = QueryBenchmark()
        benchmark.load_data()
        benchmark.run_benchmarks()
        benchmark.save_results()
        return 0
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
