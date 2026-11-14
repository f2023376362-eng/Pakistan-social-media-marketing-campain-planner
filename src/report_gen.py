"""
Report Generation Module for YouTube Social Media Data Collection & Preprocessing.
Compiles data collection summaries, cleaning audit logs, descriptive statistics,
and analytical metrics into Markdown and JSON reports.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd


def save_json_metrics(
    data: Dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Saves dictionary metrics to formatted JSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out


def save_csv_benchmarks(
    benchmarks: Dict[str, Any],
    output_path: str | Path = "outputs/benchmark_results.csv",
) -> Path:
    """Exports benchmark workloads to a clean CSV file."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    workloads = benchmarks.get("workloads", [])
    df_bm = pd.DataFrame(workloads)
    df_bm.to_csv(out, index=False, encoding="utf-8")
    return out


def generate_pipeline_report(
    inspection: Optional[Dict[str, Any]] = None,
    cleaning_metrics: Optional[Dict[str, Any]] = None,
    statistics: Optional[Dict[str, Any]] = None,
    temporal: Optional[Dict[str, Any]] = None,
    text_data: Optional[Dict[str, Any]] = None,
    sentiment: Optional[Dict[str, Any]] = None,
    dataset_name: str = "YouTube Data Collection",
    output_path: Optional[str | Path] = None,
    comments_df: Optional[pd.DataFrame] = None,
    videos_df: Optional[pd.DataFrame] = None,
    cleaning_audit: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a formal Markdown report summarizing dataset collection, cleaning, and engagement metrics.
    Supports either precomputed analysis dictionaries or raw DataFrames.
    """
    from src.inspection import inspect_dataset
    from src.statistics import calculate_descriptive_statistics
    from src.text_temporal import analyze_temporal, analyze_text

    cleaning_metrics = cleaning_metrics or cleaning_audit or {}

    if inspection is None:
        target_df = comments_df if comments_df is not None else videos_df
        if target_df is not None and not target_df.empty:
            inspection = inspect_dataset(target_df)
            statistics = statistics or calculate_descriptive_statistics(target_df)
            temporal = temporal or analyze_temporal(target_df)
            text_data = text_data or analyze_text(target_df)
        else:
            inspection = {}

    statistics = statistics or {}
    temporal = temporal or {}
    text_data = text_data or {}

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    likes_info = statistics.get("likes", {}) if statistics else {}
    replies_info = statistics.get("reply_count", {}) if statistics else {}
    gini_likes = likes_info.get("gini_coefficient", "N/A")

    cleaning_block = ""
    if cleaning_metrics:
        cleaning_block = f"""
## 2. Data Cleaning & Integrity Audit
- **Initial Record Count:** `{cleaning_metrics.get('initial_rows', 0):,}`
- **Cleaned Record Count:** `{cleaning_metrics.get('final_rows', 0):,}`
- **Exact Duplicate Rows Dropped:** `{cleaning_metrics.get('dropped_duplicates', 0):,}`
- **Legitimate Repeated Texts Preserved:** `{cleaning_metrics.get('repeated_comment_texts', 0):,}`
- **Unique Authors:** `{cleaning_metrics.get('unique_authors', 'N/A')}`
"""

    sentiment_block = ""
    if sentiment and sentiment.get("total_comments", 0) > 0:
        sentiment_block = f"""
## 5. Supporting Sentiment Analysis (Optional Module)
- **Positive Comments:** `{sentiment.get('positive_pct', 0)}%` ({sentiment.get('positive_count', 0):,} records)
- **Neutral Comments:** `{sentiment.get('neutral_pct', 0)}%` ({sentiment.get('neutral_count', 0):,} records)
- **Negative Comments:** `{sentiment.get('negative_pct', 0)}%` ({sentiment.get('negative_count', 0):,} records)
- **Mean Lexicon Polarity:** `{sentiment.get('mean_polarity', 0.0)}`
- *Method:* Rule-based lexical matching with negation inversion (exploratory indicator).
"""

    report_content = f"""# YouTube Social Media Data Collection & Preprocessing Report

## Executive Summary
This report documents the collection, validation, cleaning, and statistical profiling of YouTube social data.
The pipeline provides standardized data foundations for multi-channel audience and campaign intelligence.

- **Dataset Target:** `{dataset_name}`
- **Generation Timestamp:** `{now_str}`
- **Analyzed Rows:** `{inspection.get('total_rows', 0):,}`
- **Total Columns:** `{inspection.get('total_columns', 0)}`

---

## 1. Structural Inspection
- **Column Schema:** `{', '.join(inspection.get('column_names', []))}`
- **Memory Footprint:** `{inspection.get('memory_mb', 0.0):.2f} MB`
- **Duplicate Rows Detected:** `{inspection.get('full_duplicate_rows', 0)}`
{cleaning_block}
## 3. Engagement & Attention Inequality
- **Mean Likes:** `{likes_info.get('mean', 'N/A')}` | **Median Likes:** `{likes_info.get('median', 'N/A')}` | **Max Likes:** `{likes_info.get('max', 'N/A')}`
- **Gini Coefficient ($G$):** `{gini_likes}` (High value indicates extreme Pareto inequality in engagement)
- **Top 1% Engagement Share:** `{likes_info.get('top_1_pct_share', 'N/A')}%`
- **Mean Replies:** `{replies_info.get('mean', 'N/A')}` | **Median Replies:** `{replies_info.get('median', 'N/A')}`

## 4. Temporal Pacing & Vocabulary
- **Timeline Span:** `{temporal.get('earliest_comment_utc', 'N/A')} to {temporal.get('latest_comment_utc', 'N/A')} ({temporal.get('total_span_days', 0)} days)`
- **Total Words Analyzed:** `{text_data.get('word_count', {}).get('mean', 'N/A')} avg words/comment`
- **Comments with Emojis:** `{text_data.get('expression_counts', {}).get('emoji_pct', 0)}%`
{sentiment_block}
---
*Report automatically compiled by YouTube Social Media Data Collection & Preprocessing Pipeline.*
"""

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(report_content)

    return report_content
