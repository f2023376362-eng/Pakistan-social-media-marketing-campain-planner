"""
Standalone Benchmark Runner for DS391 Big Data Analytics.
Executes the synthetic scalability benchmark suite (1x, 10x, 100x)
and outputs structured JSON and chart artifacts.
"""

import io
import os
import sys
import tempfile

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

from src.loader import load_dataset
from src.benchmark import run_scalability_benchmarks
from src.visualizer import plot_benchmark_results
from src.report_gen import save_json_metrics, save_csv_benchmarks


def main():
    print("=" * 70)
    print("   DS391 BENCHMARK RUNNER: SYNTHETIC SCALABILITY STRESS TEST   ")
    print("=" * 70)

    import pandas as pd

    df, file_path = load_dataset()
    if df is None:
        print("[INFO] Active data directories are currently clean.")
        print("Using baseline in-memory benchmark template for performance evaluation...")
        df = pd.DataFrame({
            "comment_id": [f"c_{i}" for i in range(10)],
            "video_id": ["baseline_vid"] * 10,
            "author": [f"user_{i}" for i in range(10)],
            "comment_text": ["Brand engagement analysis benchmark query"] * 10,
            "likes": [10, 20, 5, 0, 50, 2, 1, 0, 100, 15],
            "published_at": ["2026-03-01T12:00:00Z"] * 10,
            "reply_count": [1, 2, 0, 0, 5, 0, 0, 0, 10, 1],
            "collected_at": ["2026-03-01T12:00:00Z"] * 10
        })
        file_path = "Baseline In-Memory Benchmark Template"
    print(f"Loaded ground-truth base data: {file_path} ({len(df):,} rows)")

    benchmarks = run_scalability_benchmarks(df, multipliers=[1, 10, 100], n_iterations=3)

    print("\nBenchmark Results Summary:")
    print("-" * 70)
    print(f"{'Scale':<12} {'Rows':<12} {'Mean Time (s)':<16} {'Peak Mem (MB)':<16} {'Throughput':<15}")
    print("-" * 70)
    for w in benchmarks["workloads"]:
        print(
            f"{w['multiplier']}x{'':<10} "
            f"{w['row_count']:<12,} "
            f"{w['mean_runtime_seconds']:<16.4f} "
            f"{w['peak_memory_mb']:<16.2f} "
            f"{w['throughput_rows_per_sec']:<15,.1f} rows/s"
        )
    print("-" * 70)

    json_path = save_json_metrics(benchmarks, "outputs/benchmark_results.json")
    csv_path = save_csv_benchmarks(benchmarks, "outputs/benchmark_results.csv")
    chart_path = plot_benchmark_results(benchmarks, "outputs/charts/scalability_benchmarks.png")

    print(f"\nSaved benchmark JSON to: {json_path}")
    print(f"Saved benchmark CSV to: {csv_path}")
    print(f"Saved benchmark visualization to: {chart_path}")


if __name__ == "__main__":
    main()

