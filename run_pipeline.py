"""
Main Execution Script for YouTube Social Media Data Collection & Preprocessing.
Executes data loading, inspection, cleaning, descriptive statistics,
temporal pacing, lexical analysis, synthetic benchmarking, and report generation.
"""

import io
import os
import sys
import tempfile
from pathlib import Path

# Force UTF-8 stdout for Windows console emoji support
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Writable directory for matplotlib
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

from src.loader import load_dataset
from src.cleaner import clean_comment_data, save_cleaned_dataset
from src.inspection import inspect_dataset
from src.statistics import calculate_descriptive_statistics
from src.text_temporal import analyze_temporal, analyze_text
from src.sentiment_engine import analyze_youtube_sentiment
from src.visualizer import (
    plot_engagement_distribution,
    plot_temporal_trends,
    plot_text_analysis,
    plot_benchmark_results,
)
from src.benchmark import run_scalability_benchmarks
from src.report_gen import save_json_metrics, save_csv_benchmarks, generate_pipeline_report


def main():
    print("=" * 75)
    print("   YOUTUBE SOCIAL MEDIA DATA COLLECTION & PREPROCESSING PIPELINE   ")
    print("=" * 75)

    # 1. Discover and Load Dataset
    print("\n[Step 1/7] Discovering and loading dataset from data/...")
    try:
        df, file_path = load_dataset(prefer_processed=False)
        if df is None:
            print("  --> [INFO] Active data directories (data/raw/, data/processed/, data/brand/) are clean.")
            print("  --> Ready for brand-related social data collection via YouTube API or UI upload.")
            print("\n" + "=" * 75)
            print("   PIPELINE READY FOR BRAND DATA INGESTION   ")
            print("=" * 75)
            return
        print(f"  --> Successfully loaded dataset: {file_path}")
        print(f"  --> Dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    except Exception as e:
        print(f"  [ERROR] Failed to load dataset: {e}")
        sys.exit(1)

    # 2. Structural Inspection
    print("\n[Step 2/7] Inspecting schema, missing values, and duplicates...")
    inspection = inspect_dataset(df)
    print(f"  --> Total Rows: {inspection['total_rows']:,}")
    print(f"  --> Total Columns: {inspection['total_columns']} -> {inspection['column_names']}")
    print(f"  --> Full Duplicate Rows: {inspection['full_duplicate_rows']}")
    print(f"  --> Memory Footprint: {inspection['memory_mb']:.2f} MB")

    # 3. Data Cleaning
    print("\n[Step 3/7] Standardizing schema and cleaning text...")
    cleaned_df, cleaning_metrics = clean_comment_data(df)
    print(f"  --> Cleaned Rows: {cleaning_metrics['final_rows']:,} (Dropped {cleaning_metrics['dropped_duplicates']} duplicates)")
    save_cleaned_dataset(cleaned_df, "data/processed/comments/cleaned_comments.csv")

    # 4. Descriptive Statistics & Inequality
    print("\n[Step 4/7] Calculating engagement statistics and Gini inequality...")
    stats = calculate_descriptive_statistics(cleaned_df)
    if "likes" in stats:
        likes_s = stats["likes"]
        print(f"  --> Likes: Mean={likes_s['mean']}, Median={likes_s['median']}, Gini (G)={likes_s['gini_coefficient']}")
    if "reply_count" in stats:
        rep_s = stats["reply_count"]
        print(f"  --> Replies: Mean={rep_s['mean']}, Median={rep_s['median']}, Gini (G)={rep_s['gini_coefficient']}")

    # 5. Temporal and Text Analysis
    print("\n[Step 5/7] Performing temporal pacing and lexical tokenization...")
    temporal = analyze_temporal(cleaned_df)
    text_data = analyze_text(cleaned_df)
    print(f"  --> Timeline: {temporal.get('earliest_comment_utc', 'N/A')} to {temporal.get('latest_comment_utc', 'N/A')}")
    top_kw = [k['keyword'] for k in text_data.get('top_keywords', [])[:5]]
    print(f"  --> Top Frequent Keywords: {', '.join(top_kw)}")

    # Optional Sentiment Check
    _, sent_sum = analyze_youtube_sentiment(cleaned_df)
    if sent_sum.get("total_comments", 0) > 0:
        print(f"  --> Sentiment: {sent_sum['positive_pct']}% Positive, {sent_sum['neutral_pct']}% Neutral, {sent_sum['negative_pct']}% Negative")

    # 6. Scalability Benchmarking
    print("\n[Step 6/7] Running synthetic scalability benchmarking (1x, 10x, 100x workloads)...")
    benchmarks = run_scalability_benchmarks(cleaned_df, multipliers=[1, 10, 100], n_iterations=3)
    for w in benchmarks["workloads"]:
        print(f"  --> {w['scale_label']}: {w['mean_runtime_seconds']:.4f}s | Peak Mem: {w['peak_memory_mb']:.2f} MB | {w['throughput_rows_per_sec']:,.1f} rows/s")

    # 7. Visualization & Report Generation
    print("\n[Step 7/7] Generating output charts and Markdown pipeline report...")
    os.makedirs("outputs/charts", exist_ok=True)
    c1 = plot_engagement_distribution(cleaned_df, "outputs/charts/likes_replies_distribution.png")
    c2 = plot_temporal_trends(cleaned_df, temporal, "outputs/charts/temporal_activity_trends.png")
    c3 = plot_text_analysis(text_data, "outputs/charts/top_keyword_frequency.png")
    c4 = plot_benchmark_results(benchmarks, "outputs/charts/scalability_benchmarks.png")

    summary_metrics = {
        "inspection": inspection,
        "cleaning": cleaning_metrics,
        "statistics": stats,
        "temporal": temporal,
        "text": text_data,
        "sentiment": sent_sum
    }
    j1 = save_json_metrics(summary_metrics, "outputs/summary_metrics.json")
    j2 = save_json_metrics(benchmarks, "outputs/benchmark_results.json")
    c_bm = save_csv_benchmarks(benchmarks, "outputs/benchmark_results.csv")

    rep_path = "outputs/pipeline_audit_report.md"
    generate_pipeline_report(
        inspection=inspection,
        cleaning_metrics=cleaning_metrics,
        statistics=stats,
        temporal=temporal,
        text_data=text_data,
        sentiment=sent_sum,
        dataset_name=str(file_path),
        output_path=rep_path
    )
    print(f"  --> Metrics JSON: {j1}")
    print(f"  --> Benchmarks JSON: {j2}")
    print(f"  --> Pipeline Report: {rep_path}")
    print("\n" + "=" * 75)
    print("   PIPELINE EXECUTION COMPLETED SUCCESSFULLY   ")
    print("=" * 75)


if __name__ == "__main__":
    main()
