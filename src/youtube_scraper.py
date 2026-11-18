"""
Reusable YouTube Social Media Data Collection Pipeline.
Provides robust harvesting of YouTube video metadata and user comments via YouTube Data API v3.
Features:
- Configurable search queries across any topic/industry
- Configurable video ID / URL harvesting
- Video metadata extraction (snippet + statistics)
- Comment thread collection with API pagination
- Safe error handling (comments disabled, quota exceeded, invalid IDs)
- Strict compliance with standardized Video and Comment schemas.
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import requests

YT_API_BASE = "https://www.googleapis.com/youtube/v3"

# Standardized Schema Definitions (YouTube Original)
VIDEO_SCHEMA_COLUMNS = [
    "video_id",
    "video_title",
    "video_description",
    "channel_id",
    "channel_title",
    "published_at",
    "video_url",
    "view_count",
    "like_count",
    "comment_count",
    "collected_at"
]

COMMENT_SCHEMA_COLUMNS = [
    "comment_id",
    "video_id",
    "author",
    "comment_text",
    "likes",
    "published_at",
    "reply_count",
    "collected_at"
]

# Standardized Brand Social Media Schemas (Project 3 Specification)
BRAND_VIDEO_SCHEMA_COLUMNS = [
    "platform",
    "source_platform",
    "brand_name",
    "video_id",
    "video_title",
    "video_description",
    "channel_id",
    "channel_title",
    "channel_name",
    "published_at",
    "video_url",
    "source_url",
    "view_count",
    "views",
    "like_count",
    "likes",
    "comment_count",
    "comments_count",
    "data_provenance",
    "data_role",
    "collected_at"
]

BRAND_COMMENT_SCHEMA_COLUMNS = [
    "platform",
    "source_platform",
    "brand_name",
    "video_id",
    "video_url",
    "comment_id",
    "parent_comment_id",
    "author",
    "comment_text",
    "likes",
    "reply_count",
    "published_at",
    "data_provenance",
    "data_role",
    "collected_at"
]


def _sanitize_error_msg(err_str: str) -> str:
    """Removes sensitive API key patterns from error messages."""
    return re.sub(r'(?:key|AIza)[A-Za-z0-9_-]{10,}', '[REDACTED_API_KEY]', err_str)


def get_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """Retrieves API key from parameter, environment, or .env file."""
    if explicit_key and len(explicit_key.strip()) > 10 and explicit_key.strip() != "your_youtube_api_key_here":
        return explicit_key.strip()

    key = os.getenv("YOUTUBE_API_KEY")
    if key and key != "your_youtube_api_key_here" and len(key.strip()) > 10:
        return key.strip()

    # Fallback to inspecting .env file manually
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("YOUTUBE_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and val != "your_youtube_api_key_here" and len(val) > 10:
                        return val
    return None


def get_api_status(explicit_key: Optional[str] = None) -> Dict[str, Any]:
    """Returns safe API readiness status without exposing secret values."""
    key = get_api_key(explicit_key)
    is_ready = bool(key)
    masked = f"{key[:4]}...{key[-4:]}" if key and len(key) >= 8 else ("Configured" if key else "Not Configured")
    return {
        "configured": is_ready,
        "masked_key": masked,
        "status_label": "Ready (API Key Configured)" if is_ready else "Missing API Key (Set YOUTUBE_API_KEY in .env)",
        "can_scrape": is_ready
    }


def extract_video_id(url_or_id: str) -> Optional[str]:
    """
    Extracts canonical 11-character YouTube video ID from various URL formats.
    Supported inputs:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - Raw 11-character string
    """
    if not url_or_id:
        return None
    text = str(url_or_id).strip()
    if len(text) == 11 and re.match(r'^[A-Za-z0-9_-]{11}$', text):
        return text

    patterns = [
        r'(?:v=|\/)([A-Za-z0-9_-]{11})(?:\&|\?|\/|$)',
        r'youtu\.be\/([A-Za-z0-9_-]{11})',
        r'shorts\/([A-Za-z0-9_-]{11})',
        r'embed\/([A-Za-z0-9_-]{11})'
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def get_video_details(video_ids: List[str] | str,
                      api_key: Optional[str] = None,
                      brand_name: Optional[str] = None,
                      platform: str = "YouTube") -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Retrieves full video metadata (snippet and statistics) for one or more video IDs.
    Returns: (DataFrame matching VIDEO_SCHEMA_COLUMNS & BRAND_VIDEO_SCHEMA_COLUMNS, error_message)
    """
    key = get_api_key(api_key)
    if not key:
        return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), "YouTube API key not found. Please set YOUTUBE_API_KEY."

    if isinstance(video_ids, str):
        v_list = [extract_video_id(video_ids) or video_ids]
    else:
        v_list = [extract_video_id(v) or v for v in video_ids if v]

    v_list = [v for v in v_list if v and len(v) == 11]
    if not v_list:
        return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), "No valid 11-character YouTube video IDs provided."

    records = []
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # API accepts up to 50 video IDs per request
    for i in range(0, len(v_list), 50):
        batch = v_list[i:i + 50]
        params = {
            "part": "snippet,statistics",
            "id": ",".join(batch),
            "key": key
        }
        try:
            resp = requests.get(f"{YT_API_BASE}/videos", params=params, timeout=12)
            data = resp.json()

            if resp.status_code != 200:
                err_code = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                if err_code == "quotaExceeded":
                    return pd.DataFrame(records), "YouTube Data API quota exceeded for today."
                return pd.DataFrame(records), data.get("error", {}).get("message", "API request failed.")

            items = data.get("items", [])
            for item in items:
                v_id = item.get("id", "")
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                # Safe integer coercion preserving None if statistics not available
                def parse_int_metric(val):
                    try:
                        return int(val) if val is not None else None
                    except (ValueError, TypeError):
                        return None

                v_views = parse_int_metric(stats.get("viewCount"))
                v_likes = parse_int_metric(stats.get("likeCount"))
                v_comments = parse_int_metric(stats.get("commentCount"))
                v_url = f"https://www.youtube.com/watch?v={v_id}"

                records.append({
                    "platform": platform,
                    "source_platform": platform,
                    "brand_name": brand_name or "",
                    "video_id": v_id,
                    "post_id": v_id,
                    "video_title": snippet.get("title", ""),
                    "video_description": snippet.get("description", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "channel_name": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "video_url": v_url,
                    "source_url": v_url,
                    "view_count": v_views,
                    "views": v_views,
                    "like_count": v_likes,
                    "likes": v_likes,
                    "comment_count": v_comments,
                    "comments_count": v_comments,
                    "data_provenance": "real_public",
                    "data_role": "analysis",
                    "collected_at": collected_at
                })
        except requests.exceptions.RequestException as e:
            return pd.DataFrame(records), _sanitize_error_msg(f"Network error during video lookup: {str(e)}")

    cols = list(dict.fromkeys(VIDEO_SCHEMA_COLUMNS + BRAND_VIDEO_SCHEMA_COLUMNS))
    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=cols)
    else:
        for c in cols:
            if c not in df.columns:
                df[c] = None
    return df, None


