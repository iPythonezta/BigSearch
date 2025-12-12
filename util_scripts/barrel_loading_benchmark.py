"""
Barrel Loading Performance Benchmark Script
============================================
Fast benchmark based on speed_test.py - measures actual performance:
- File sizes (JSON vs MessagePack)
- Loading times (standard json, orjson, ormsgpack)
- Compression ratios
"""

import json
import orjson
import ormsgpack
import os
import time
import sys
from pathlib import Path

# Path configuration
BARRELS_DIR = Path(__file__).parent.parent / "Barrels"
RESULTS_FILE = Path(__file__).parent.parent / "Documentation" / "benchmark_results.json"


def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)


def run_benchmark():
    """Run fast barrel loading benchmark"""
    print("=" * 80)
    print("BARREL LOADING PERFORMANCE BENCHMARK")
    print("=" * 80)
    print(f"Barrels directory: {BARRELS_DIR}")
    print("=" * 80)
    print()
    
    # Storage for results
    std_json_times = []
    orjson_times = []
    msgpack_times = []
    json_sizes = []
    msgpack_sizes = []
    barrel_entry_counts = []
    
    total_json_size = 0
    total_msgpack_size = 0
    
    print("Testing all 79 barrels...")
    print("-" * 80)
    
    for i in range(79):
        json_path = BARRELS_DIR / f"{i}.json"
        msgpack_path = BARRELS_DIR / f"{i}.msgpack"
        
        # Get file sizes
        json_size = get_file_size_mb(json_path)
        msgpack_size = get_file_size_mb(msgpack_path)
        json_sizes.append(json_size)
        msgpack_sizes.append(msgpack_size)
        total_json_size += json_size
        total_msgpack_size += msgpack_size
        
        # Test standard json loading
        start = time.time()
        with open(json_path, 'r', encoding='utf-8') as f:
            data_std_json = json.load(f)
        std_json_time = time.time() - start
        std_json_times.append(std_json_time)
        
        # Test MessagePack loading
        start = time.time()
        with open(msgpack_path, 'rb') as f:
            data_msgpack = ormsgpack.unpackb(f.read())
        msgpack_time = time.time() - start
        msgpack_times.append(msgpack_time)
        
        # Test orjson loading
        start = time.time()
        with open(json_path, 'rb') as f:
            data_orjson = orjson.loads(f.read())
        orjson_time = time.time() - start
        orjson_times.append(orjson_time)
        
        # Verify data integrity
        barrel_entry_counts.append(len(data_msgpack))
        
        # Print progress every 10 barrels
        if (i + 1) % 10 == 0 or i == 78:
            print(f"✓ Processed barrels 0-{i} ({i+1}/79)")
    
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    # Calculate statistics
    avg_std_json_time = sum(std_json_times) / len(std_json_times)
    avg_orjson_time = sum(orjson_times) / len(orjson_times)
    avg_msgpack_time = sum(msgpack_times) / len(msgpack_times)
    
    min_std_json_time = min(std_json_times)
    max_std_json_time = max(std_json_times)
    min_orjson_time = min(orjson_times)
    max_orjson_time = max(orjson_times)
    min_msgpack_time = min(msgpack_times)
    max_msgpack_time = max(msgpack_times)
    
    compression_ratio = total_json_size / total_msgpack_size if total_msgpack_size > 0 else 0
    size_reduction_percent = (1 - total_msgpack_size / total_json_size) * 100 if total_json_size > 0 else 0
    speedup_vs_std_json = avg_std_json_time / avg_msgpack_time if avg_msgpack_time > 0 else 0
    speedup_vs_orjson = avg_orjson_time / avg_msgpack_time if avg_msgpack_time > 0 else 0
    
    # Print file size results
    print(f"\nFile Size Analysis:")
    print(f"  Total JSON size:        {total_json_size:8.2f} MB")
    print(f"  Total MessagePack size: {total_msgpack_size:8.2f} MB")
    print(f"  Compression ratio:      {compression_ratio:8.2f}x")
    print(f"  Size reduction:         {size_reduction_percent:8.1f}%")
    print(f"  Total entries across all barrels: {sum(barrel_entry_counts):,}")
    
    # Print loading time results
    print(f"\nLoading Time Analysis:")
    print(f"  Standard json:")
    print(f"    Average: {avg_std_json_time*1000:6.2f}ms")
    print(f"    Range:   {min_std_json_time*1000:6.2f}ms - {max_std_json_time*1000:6.2f}ms")
    print(f"  orjson (Rust-optimized JSON):")
    print(f"    Average: {avg_orjson_time*1000:6.2f}ms")
    print(f"    Range:   {min_orjson_time*1000:6.2f}ms - {max_orjson_time*1000:6.2f}ms")
    print(f"  ormsgpack (MessagePack):")
    print(f"    Average: {avg_msgpack_time*1000:6.2f}ms")
    print(f"    Range:   {min_msgpack_time*1000:6.2f}ms - {max_msgpack_time*1000:6.2f}ms")
    print(f"  Speedup (MessagePack vs standard json): {speedup_vs_std_json:.2f}x faster")
    print(f"  Speedup (MessagePack vs orjson): {speedup_vs_orjson:.2f}x faster")
    
    # Print performance improvements
    time_improvement_vs_std = (1 - avg_msgpack_time / avg_std_json_time) * 100 if avg_std_json_time > 0 else 0
    time_improvement_vs_orjson = (1 - avg_msgpack_time / avg_orjson_time) * 100 if avg_orjson_time > 0 else 0
    print(f"\nPerformance Improvements (MessagePack vs JSON):")
    print(f"  vs standard json:  {time_improvement_vs_std:.1f}% faster")
    print(f"  vs orjson:         {time_improvement_vs_orjson:.1f}% faster")
    print(f"  Storage savings:   {size_reduction_percent:.1f}%")
    
    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    
    # Prepare results for saving
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_barrels": 79,
        "file_sizes": {
            "total_json_mb": round(total_json_size, 2),
            "total_msgpack_mb": round(total_msgpack_size, 2),
            "compression_ratio": round(compression_ratio, 2),
            "size_reduction_percent": round(size_reduction_percent, 2)
        },
        "load_times": {
            "std_json_avg_ms": round(avg_std_json_time * 1000, 2),
            "std_json_min_ms": round(min_std_json_time * 1000, 2),
            "std_json_max_ms": round(max_std_json_time * 1000, 2),
            "orjson_avg_ms": round(avg_orjson_time * 1000, 2),
            "orjson_min_ms": round(min_orjson_time * 1000, 2),
            "orjson_max_ms": round(max_orjson_time * 1000, 2),
            "msgpack_avg_ms": round(avg_msgpack_time * 1000, 2),
            "msgpack_min_ms": round(min_msgpack_time * 1000, 2),
            "msgpack_max_ms": round(max_msgpack_time * 1000, 2),
            "speedup_vs_std_json": round(speedup_vs_std_json, 2),
            "speedup_vs_orjson": round(speedup_vs_orjson, 2)
        },
        "performance_improvements": {
            "vs_std_json_percent": round(time_improvement_vs_std, 2),
            "vs_orjson_percent": round(time_improvement_vs_orjson, 2),
            "storage_savings_percent": round(size_reduction_percent, 2)
        },
        "total_entries": sum(barrel_entry_counts)
    }
    
    # Save results
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {RESULTS_FILE}")
    
    return results


if __name__ == "__main__":
    try:
        run_benchmark()
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        print(traceback.format_exc())
        exit(1)
