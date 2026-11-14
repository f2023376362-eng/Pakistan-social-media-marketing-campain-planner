"""
Test Suite for YouTube Data Scraper Module.
Tests video ID extraction, API configuration status, search querying,
video detail retrieval, and comment scraping with mocked YouTube Data API v3 responses.
"""

from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from src.youtube_scraper import (
    extract_video_id,
    get_api_status,
    search_videos,
    get_video_details,
    scrape_video_comments,
    scrape_comments_for_videos,
    VIDEO_SCHEMA_COLUMNS,
    COMMENT_SCHEMA_COLUMNS,
)


def test_extract_video_id():
    # Standard watch URL
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Shortened youtu.be URL
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # YouTube Shorts URL
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Embed URL
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Raw 11-char ID
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # With extra URL query parameters
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=shared") == "dQw4w9WgXcQ"
    # Invalid strings
    assert extract_video_id("https://google.com") is None
    assert extract_video_id("not-a-valid-id") is None
    assert extract_video_id("") is None


def test_get_api_status():
    status = get_api_status()
    assert "configured" in status
    assert "masked_key" in status
    assert "status_label" in status
    assert isinstance(status["configured"], bool)


@patch("src.youtube_scraper.requests.get")
def test_get_video_details_mocked(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "dQw4w9WgXcQ",
                "snippet": {
                    "title": "Pakistan FinTech Growth 2026",
                    "description": "An analysis of mobile payments and banking trends.",
                    "channelId": "ch_pk_001",
                    "channelTitle": "Tech Digest Pakistan",
                    "publishedAt": "2026-01-15T10:00:00Z"
                },
                "statistics": {
                    "viewCount": "125000",
                    "likeCount": "4300",
                    "commentCount": "210"
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    df, err = get_video_details(["dQw4w9WgXcQ"], api_key="FAKE_KEY_12345")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["video_id"] == "dQw4w9WgXcQ"
    assert df.iloc[0]["view_count"] == 125000
    assert df.iloc[0]["like_count"] == 4300
    assert df.iloc[0]["comment_count"] == 210
    for col in VIDEO_SCHEMA_COLUMNS:
        assert col in df.columns


@patch("src.youtube_scraper.get_video_details")
@patch("src.youtube_scraper.requests.get")
def test_search_videos_mocked(mock_get, mock_details):
    mock_search_resp = MagicMock()
    mock_search_resp.status_code = 200
    mock_search_resp.json.return_value = {
        "items": [
            {
                "id": {"videoId": "dQw4w9WgXcQ"}
            }
        ]
    }
    mock_get.return_value = mock_search_resp

    mock_details_df = pd.DataFrame([
        {
            "video_id": "dQw4w9WgXcQ",
            "video_title": "Pakistan FinTech Growth 2026",
            "video_description": "An analysis of mobile payments.",
            "channel_id": "ch_pk_001",
            "channel_title": "Tech Digest Pakistan",
            "published_at": "2026-01-15T10:00:00Z",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "view_count": 125000,
            "like_count": 4300,
            "comment_count": 210,
            "collected_at": "2026-02-01T12:00:00Z"
        }
    ])
    mock_details.return_value = (mock_details_df, None)

    df, err = search_videos(query="Pakistan FinTech", max_results=1, api_key="FAKE_KEY_12345")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["video_id"] == "dQw4w9WgXcQ"
    assert df.iloc[0]["video_title"] == "Pakistan FinTech Growth 2026"


@patch("src.youtube_scraper.requests.get")
def test_scrape_video_comments_mocked(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "comment_101",
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "authorDisplayName": "@AudienceUser",
                            "textDisplay": "Excellent initiative for social data collection!",
                            "likeCount": 15,
                            "publishedAt": "2026-02-01T12:00:00Z"
                        }
                    },
                    "totalReplyCount": 3
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    df, err = scrape_video_comments(video_id="dQw4w9WgXcQ", max_comments=10, api_key="FAKE_KEY_12345")
    assert err is None
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["comment_id"] == "comment_101"
    assert df.iloc[0]["author"] == "@AudienceUser"
    assert df.iloc[0]["likes"] == 15
    assert df.iloc[0]["reply_count"] == 3
    for col in COMMENT_SCHEMA_COLUMNS:
        assert col in df.columns


@patch("src.youtube_scraper.requests.get")
def test_api_quota_error_handling(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {
        "error": {
            "errors": [{"reason": "quotaExceeded"}],
            "message": "The request cannot be completed because you have exceeded your quota."
        }
    }
    mock_get.return_value = mock_response

    df, err = search_videos(query="Test", api_key="FAKE_KEY_12345")
    assert df.empty
    assert "quota" in str(err).lower()
