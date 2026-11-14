"""
Temporal Pacing and Lexical Text Analysis Engine.
Analyzes temporal activity distributions (yearly, day-of-week, UTC hour)
and extracts lexical features, word counts, emoji usage, and frequent keywords dynamically.
"""

from collections import Counter
import re
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Multi-lingual stopwords (English, Urdu/Hindi Romanized, common social expressions)
GENERIC_STOPWORDS = {
    "the", "and", "this", "that", "with", "for", "you", "are", "was", "very", "nice", "good", "super",
    "best", "love", "dil", "hai", "ki", "ka", "ke", "ko", "se", "me", "bhi", "ho", "par", "kya", "yeh", "woh",
    "tha", "thi", "the", "h", "to", "is", "in", "it", "my", "of", "on", "at", "by", "an", "as", "be", "all",
    "so", "one", "na", "ne", "si", "ek", "mera", "meri", "mere", "mai", "main", "mujhe", "hum", "tum", "aap",
    "karo", "kare", "kar", "karna", "liye", "baat", "lag", "laga", "rahe", "raha", "rahi", "jaise", "aise",
    "from", "your", "have", "has", "had", "will", "would", "can", "could", "should", "not", "but", "about",
    "after", "watching", "still", "when", "how", "why", "their", "its", "into", "just", "like"
}


def analyze_temporal(
    df: pd.DataFrame,
    date_col: Optional[str] = None,
    timestamp_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes temporal patterns across comments or video publication timestamps:
    - Span in days, earliest and latest publication timestamps
    - Yearly publication breakdown
    - Day of week activity (Monday-Sunday)
    - Hour of day activity (UTC 00:00 - 23:00)
    """
    target_col = timestamp_col or date_col or "published_at"
    if target_col not in df.columns:
        if "published_at" in df.columns:
            target_col = "published_at"
        elif "date" in df.columns:
            target_col = "date"
        else:
            return {}

    parsed_dates = pd.to_datetime(df[target_col], errors="coerce", utc=True)
    valid_dt = parsed_dates.dropna()

    if valid_dt.empty:
        return {
            "earliest_comment_utc": "N/A",
            "latest_comment_utc": "N/A",
            "total_span_days": 0,
            "yearly_distribution": {},
            "day_of_week_distribution": {},
            "hour_of_day_distribution_utc": {},
            "hourly_distribution": {},
        }

    earliest = valid_dt.min()
    latest = valid_dt.max()
    span_days = round((latest - earliest).total_seconds() / 86400.0, 1)

    # Yearly breakdown
    yearly_counts = valid_dt.dt.year.value_counts().sort_index().to_dict()
    yearly_dict = {str(k): int(v) for k, v in yearly_counts.items()}

    # Day of week breakdown (0=Monday, 6=Sunday)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_counts = valid_dt.dt.day_of_week.value_counts().sort_index().to_dict()
    dow_dict = {day_names[k]: int(dow_counts.get(k, 0)) for k in range(7)}

    # Hour of day breakdown (UTC)
    hour_counts = valid_dt.dt.hour.value_counts().sort_index().to_dict()
    hour_dict = {f"{h:02d}:00": int(hour_counts.get(h, 0)) for h in range(24)}

    return {
        "earliest_comment_utc": earliest.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "latest_comment_utc": latest.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_span_days": span_days,
        "yearly_distribution": yearly_dict,
        "day_of_week_distribution": dow_dict,
        "hour_of_day_distribution_utc": hour_dict,
        "hourly_distribution": hour_dict,
    }


def analyze_text(
    df: pd.DataFrame,
    text_col: Optional[str] = None,
    custom_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyzes lexical characteristics, character/word length, questions, emojis,
    and extracts top frequent keywords dynamically.
    """
    if text_col is None:
        text_col = "comment_text" if "comment_text" in df.columns else ("comment" if "comment" in df.columns else None)

    if not text_col or text_col not in df.columns:
        return {}

    comments = df[text_col].dropna().astype(str)
    total_comments = len(comments)
    if total_comments == 0:
        return {}

    char_lengths = comments.str.len()
    word_counts = comments.apply(lambda text: len(text.split()))

    # Expressions
    has_question = int(comments.str.contains(r"\?", regex=True).sum())
    has_exclamation = int(comments.str.contains(r"!", regex=True).sum())
    has_emoji = int(comments.apply(lambda s: bool(re.search(r"[\U00010000-\U0010ffff]", s))).sum())

    # Token frequency
    tokens = []
    for comment in comments:
        clean_str = re.sub(r"[^\w\s]", " ", comment.lower())
        words = [w for w in clean_str.split() if len(w) > 2 and w not in GENERIC_STOPWORDS and not w.isdigit()]
        tokens.extend(words)

    word_freq = Counter(tokens).most_common(25)

    # Configurable keyword tracking
    custom_tracking = {}
    if custom_keywords:
        lower_comments = comments.str.lower()
        for kw in custom_keywords:
            kw_clean = kw.strip().lower()
            if kw_clean:
                pattern = r"\b" + re.escape(kw_clean) + r"\b"
                custom_tracking[kw_clean] = int(lower_comments.str.contains(pattern, regex=True).sum())

    return {
        "total_analyzed_comments": total_comments,
        "char_length": {
            "min": int(char_lengths.min()),
            "mean": round(float(char_lengths.mean()), 2),
            "median": float(char_lengths.median()),
            "max": int(char_lengths.max()),
            "std": round(float(char_lengths.std()), 2) if len(char_lengths) > 1 else 0.0,
        },
        "word_count": {
            "min": int(word_counts.min()),
            "mean": round(float(word_counts.mean()), 2),
            "median": float(word_counts.median()),
            "max": int(word_counts.max()),
        },
        "expression_counts": {
            "comments_with_question": has_question,
            "question_pct": round(has_question / total_comments * 100, 2) if total_comments > 0 else 0.0,
            "comments_with_exclamation": has_exclamation,
            "exclamation_pct": round(has_exclamation / total_comments * 100, 2) if total_comments > 0 else 0.0,
            "comments_with_emojis": has_emoji,
            "emoji_pct": round(has_emoji / total_comments * 100, 2) if total_comments > 0 else 0.0,
        },
        "top_keywords": [{"keyword": k, "count": c} for k, c in word_freq],
        "top_unigrams": word_freq,
        "vocabulary_size": len(set(tokens)),
        "total_words": len(tokens),
        "custom_keyword_tracking": custom_tracking,
    }