def search_videos(query: str,
                  max_results: int = 20,
                  order: str = "relevance",
                  region_code: Optional[str] = None,
                  api_key: Optional[str] = None,
                  brand_name: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Searches YouTube for videos matching a query keyword/topic, across any industry or brand.
    Retrieves full video metadata for the matching videos.
    Returns: (DataFrame matching VIDEO_SCHEMA_COLUMNS, error_message)
    """
    key = get_api_key(api_key)
    if not key:
        return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), "YouTube API key not found. Please set YOUTUBE_API_KEY."

    if not query or not query.strip():
        return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), "Search query cannot be empty."

    collected_video_ids = []
    page_token = None
    target_count = max(1, min(max_results, 100))

    try:
        while len(collected_video_ids) < target_count:
            params = {
                "part": "id",
                "type": "video",
                "q": query.strip(),
                "maxResults": min(50, target_count - len(collected_video_ids)),
                "order": order,
                "key": key
            }
            if region_code:
                params["regionCode"] = region_code
            if page_token:
                params["pageToken"] = page_token

            resp = requests.get(f"{YT_API_BASE}/search", params=params, timeout=12)
            data = resp.json()

            if resp.status_code != 200:
                err_code = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                if err_code == "quotaExceeded":
                    return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), "YouTube Data API quota exceeded for today."
                return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), data.get("error", {}).get("message", "Search failed.")

            items = data.get("items", [])
            if not items:
                break

            for it in items:
                v_id = it.get("id", {}).get("videoId")
                if v_id and v_id not in collected_video_ids:
                    collected_video_ids.append(v_id)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        if not collected_video_ids:
            return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), f"No videos found matching query: '{query}'."

        # Fetch full snippet and stats for discovered videos
        return get_video_details(collected_video_ids, api_key=key, brand_name=brand_name)

    except requests.exceptions.RequestException as e:
        return pd.DataFrame(columns=VIDEO_SCHEMA_COLUMNS), _sanitize_error_msg(f"Network error during YouTube search: {str(e)}")


def scrape_video_comments(video_url_or_id: Optional[str] = None,
                          max_comments: int = 100,
                          order: str = "relevance",
                          api_key: Optional[str] = None,
                          video_id: Optional[str] = None,
                          brand_name: Optional[str] = None,
                          platform: str = "YouTube",
                          include_replies: bool = True) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Harvests public comments for a specific YouTube video via YouTube Data API v3.
    Supports API pagination via nextPageToken, brand attribution, and threaded replies.
    Returns: (DataFrame matching COMMENT_SCHEMA_COLUMNS & BRAND_COMMENT_SCHEMA_COLUMNS, error_message)
    """
    target = video_url_or_id or video_id
    key = get_api_key(api_key)
    if not key:
        return pd.DataFrame(columns=COMMENT_SCHEMA_COLUMNS), "YouTube API key not found. Please set YOUTUBE_API_KEY."

    vid = extract_video_id(target)
    if not vid:
        return pd.DataFrame(columns=COMMENT_SCHEMA_COLUMNS), "Invalid YouTube video URL or ID format."

    records = []
    page_token = None
    target_count = max(1, max_comments)
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    video_url = f"https://www.youtube.com/watch?v={vid}"

    try:
        while len(records) < target_count:
            params = {
                "part": "snippet,replies" if include_replies else "snippet",
                "videoId": vid,
                "maxResults": min(100, target_count - len(records)),
                "order": order,
                "textFormat": "plainText",
                "key": key
            }
            if page_token:
                params["pageToken"] = page_token

            resp = requests.get(f"{YT_API_BASE}/commentThreads", params=params, timeout=12)
            data = resp.json()

            if resp.status_code != 200:
                err_code = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                if err_code == "commentsDisabled":
                    return pd.DataFrame(columns=COMMENT_SCHEMA_COLUMNS), "Comments are disabled for this YouTube video."
                elif err_code == "quotaExceeded":
                    return pd.DataFrame(records, columns=COMMENT_SCHEMA_COLUMNS), "YouTube Data API quota exceeded for today."
                else:
                    return pd.DataFrame(records, columns=COMMENT_SCHEMA_COLUMNS), data.get("error", {}).get("message", "API request failed.")

            items = data.get("items", [])
            if not items:
                break

            for it in items:
                c_id = it.get("id", "")
                snippet_top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                reply_count = int(it.get("snippet", {}).get("totalReplyCount", 0))

                records.append({
                    "platform": platform,
                    "source_platform": platform,
                    "brand_name": brand_name or "",
                    "video_id": vid,
                    "post_id": vid,
                    "video_url": video_url,
                    "comment_id": c_id,
                    "parent_comment_id": None,
                    "author": snippet_top.get("authorDisplayName", "Anonymous"),
                    "comment_text": snippet_top.get("textDisplay", ""),
                    "likes": int(snippet_top.get("likeCount", 0)),
                    "published_at": snippet_top.get("publishedAt", ""),
                    "reply_count": reply_count,
                    "data_provenance": "real_public",
                    "data_role": "analysis",
                    "collected_at": collected_at
                })

                # Harvest replies if present in thread
                if include_replies and reply_count > 0 and "replies" in it and "comments" in it["replies"]:
                    for reply in it["replies"]["comments"]:
                        if len(records) >= target_count:
                            break
                        r_snippet = reply.get("snippet", {})
                        r_id = reply.get("id", "")
                        records.append({
                            "platform": platform,
                            "source_platform": platform,
                            "brand_name": brand_name or "",
                            "video_id": vid,
                            "post_id": vid,
                            "video_url": video_url,
                            "comment_id": r_id,
                            "parent_comment_id": c_id,
                            "author": r_snippet.get("authorDisplayName", "Anonymous"),
                            "comment_text": r_snippet.get("textDisplay", ""),
                            "likes": int(r_snippet.get("likeCount", 0)),
                            "published_at": r_snippet.get("publishedAt", ""),
                            "reply_count": 0,
                            "data_provenance": "real_public",
                            "data_role": "analysis",
                            "collected_at": collected_at
                        })

                if len(records) >= target_count:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        cols = list(dict.fromkeys(COMMENT_SCHEMA_COLUMNS + BRAND_COMMENT_SCHEMA_COLUMNS))
        df = pd.DataFrame(records)
        if df.empty:
            return pd.DataFrame(columns=cols), "No comments were returned for this video (video may have 0 comments)."
        for c in cols:
            if c not in df.columns:
                df[c] = None
        return df, None

    except requests.exceptions.RequestException as e:
        return pd.DataFrame(records, columns=COMMENT_SCHEMA_COLUMNS), _sanitize_error_msg(f"Network communication error: {str(e)}")


def scrape_comments_for_videos(video_ids: List[str],
                              max_comments_per_video: int = 50,
                              order: str = "relevance",
                              api_key: Optional[str] = None,
                              brand_name: Optional[str] = None,
                              include_replies: bool = True) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Harvests comments across multiple videos in a batch.
    Returns: (combined_comments_df, log_of_statuses)
    """
    all_comments = []
    statuses = []

    for vid in video_ids:
        c_df, err = scrape_video_comments(vid, max_comments=max_comments_per_video, order=order, api_key=api_key, brand_name=brand_name, include_replies=include_replies)
        if err:
            statuses.append({"video_id": vid, "count": len(c_df), "status": "ERROR", "message": err})
        else:
            statuses.append({"video_id": vid, "count": len(c_df), "status": "SUCCESS", "message": "OK"})
            if not c_df.empty:
                all_comments.append(c_df)

    if all_comments:
        return pd.concat(all_comments, ignore_index=True), statuses
    return pd.DataFrame(columns=COMMENT_SCHEMA_COLUMNS), statuses
