"""
Quick Search - Simple command-line interface for BigSearch
==========================================================

Usage:
    python quick_search.py "your query here"
    
    Or interactive mode:
    python quick_search.py
"""

import sys
import os

# Add parent directory to path to import hybrid_search
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_search import HybridSearchEngine


def quick_search(query, top_k=10):
    """
    Quick search function - returns results with URLs.
    
    Args:
        query: Search query string
        top_k: Number of results to return (default: 10)
    
    Returns:
        List of tuples: (rank, doc_id, score, url)
    """
    engine = HybridSearchEngine()
    results = engine.search(query, top_k=top_k, use_semantic=True)
    
    formatted_results = []
    
    for rank, result in enumerate(results, 1):
        if isinstance(result, list):
            # Single-word results
            doc_id, score, url = result
            formatted_results.append((rank, doc_id, score, url))
        else:
            # Multi-word results
            doc_id = result['doc_id']
            score = result['final_score']
            url = result['url']
            formatted_results.append((rank, doc_id, score, url))
    
    return formatted_results


def print_results(results, query):
    """Print search results in a clean format."""
    if not results:
        print("\nNo results found.")
        return
    
    print(f"\n{'='*100}")
    print(f"Search Results for: '{query}'")
    print(f"{'='*100}\n")
    
    for rank, doc_id, score, url in results:
        print(f"{rank}. [{doc_id}] Score: {score:.2f}")
        print(f"   {url}")
        print()


def main():
    """Main entry point."""
    
    # Check if query provided as command-line argument
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        print(f"Searching for: '{query}'...")
        
        results = quick_search(query, top_k=10)
        print_results(results, query)
    else:
        # Interactive mode
        print("="*70)
        print("BigSearch Quick Search")
        print("="*70)
        print("Type your query and press Enter (or 'quit' to exit)")
        print("="*70)
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                results = quick_search(query, top_k=10)
                print_results(results, query)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
