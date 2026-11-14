"""
Reusable Data Cleaning & Standardization Engine for YouTube Social Media Data.
Standardizes and cleans raw video metadata and comment datasets without mutating raw source files.
Enforces the standardized schemas:
1. Video Metadata Schema (video_id, video_title, channel_id, view_count, etc.)
2. Comment Telemetry Schema (comment_id, video_id, author, comment_text, likes, etc.)
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

from src.youtube_scraper import VIDEO_SCHEMA_COLUMNS, COMMENT_SCHEMA_COLUMNS


def clean_comment_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw YouTube comment dataset according to project standards:
    1. Standardizes column names (maps legacy aliases like 'comment' -> 'comment_text').
    2. Strips leading/trailing whitespace and normalizes text fields.
    3. Safely parses ISO 8601 UTC publication and collection timestamps.
    4. Converts likes and reply_count to non-negative integers.
    5. Deduplicates by comment_id if present, or evaluates multi-column row identity,
       preserving legitimate repeated comments across different authors or timestamps.
    6. Returns (cleaned_df, cleaning_audit_metrics).
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=COMMENT_SCHEMA_COLUMNS), {
            "initial_rows": 0,
            "final_rows": 0,
            "dropped_duplicates": 0,
            "repeated_comment_texts": 0,
            "missing_values": {}
        }

    clean_df = df.copy()
    initial_rows = len(clean_df)

    # Standardize column headers
    clean_df.columns = [str(c).strip().lower().replace(" ", "_") for c in clean_df.columns]

    had_comment_id = "comment_id" in clean_df.columns or "id" in clean_df.columns

    # Handle common field name aliases
    alias_map = {
        "comment": "comment_text",
        "text": "comment_text",
        "textdisplay": "comment_text",
        "body": "comment_text",
        "like_count": "likes",
        "total_reply_count": "reply_count",
        "id": "comment_id",
        "post_id": "video_id",
        "post": "video_id",
        "channel_name": "channel_title",
        "account_name": "channel_title",
        "source_url": "video_url",
    }
    for old_col, new_col in alias_map.items():
        if old_col in clean_df.columns and new_col not in clean_df.columns:
            clean_df = clean_df.rename(columns={old_col: new_col})

    # Ensure required textual columns exist, imputing standard defaults
    if "comment_text" not in clean_df.columns:
        clean_df["comment_text"] = ""
    if "author" not in clean_df.columns:
        clean_df["author"] = "Anonymous"
    if "video_id" not in clean_df.columns:
        clean_df["video_id"] = "unknown"
    if "comment_id" not in clean_df.columns:
        clean_df["comment_id"] = ""

    # Brand and platform attributes
    if "platform" not in clean_df.columns:
        clean_df["platform"] = "YouTube"
    if "brand_name" not in clean_df.columns:
        clean_df["brand_name"] = None

    # 1. Whitespace and text normalization
    clean_df["comment_text"] = clean_df["comment_text"].fillna("").astype(str).str.strip()
    clean_df["author"] = clean_df["author"].fillna("Anonymous").astype(str).str.strip()
    clean_df["video_id"] = clean_df["video_id"].fillna("unknown").astype(str).str.strip()
    clean_df["comment_id"] = clean_df["comment_id"].fillna("").astype(str).str.strip()

    # 2. Preserve missing values: do NOT fabricate zeros; clip existing numbers to non-negative
    if "likes" in clean_df.columns:
        num_likes = pd.to_numeric(clean_df["likes"], errors="coerce")
        clean_df["likes"] = num_likes.where(num_likes.isna(), num_likes.clip(lower=0))
    else:
        clean_df["likes"] = np.nan

    if "reply_count" in clean_df.columns:
        num_replies = pd.to_numeric(clean_df["reply_count"], errors="coerce")
        clean_df["reply_count"] = num_replies.where(num_replies.isna(), num_replies.clip(lower=0))
    else:
        clean_df["reply_count"] = np.nan

    # 3. Parse publication timestamp to ISO 8601 UTC
    if "published_at" in clean_df.columns:
        parsed_pub = pd.to_datetime(clean_df["published_at"], errors="coerce", utc=True)
        clean_df["published_at"] = parsed_pub.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
    else:
        clean_df["published_at"] = ""

    # 4. Parse collection timestamp
    if "collected_at" in clean_df.columns:
        parsed_col = pd.to_datetime(clean_df["collected_at"], errors="coerce", utc=True)
        clean_df["collected_at"] = parsed_col.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
    else:
        clean_df["collected_at"] = ""

    # 5. Deduplication
    # If genuine comment_id exists and is non-empty for rows, deduplicate by comment_id
    has_valid_ids = had_comment_id and ((clean_df["comment_id"] != "").sum() > (len(clean_df) * 0.5))
    if has_valid_ids:
        dropped_duplicates = int(clean_df.duplicated(subset=["comment_id"]).sum())
        clean_df = clean_df.drop_duplicates(subset=["comment_id"]).reset_index(drop=True)
    else:
        # Deduplicate based on author + text + published_at or entire row identity
        content_cols = [c for c in ["comment_text", "author", "published_at"] if c in clean_df.columns]
        if content_cols:
            dropped_duplicates = int(clean_df.duplicated(subset=content_cols).sum())
            clean_df = clean_df.drop_duplicates(subset=content_cols).reset_index(drop=True)
        else:
            dropped_duplicates = int(clean_df.duplicated().sum())
            clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    # Ensure comment_id is populated for all retained rows
    clean_df["comment_id"] = [
        val if val else f"c_{i}" for i, val in enumerate(clean_df["comment_id"])
    ]

    final_rows = len(clean_df)

    # Reorder columns to standard schema, retaining any extra custom columns at the end
    standard_cols = [c for c in COMMENT_SCHEMA_COLUMNS if c in clean_df.columns]
    extra_cols = [c for c in clean_df.columns if c not in standard_cols]
    clean_df = clean_df[standard_cols + extra_cols]

    metrics = {
        "dataset_type": "comments",
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "dropped_duplicates": dropped_duplicates,
        "repeated_comment_texts": int(clean_df.duplicated(subset=["comment_text"]).sum()),
        "unique_authors": int(clean_df["author"].nunique()),
        "missing_values": clean_df.isnull().sum().to_dict()
    }
    return clean_df, metrics


def clean_video_metadata(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw YouTube video metadata dataset:
    1. Standardizes column names to VIDEO_SCHEMA_COLUMNS.
    2. Trims whitespace from titles, descriptions, and channel fields.
    3. Parses publication and collection dates to ISO 8601 UTC.
    4. Validates view, like, and comment counts as nullable numeric integers.
    5. Deduplicates records by video_id.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), {
            "initial_rows": 0,
            "final_rows": 0,
            "dropped_duplicates": 0,
            "missing_values": {}
        }

    clean_df = df.copy()
    initial_rows = len(clean_df)

    clean_df.columns = [str(c).strip().lower().replace(" ", "_") for c in clean_df.columns]

    alias_map = {
        "id": "video_id",
        "post_id": "video_id",
        "title": "video_title",
        "description": "video_description",
        "channel": "channel_title",
        "channel_name": "channel_title",
        "account_name": "channel_title",
        "views": "view_count",
        "likes": "like_count",
        "comments": "comment_count",
        "comments_count": "comment_count",
        "url": "video_url",
        "source_url": "video_url",
    }
    for old_col, new_col in alias_map.items():
        if old_col in clean_df.columns and new_col not in clean_df.columns:
            clean_df = clean_df.rename(columns={old_col: new_col})

    # Ensure required columns exist
    for col in ["video_id", "video_title", "channel_title", "video_description", "channel_id"]:
        if col not in clean_df.columns:
            clean_df[col] = ""

    # Brand and platform attributes
    if "platform" not in clean_df.columns:
        clean_df["platform"] = "YouTube"
    if "brand_name" not in clean_df.columns:
        clean_df["brand_name"] = None

    # Normalization
    clean_df["video_id"] = clean_df["video_id"].fillna("").astype(str).str.strip()
    clean_df["video_title"] = clean_df["video_title"].fillna("").astype(str).str.strip()
    clean_df["video_description"] = clean_df["video_description"].fillna("").astype(str).str.strip()
    clean_df["channel_title"] = clean_df["channel_title"].fillna("").astype(str).str.strip()
    clean_df["channel_id"] = clean_df["channel_id"].fillna("").astype(str).str.strip()

    # Video URL and source URL
    clean_df["video_url"] = clean_df["video_id"].apply(
        lambda v: f"https://www.youtube.com/watch?v={v}" if v else ""
    )
    clean_df["source_url"] = clean_df["video_url"]
    clean_df["channel_name"] = clean_df["channel_title"]

    # Numeric counts: preserve nulls appropriately and clip non-negative
    for metric in ["view_count", "like_count", "comment_count"]:
        if metric in clean_df.columns:
            num_val = pd.to_numeric(clean_df[metric], errors="coerce")
            clean_df[metric] = num_val.where(num_val.isna(), num_val.clip(lower=0))
        else:
            clean_df[metric] = np.nan

    # Synchronize brand alias columns
    clean_df["views"] = clean_df["view_count"]
    clean_df["likes"] = clean_df["like_count"]
    clean_df["comments_count"] = clean_df["comment_count"]

    # Timestamps
    for date_col in ["published_at", "collected_at"]:
        if date_col in clean_df.columns:
            parsed = pd.to_datetime(clean_df[date_col], errors="coerce", utc=True)
            clean_df[date_col] = parsed.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
        else:
            clean_df[date_col] = ""

    # Deduplicate by video_id
    dropped_duplicates = int(clean_df.duplicated(subset=["video_id"]).sum())
    clean_df = clean_df.drop_duplicates(subset=["video_id"]).reset_index(drop=True)
    final_rows = len(clean_df)

    # Standard column ordering
    standard_cols = [c for c in VIDEO_SCHEMA_COLUMNS if c in clean_df.columns]
    extra_cols = [c for c in clean_df.columns if c not in standard_cols]
    clean_df = clean_df[standard_cols + extra_cols]

    metrics = {
        "dataset_type": "videos",
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "dropped_duplicates": dropped_duplicates,
        "missing_values": clean_df.isnull().sum().to_dict()
    }
    return clean_df, metrics


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Polymorphic dispatcher: inspects columns to route to video or comment cleaner.
    """
    if df is None or df.empty:
        return df, {"initial_rows": 0, "final_rows": 0, "dropped_duplicates": 0}

    cols = set(str(c).strip().lower() for c in df.columns)
    if "video_title" in cols or "channel_title" in cols or "view_count" in cols:
        return clean_video_metadata(df)
    return clean_comment_data(df)


