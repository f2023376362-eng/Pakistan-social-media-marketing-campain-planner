"""
Dataset Inspection Module for YouTube Social Media Data.
Audits record volume, column schema, data types, null rates, and duplicates.
Supports both Video Metadata and Comment Telemetry formats.
"""

from typing import Any, Dict
import pandas as pd


def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs comprehensive structural inspection of a YouTube dataset.
    Returns:
    - total_rows, total_columns, column_names
    - column_inspection: data types, non-null counts, null percentages, distinct counts
    - duplicate analysis: full row duplicates, key field duplicates
    - memory footprint in bytes and megabytes
    """
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "total_columns": 0,
            "column_names": [],
            "column_inspection": {},
            "full_duplicate_rows": 0,
            "duplicate_comments_text": 0,
            "distinct_repeated_comments": 0,
            "duplicate_authors": 0,
            "duplicate_video_ids": 0,
            "memory_bytes": 0,
            "memory_mb": 0.0,
        }

    total_rows, total_cols = df.shape
    columns = list(df.columns)

    # Column-level data types and null audits
    column_info = {}
    for col in columns:
        null_count = int(df[col].isnull().sum())
        null_pct = float((null_count / total_rows) * 100) if total_rows > 0 else 0.0
        column_info[col] = {
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notnull().sum()),
            "null_count": null_count,
            "null_pct": round(null_pct, 3),
            "unique_values": int(df[col].nunique(dropna=True)),
        }

    # Duplicate audits
    full_duplicate_rows = int(df.duplicated().sum())

    # Text repetition audit (supports both comment_text and legacy comment)
    text_col = "comment_text" if "comment_text" in df.columns else ("comment" if "comment" in df.columns else None)
    if text_col:
        duplicate_comments_text = int(df.duplicated(subset=[text_col]).sum())
        distinct_repeated_comments = int((df[text_col].value_counts() > 1).sum())
    else:
        duplicate_comments_text = 0
        distinct_repeated_comments = 0

    duplicate_authors = int(df.duplicated(subset=["author"]).sum()) if "author" in df.columns else 0
    duplicate_video_ids = int(df.duplicated(subset=["video_id"]).sum()) if "video_id" in df.columns else 0

    memory_bytes = int(df.memory_usage(deep=True).sum())
    memory_mb = round(memory_bytes / (1024 * 1024), 3)

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "column_names": columns,
        "column_inspection": column_info,
        "full_duplicate_rows": full_duplicate_rows,
        "duplicate_comments_text": duplicate_comments_text,
        "distinct_repeated_comments": distinct_repeated_comments,
        "duplicate_authors": duplicate_authors,
        "duplicate_video_ids": duplicate_video_ids,
        "memory_bytes": memory_bytes,
        "memory_mb": memory_mb,
    }
