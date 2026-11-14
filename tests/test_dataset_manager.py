"""
Test Suite for Dataset Management System.
Tests CSV and Excel ingestion, invalid file handling, schema validation,
brand dataset upload validation, provenance preservation, and empty directory resilience.
"""

import io
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.dataset_manager import (
    load_file_buffer,
    load_file_to_dataframe,
    validate_comment_dataset,
    validate_video_dataset,
    validate_brand_dataset,
    initialize_session_state,
    reset_session_state,
    get_bundled_youtube_sample,
    get_bundled_video_sample,
)
from src.youtube_scraper import (
    VIDEO_SCHEMA_COLUMNS,
    COMMENT_SCHEMA_COLUMNS,
    BRAND_VIDEO_SCHEMA_COLUMNS,
    BRAND_COMMENT_SCHEMA_COLUMNS,
)


def test_load_csv_from_buffer():
    csv_bytes = b"comment_text,likes,reply_count\nGreat pipeline,100,5\nRobust code,50,2\n"
    buffer = io.BytesIO(csv_bytes)
    setattr(buffer, "name", "test.csv")
    df, err = load_file_to_dataframe(buffer)
    assert err is None
    assert len(df) == 2
    assert "comment_text" in df.columns


def test_load_excel_from_buffer():
    df_orig = pd.DataFrame({"video_id": ["v1", "v2"], "video_title": ["Audionic Review", "Zero Lifestyle Trends"]})
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        df_orig.to_excel(writer, index=False)
    excel_buf.seek(0)
    setattr(excel_buf, "name", "test.xlsx")

    df, err = load_file_to_dataframe(excel_buf)
    assert err is None
    assert len(df) == 2
    assert "video_id" in df.columns


def test_invalid_empty_file():
    buf = io.BytesIO(b"")
    setattr(buf, "name", "empty.csv")
    df, err = load_file_to_dataframe(buf)
    assert df is None
    assert "error" in str(err).lower() or "no rows" in str(err).lower()


def test_validate_comment_dataset():
    valid_df = pd.DataFrame({
        "platform": ["YouTube"],
        "brand_name": ["Audionic"],
        "comment_id": ["c1"],
        "comment_text": ["Test comment text"],
        "author": ["User1"],
        "likes": [10],
        "reply_count": [2]
    })
    is_valid, issues, stats = validate_comment_dataset(valid_df)
    assert is_valid is True
    assert len(issues) == 0
    assert stats["rows"] == 1
    assert stats["has_likes"] is True
    assert stats["has_brand"] is True

    invalid_df = pd.DataFrame({"random_col": [1, 2, 3]})
    is_valid2, issues2, stats2 = validate_comment_dataset(invalid_df)
    assert is_valid2 is False
    assert len(issues2) > 0


def test_validate_video_dataset():
    valid_df = pd.DataFrame({
        "platform": ["YouTube"],
        "brand_name": ["Audionic"],
        "video_id": ["abc12345678"],
        "video_title": ["Audionic Earbuds Launch"],
        "channel_title": ["Audionic Pakistan"],
        "view_count": [1000]
    })
    is_valid, issues, stats = validate_video_dataset(valid_df)
    assert is_valid is True
    assert stats["has_views"] is True
    assert stats["has_brand"] is True

    invalid_df = pd.DataFrame({"some_metric": [100]})
    is_valid2, issues2, _ = validate_video_dataset(invalid_df)
    assert is_valid2 is False
    assert any("identifier" in i.lower() or "video_id" in i.lower() for i in issues2)


def test_validate_brand_dataset_dispatcher():
    # Brand comments
    brand_comments = pd.DataFrame({
        "platform": ["YouTube"],
        "brand_name": ["Zero Lifestyle"],
        "video_id": ["vid_001"],
        "comment_id": ["c_101"],
        "comment_text": ["Smartwatch battery life is impressive."],
        "author": ["TechReviewerPK"],
        "likes": [25],
        "reply_count": [3]
    })
    is_val, dtype, issues, _ = validate_brand_dataset(brand_comments)
    assert is_val is True
    assert dtype == "comments"

    # Brand videos
    brand_videos = pd.DataFrame({
        "platform": ["YouTube"],
        "brand_name": ["Zero Lifestyle"],
        "video_id": ["vid_001"],
        "video_title": ["Zero Lifestyle Luna Smartwatch Unboxing"],
        "views": [50000],
        "likes": [1200]
    })
    is_val_v, dtype_v, issues_v, _ = validate_brand_dataset(brand_videos)
    assert is_val_v is True
    assert dtype_v == "videos"


def test_empty_directories_do_not_crash_manager():
    # When active data dirs are empty, sample getters return clean schema templates
    c_df = get_bundled_youtube_sample()
    assert isinstance(c_df, pd.DataFrame)
    for col in COMMENT_SCHEMA_COLUMNS:
        assert col in c_df.columns

    v_df = get_bundled_video_sample()
    assert isinstance(v_df, pd.DataFrame)
    for col in VIDEO_SCHEMA_COLUMNS:
        assert col in v_df.columns


def test_missing_values_are_preserved():
    # Verification that null/missing values are not converted to genuine zeros
    raw_with_nulls = pd.DataFrame({
        "comment_id": ["c1", "c2"],
        "comment_text": ["Comment with known metrics", "Comment with unknown metrics"],
        "author": ["UserA", "UserB"],
        "likes": [15, None],
        "reply_count": [2, np.nan],
    })
    from src.cleaner import clean_comment_data
    cleaned, _ = clean_comment_data(raw_with_nulls)
    # Row 0 likes was 15 -> should remain 15
    assert cleaned.iloc[0]["likes"] == 15
    # Row 1 likes was None -> must NOT be fabricated into 0
    assert pd.isna(cleaned.iloc[1]["likes"])
    assert pd.isna(cleaned.iloc[1]["reply_count"])
