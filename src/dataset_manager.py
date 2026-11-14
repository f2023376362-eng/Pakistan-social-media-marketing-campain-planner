"""
Dataset Management & Session State Persistence Engine.
Manages in-memory state for YouTube Social Media Data Collection & Preprocessing.
Supports:
- Video metadata loading and validation
- Comment dataset loading and validation
- CSV and Excel file format decoding
- Flexible alias mapping
- Session reset and sample fallbacks
"""

import io
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import streamlit as st

from src.youtube_scraper import (
    VIDEO_SCHEMA_COLUMNS,
    COMMENT_SCHEMA_COLUMNS,
    BRAND_VIDEO_SCHEMA_COLUMNS,
    BRAND_COMMENT_SCHEMA_COLUMNS,
)
from src.cleaner import clean_comment_data, clean_video_metadata, clean_dataset


def load_file_buffer(uploaded_file) -> pd.DataFrame:
    """
    Decodes an uploaded Streamlit file buffer or file path into a pandas DataFrame.
    Supports CSV and Excel (.xlsx, .xls) files.
    """
    if uploaded_file is None:
        raise ValueError("No file provided.")

    fname = getattr(uploaded_file, "name", str(uploaded_file)).lower()

    if fname.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        # Standard CSV decode with utf-8-sig to handle BOM markers
        return pd.read_csv(uploaded_file, encoding="utf-8-sig")


def load_file_to_dataframe(file_buffer) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safe wrapper around load_file_buffer returning (df, error_message).
    """
    try:
        df = load_file_buffer(file_buffer)
        if df is None or df.empty:
            return None, "Error: File contains no rows or valid data."
        return df, None
    except Exception as e:
        return None, f"Error: {e}"


def get_bundled_youtube_sample() -> pd.DataFrame:
    """Returns sample comments or empty template."""
    p = Path("data/raw/comments/sample_comments.csv")
    if p.exists():
        return pd.read_csv(p)
    brand_p = list(Path("data/brand").glob("*comment*.csv")) if Path("data/brand").exists() else []
    if brand_p:
        return pd.read_csv(brand_p[0])
    return pd.DataFrame(columns=COMMENT_SCHEMA_COLUMNS)


def get_bundled_video_sample() -> pd.DataFrame:
    """Returns sample videos or empty template."""
    p = Path("data/raw/videos/sample_videos.csv")
    if p.exists():
        return pd.read_csv(p)
    brand_p = list(Path("data/brand").glob("*video*.csv")) if Path("data/brand").exists() else []
    if brand_p:
        return pd.read_csv(brand_p[0])
    return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS)


def validate_comment_dataset(df: pd.DataFrame) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates that a dataset contains comment telemetry fields.
    At minimum requires a recognizable textual comment column.
    """
    issues = []
    cols = [str(c).strip().lower() for c in df.columns]

    has_text = any(t in cols for t in ["comment_text", "comment", "text", "body", "textdisplay"])
    if not has_text:
        issues.append("Dataset lacks a recognizable comment text column (e.g., 'comment_text', 'comment', 'text').")

    stats = {
        "rows": len(df),
        "total_rows": len(df),
        "columns": list(df.columns),
        "has_author": any(a in cols for a in ["author", "author_name", "user"]),
        "has_likes": any(l in cols for l in ["likes", "like_count"]),
        "has_replies": any(r in cols for r in ["reply_count", "replies"]),
        "has_published": any(p in cols for p in ["published_at", "date", "timestamp"]),
        "has_brand": any(b in cols for b in ["brand_name", "brand"]),
        "has_platform": any(p in cols for p in ["platform", "channel_platform"]),
    }
    is_valid = len(issues) == 0
    return is_valid, issues, stats


# Compatibility alias
validate_youtube_dataset = validate_comment_dataset


def validate_video_dataset(df: pd.DataFrame) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates that a dataset contains video or post metadata fields.
    """
    issues = []
    cols = [str(c).strip().lower() for c in df.columns]

    has_id = any(i in cols for i in ["video_id", "post_id", "id"])
    has_title = any(t in cols for t in ["video_title", "title", "name", "caption"])

    if not has_id:
        issues.append("Dataset lacks a recognizable identifier column (e.g., 'video_id', 'post_id', or 'id').")
    if not has_title:
        issues.append("Dataset lacks a title or caption column (e.g., 'video_title', 'title', or 'name').")

    stats = {
        "rows": len(df),
        "columns": list(df.columns),
        "has_views": any(v in cols for v in ["view_count", "views"]),
        "has_likes": any(l in cols for l in ["like_count", "likes"]),
        "has_channel": any(c in cols for c in ["channel_title", "channel", "channel_name", "account_name"]),
        "has_brand": any(b in cols for b in ["brand_name", "brand"]),
        "has_platform": any(p in cols for p in ["platform", "channel_platform"]),
    }
    is_valid = len(issues) == 0
    return is_valid, issues, stats


def validate_brand_dataset(df: pd.DataFrame) -> Tuple[bool, str, List[str], Dict[str, Any]]:
    """
    Validates an incoming brand dataset, detecting whether it represents comments or post/video metadata.
    Returns: (is_valid, detected_type, issues, stats)
    """
    if df is None or df.empty:
        return False, "unknown", ["Dataset is empty."], {}

    cols = set(str(c).strip().lower() for c in df.columns)
    if any(t in cols for t in ["comment_text", "comment", "body"]):
        is_val, issues, stats = validate_comment_dataset(df)
        return is_val, "comments", issues, stats
    elif any(v in cols for v in ["video_title", "title", "caption", "views", "view_count"]):
        is_val, issues, stats = validate_video_dataset(df)
        return is_val, "videos", issues, stats
    else:
        return False, "unknown", ["Unrecognized dataset schema. Must contain comment text or video metadata."], {"columns": list(df.columns)}


def initialize_session_state():
    """
    Initializes Streamlit session state keys.
    Starts with empty/None state for brand datasets.
    """
    if "comments_data" not in st.session_state:
        st.session_state["comments_data"] = None
        st.session_state["comments_source"] = "No active brand comment dataset loaded"

    if "videos_data" not in st.session_state:
        st.session_state["videos_data"] = None
        st.session_state["videos_source"] = "No active brand video dataset loaded"

    if "brand_name" not in st.session_state:
        st.session_state["brand_name"] = "Audionic"

    if "platform" not in st.session_state:
        st.session_state["platform"] = "YouTube"

    if "data_source" not in st.session_state:
        st.session_state["data_source"] = "None"

    if "upload_filename" not in st.session_state:
        st.session_state["upload_filename"] = "None"

    if "collection_date" not in st.session_state:
        st.session_state["collection_date"] = None

    if "search_query" not in st.session_state:
        st.session_state["search_query"] = "Audionic Pakistan sound and audio reviews"

    if "cleaning_audit" not in st.session_state:
        st.session_state["cleaning_audit"] = None


def reset_session_state():
    """Resets session state to empty brand state."""
    st.session_state["comments_data"] = None
    st.session_state["videos_data"] = None
    st.session_state["data_source"] = "None"
    st.session_state["upload_filename"] = "None"
    st.session_state["collection_date"] = None
    st.session_state["cleaning_audit"] = None
    initialize_session_state()
