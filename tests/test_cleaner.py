"""
Test Suite for Data Cleaning & Standardization Engine.
Tests column mapping, duplicate detection, ISO 8601 UTC timestamp parsing,
numeric bounding, and empty-set resilience for comments and video metadata.
"""

import os
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.cleaner import (
    clean_comment_data,
    clean_video_metadata,
    clean_dataset,
    save_cleaned_dataset,
)
from src.youtube_scraper import VIDEO_SCHEMA_COLUMNS, COMMENT_SCHEMA_COLUMNS


def test_clean_comment_data_standards():
    raw_df = pd.DataFrame([
        {
            "id": "c100",
            "comment": "  Brilliant insights!  ",
            "author": "  Ali Khan ",
            "video_id": "v123",
            "like_count": "15",
            "total_reply_count": "-5",  # Negative count to test clip
            "published_at": "2026-02-10 14:00:00",
        },
        {
            # Exact duplicate ID to test deduplication
            "id": "c100",
            "comment": "Duplicate entry",
            "author": "Ali Khan",
            "video_id": "v123",
            "like_count": "10",
            "total_reply_count": "0",
            "published_at": "2026-02-10 14:00:00",
        },
        {
            "id": "c101",
            "comment": "Needs better data validation.",
            "author": "Sara Ahmed",
            "video_id": "v123",
            "like_count": "invalid_num",  # Coerced to 0
            "total_reply_count": "2",
            "published_at": "2026-02-11T09:30:00Z",
        }
    ])

    cleaned, metrics = clean_comment_data(raw_df)
    assert metrics["initial_rows"] == 3
    assert metrics["final_rows"] == 2
    assert metrics["dropped_duplicates"] == 1
    assert len(cleaned) == 2

    # Check column standardization
    for col in COMMENT_SCHEMA_COLUMNS:
        assert col in cleaned.columns

    # Check row 0 transformations
    row0 = cleaned[cleaned["comment_id"] == "c100"].iloc[0]
    assert row0["comment_text"] == "Brilliant insights!"
    assert row0["author"] == "Ali Khan"
    assert row0["likes"] == 15
    assert row0["reply_count"] == 0  # Clipped from -5 to 0
    assert "2026-02-10" in row0["published_at"]

    # Check row 1 coerced likes: unknown values preserved as NaN, not fabricated as 0
    row1 = cleaned[cleaned["comment_id"] == "c101"].iloc[0]
    assert pd.isna(row1["likes"])


def test_clean_comment_data_empty():
    cleaned, metrics = clean_comment_data(pd.DataFrame())
    assert metrics["final_rows"] == 0
    assert list(cleaned.columns) == COMMENT_SCHEMA_COLUMNS


def test_clean_video_metadata_standards():
    raw_videos = pd.DataFrame([
        {
            "id": "vid_pk_01",
            "title": "   Pakistan E-Commerce Boom 2026  ",
            "channel": "Business Insight PK",
            "description": "Analysis of online marketplace trends.",
            "views": "250000",
            "likes": "12000",
            "comments": "450",
            "published_at": "2026-01-01 12:00:00"
        },
        {
            # Duplicate video ID
            "id": "vid_pk_01",
            "title": "Pakistan E-Commerce Boom 2026 (Duplicate)",
            "channel": "Business Insight PK",
            "description": "Duplicated record",
            "views": "250000",
            "likes": "12000",
            "comments": "450",
            "published_at": "2026-01-01 12:00:00"
        }
    ])

    cleaned, metrics = clean_video_metadata(raw_videos)
    assert metrics["initial_rows"] == 2
    assert metrics["final_rows"] == 1
    assert metrics["dropped_duplicates"] == 1

    for col in VIDEO_SCHEMA_COLUMNS:
        assert col in cleaned.columns

    record = cleaned.iloc[0]
    assert record["video_id"] == "vid_pk_01"
    assert record["video_title"] == "Pakistan E-Commerce Boom 2026"
    assert record["view_count"] == 250000
    assert "youtube.com/watch?v=vid_pk_01" in record["video_url"]


def test_clean_dataset_polymorphic_dispatcher():
    comment_df = pd.DataFrame({"comment_text": ["Test"], "author": ["User"]})
    res_c, m_c = clean_dataset(comment_df)
    assert m_c["dataset_type"] == "comments"

    video_df = pd.DataFrame({"video_title": ["Video Title"], "channel_title": ["Channel"]})
    res_v, m_v = clean_dataset(video_df)
    assert m_v["dataset_type"] == "videos"


def test_save_cleaned_dataset(tmp_path):
    out_file = tmp_path / "subdir" / "test_out.csv"
    sample_df = pd.DataFrame({"col_a": [1, 2], "col_b": ["x", "y"]})
    saved = save_cleaned_dataset(sample_df, out_file)
    assert saved.exists()
    loaded = pd.read_csv(saved)
    assert len(loaded) == 2