def save_cleaned_dataset(df: pd.DataFrame, output_path: str | Path) -> Path:
    """Saves cleaned DataFrame to destination CSV, creating parent directories if needed."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False, encoding="utf-8")
    return p


def main():
    """
    CLI Entrypoint for data cleaning. Cleans raw comments and videos datasets.
    """
    print("=" * 70)
    print("   YOUTUBE DATA CLEANING & STANDARDIZATION ENGINE   ")
    print("=" * 70)

    # 1. Discover raw comments
    raw_comments_dir = Path("data/raw/comments")
    comment_files = list(raw_comments_dir.glob("*.csv")) if raw_comments_dir.exists() else []

    if comment_files:
        for f in comment_files:
            raw_comments = pd.read_csv(f)
            cleaned_comments, c_metrics = clean_comment_data(raw_comments)
            out_c = save_cleaned_dataset(cleaned_comments, f"data/processed/comments/cleaned_{f.name}")
            print(f"\n[Comments] Cleaned {f.name}: {c_metrics['initial_rows']:,} -> {c_metrics['final_rows']:,} rows")
            print(f"  - Dropped duplicates: {c_metrics['dropped_duplicates']}")
            print(f"  - Saved to: {out_c}")
    else:
        print("\n[Comments] No raw comment CSV files found in data/raw/comments/ (directory is ready for brand data).")

    # 2. Discover raw videos
    raw_videos_dir = Path("data/raw/videos")
    video_files = list(raw_videos_dir.glob("*.csv")) if raw_videos_dir.exists() else []

    if video_files:
        for f in video_files:
            raw_videos = pd.read_csv(f)
            cleaned_videos, v_metrics = clean_video_metadata(raw_videos)
            out_v = save_cleaned_dataset(cleaned_videos, f"data/processed/videos/cleaned_{f.name}")
            print(f"\n[Videos] Cleaned {f.name}: {v_metrics['initial_rows']:,} -> {v_metrics['final_rows']:,} rows")
            print(f"  - Dropped duplicates: {v_metrics['dropped_duplicates']}")
            print(f"  - Saved to: {out_v}")
    else:
        print("\n[Videos] No raw video CSV files found in data/raw/videos/ (directory is ready for brand data).")

    # 3. Discover brand folder data
    brand_dir = Path("data/brand")
    brand_files = list(brand_dir.glob("*.csv")) if brand_dir.exists() else []
    if brand_files:
        for f in brand_files:
            brand_df = pd.read_csv(f)
            cleaned_b, b_metrics = clean_dataset(brand_df)
            out_b = save_cleaned_dataset(cleaned_b, f"data/processed/cleaned_{f.name}")
            print(f"\n[Brand] Cleaned {f.name}: {b_metrics['initial_rows']:,} -> {b_metrics['final_rows']:,} rows")
            print(f"  - Saved to: {out_b}")
    else:
        print("\n[Brand] data/brand/ is currently clean and ready for genuine brand dataset imports.")

    print("\n" + "=" * 70)
    print("   DATA CLEANING COMPLETE")
    print("=" * 70)

