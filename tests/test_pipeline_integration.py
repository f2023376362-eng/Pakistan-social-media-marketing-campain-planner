"""
Test Suite for End-to-End Pipeline Integration and Loader Utilities.
Tests dataset loader, report generator, archive isolation, and empty directory behavior.
"""

from pathlib import Path
import pytest
import pandas as pd

from src.loader import discover_datasets, load_dataset, find_target_csv
from src.report_gen import generate_pipeline_report, save_json_metrics, save_csv_benchmarks


def test_loader_discover_datasets_ignores_archive():
    discovery = discover_datasets("data")
    assert "raw_videos" in discovery
    assert "raw_comments" in discovery
    assert "processed_videos" in discovery
    assert "processed_comments" in discovery
    assert "brand_datasets" in discovery
    assert "all_csvs" in discovery
    # Crucial test: Ensure archive/ is NEVER discovered or mixed into active datasets
    for p in discovery["all_csvs"]:
        assert "archive" not in str(p).lower()


def test_loader_empty_directories_return_none():
    # In clean state with sample files removed, load_dataset returns (None, None) gracefully
    df_c, p_c = load_dataset(dataset_type="comments")
    if p_c is None:
        assert df_c is None
    else:
        # If user placed data in data/brand or data/raw
        assert isinstance(df_c, pd.DataFrame)

    df_v, p_v = load_dataset(dataset_type="videos")
    if p_v is None:
        assert df_v is None
    else:
        assert isinstance(df_v, pd.DataFrame)


def test_loader_explicit_file_loading(tmp_path):
    test_file = tmp_path / "brand_comments.csv"
    test_df = pd.DataFrame({
        "platform": ["YouTube"],
        "brand_name": ["Audionic"],
        "comment_id": ["c1"],
        "comment_text": ["Great earphones"],
        "likes": [5]
    })
    test_df.to_csv(test_file, index=False)

    loaded_df, loaded_path = load_dataset(file_path=test_file)
    assert loaded_df is not None
    assert len(loaded_df) == 1
    assert loaded_path == test_file


def test_archived_music_datasets_not_automatically_loaded():
    # Guarantee that music datasets in archive/ are not loaded by default
    df, p = load_dataset(dataset_type="comments")
    if p is not None:
        assert "archive" not in str(p).lower()
        text_dump = df.to_string().lower()
        for forbidden in ["gali gali", "high heels", "neha kakkar", "meet bros"]:
            assert forbidden not in text_dump


def test_report_gen_markdown_generation():
    comments_df = pd.DataFrame({
        "comment_id": ["c1", "c2"],
        "comment_text": ["Great progress", "Needs improvement"],
        "likes": [10, 2],
        "reply_count": [1, 0],
        "published_at": ["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]
    })
    videos_df = pd.DataFrame({
        "video_id": ["v1"],
        "video_title": ["Audionic Showcase"],
        "view_count": [1000],
        "like_count": [50],
        "comment_count": [5]
    })
    audit_metrics = {
        "initial_rows": 2,
        "final_rows": 2,
        "dropped_duplicates": 0
    }
    report = generate_pipeline_report(
        comments_df=comments_df,
        videos_df=videos_df,
        cleaning_audit=audit_metrics,
        dataset_name="Audionic Brand Social Analytics"
    )
    assert "# YouTube Social Media Data Collection & Preprocessing Report" in report
    assert "Executive Summary" in report
    assert "Data Cleaning & Integrity Audit" in report
    assert "Audionic Brand Social Analytics" in report


def test_save_json_and_csv_metrics(tmp_path):
    data = {"workloads": [{"multiplier": 1, "mean_runtime_seconds": 0.05, "peak_memory_mb": 0.1, "throughput_rows_per_sec": 500}]}
    json_p = save_json_metrics(data, tmp_path / "metrics.json")
    csv_p = save_csv_benchmarks(data, tmp_path / "metrics.csv")
    assert json_p.exists()
    assert csv_p.exists()
