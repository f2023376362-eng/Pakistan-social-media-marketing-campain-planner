"""
Test Suite for Statistical, Temporal, Lexical, and Sentiment Analytics Modules.
Verifies Gini inequality calculations, descriptive distributions, temporal pacing,
lexical tokenization, and optional sentiment classification.
"""

import pytest
import numpy as np
import pandas as pd

from src.statistics import calculate_descriptive_statistics, compute_gini
from src.text_temporal import analyze_temporal, analyze_text
from src.sentiment_engine import (
    analyze_youtube_sentiment,
    compute_comment_polarity,
    classify_sentiment,
    clean_comment_text,
)


def test_gini_coefficient_properties():
    # Perfectly equal distribution -> Gini should be 0.0
    equal_series = pd.Series([10, 10, 10, 10, 10])
    assert compute_gini(equal_series) == 0.0

    # Highly unequal distribution -> Gini should be close to 1.0
    unequal_series = pd.Series([0, 0, 0, 0, 1000])
    g_unequal = compute_gini(unequal_series)
    assert 0.7 <= g_unequal <= 1.0

    # All zeros -> Gini is 0.0
    zero_series = pd.Series([0, 0, 0])
    assert compute_gini(zero_series) == 0.0

    # Empty series
    empty_series = pd.Series([], dtype=float)
    assert compute_gini(empty_series) == 0.0


def test_descriptive_statistics():
    df = pd.DataFrame({
        "likes": [0, 5, 10, 15, 20],
        "reply_count": [0, 1, 2, 3, 4],
        "comment_text": ["a", "b", "c", "d", "e"]
    })
    stats = calculate_descriptive_statistics(df)
    assert "likes" in stats
    assert stats["likes"]["mean"] == 10.0
    assert stats["likes"]["sum"] == 50
    assert stats["likes"]["min"] == 0
    assert stats["likes"]["max"] == 20
    assert "reply_count" in stats
    assert stats["reply_count"]["mean"] == 2.0


def test_temporal_analysis():
    df = pd.DataFrame({
        "published_at": [
            "2026-01-01T10:00:00Z",
            "2026-01-02T12:00:00Z",
            "2026-01-03T18:00:00Z",
            "2026-01-03T20:00:00Z",
        ],
        "comment_text": ["c1", "c2", "c3", "c4"]
    })
    temp = analyze_temporal(df, timestamp_col="published_at")
    assert "yearly_distribution" in temp
    assert "day_of_week_distribution" in temp
    assert "hourly_distribution" in temp
    assert temp["yearly_distribution"].get("2026", 0) == 4 or temp["yearly_distribution"].get(2026, 0) == 4


def test_lexical_text_analysis():
    df = pd.DataFrame({
        "comment_text": [
            "Pakistan digital tech is advancing rapidly in fintech and logistics.",
            "Fintech is booming in Pakistan with mobile wallets and venture capital.",
            "E-commerce logistics and digital transformation represent immense opportunity."
        ]
    })
    text_metrics = analyze_text(df, text_col="comment_text")
    assert "top_unigrams" in text_metrics
    assert "vocabulary_size" in text_metrics
    assert text_metrics["total_words"] > 0
    top_words = [word for word, count in text_metrics["top_unigrams"]]
    assert "fintech" in top_words or "pakistan" in top_words


def test_sentiment_classification_optional_module():
    df = pd.DataFrame({
        "comment_text": [
            "Superb execution, truly fantastic and inspiring progress!",
            "Terrible disaster, horrible experience and broken service.",
            "The report was published on Tuesday at 4 PM."
        ]
    })
    sent_df, summary = analyze_youtube_sentiment(df, comment_col="comment_text")
    assert summary["total_comments"] == 3
    assert summary["positive_count"] == 1
    assert summary["negative_count"] == 1
    assert summary["neutral_count"] == 1
    assert np.isclose(summary["positive_pct"] + summary["negative_pct"] + summary["neutral_pct"], 100.0, atol=0.1)
    assert "sentiment" in sent_df.columns
    assert "sentiment_score" in sent_df.columns


def test_sentiment_empty_and_null_resilience():
    empty_df = pd.DataFrame({"comment_text": ["", None, "   "]})
    sent_df, summary = analyze_youtube_sentiment(empty_df, comment_col="comment_text")
    assert summary["total_comments"] == 3
    assert summary["neutral_count"] == 3
    assert summary["positive_count"] == 0
    assert summary["negative_count"] == 0
