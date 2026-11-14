"""
YouTube Comment Sentiment Analysis Supporting Engine.
Optional analytical module performing lexicon-based polarity scoring
and sentiment classification on social media comments.

Academic Notice:
Sentiment scores are approximations derived from rule-based lexical matching and negation inversion.
They serve as an exploratory qualitative signal, not as definitive ground truth.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

# Multi-domain social sentiment lexicon
YOUTUBE_SENTIMENT_LEXICON = {
    # Positive tokens
    'love': 2.0, 'awesome': 2.2, 'amazing': 2.2, 'masterpiece': 2.5, 'great': 1.5,
    'good': 1.2, 'best': 2.0, 'fire': 2.0, 'goosebumps': 2.2, 'fantastic': 2.0,
    'beautiful': 1.8, 'favorite': 1.8, 'proud': 1.6, 'hit': 1.5, 'legend': 2.0,
    'super': 1.4, 'cool': 1.3, 'nice': 1.2, 'perfect': 2.0, 'loved': 1.8,
    'outstanding': 2.2, 'wonderful': 2.0, 'king': 1.5, 'queen': 1.5, 'blessed': 1.6,
    'classic': 1.7, 'vibes': 1.4, 'enjoyed': 1.5, 'sweet': 1.2, 'gem': 2.0,
    'helpful': 1.5, 'informative': 1.8, 'brilliant': 2.0, 'excellent': 2.2,
    
    # Negative tokens
    'bad': -1.5, 'worst': -2.5, 'terrible': -2.2, 'horrible': -2.2, 'cringe': -2.0,
    'boring': -1.8, 'disappointed': -2.0, 'waste': -2.2, 'hate': -2.0, 'stupid': -1.8,
    'flop': -1.8, 'cheap': -1.5, 'ugly': -1.7, 'trash': -2.2, 'poor': -1.4,
    'ruined': -2.0, 'annoying': -1.8, 'overrated': -1.6, 'garbage': -2.2, 'dislike': -1.5,
    'useless': -2.0, 'fake': -2.0, 'misleading': -2.0, 'pathetic': -2.2
}

NEGATION_WORDS = {'not', 'never', 'no', 'without', 'hardly', 'barely', "didn't", "don't", "wasn't", "isn't", "cannot"}


def clean_comment_text(text: str) -> str:
    """Normalizes comment text: strips URLs, HTML tags, and excessive spaces."""
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r'<[^>]+>', ' ', text)
    cleaned = re.sub(r'http\S+|www\.\S+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def compute_comment_polarity(text: str) -> float:
    """
    Computes normalized polarity score in [-1.0, 1.0] using lexicon and negation heuristics.
    """
    cleaned = clean_comment_text(text).lower()
    words = re.findall(r"\b[a-z']+\b", cleaned)
    if not words:
        return 0.0

    score = 0.0
    negate_flag = False

    for w in words:
        if w in NEGATION_WORDS:
            negate_flag = True
            continue

        weight = YOUTUBE_SENTIMENT_LEXICON.get(w, 0.0)
        if weight != 0.0:
            if negate_flag:
                score -= weight * 0.8
                negate_flag = False
            else:
                score += weight
        else:
            if w in {'but', 'however', 'and'}:
                negate_flag = False

    return round(float(np.tanh(score / 2.5)), 4)


def classify_sentiment(polarity: float) -> str:
    """Classifies polarity into Positive, Negative, or Neutral."""
    if polarity >= 0.08:
        return 'Positive'
    elif polarity <= -0.08:
        return 'Negative'
    return 'Neutral'


def analyze_youtube_sentiment(df: pd.DataFrame,
                              comment_col: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes sentiment analysis on YouTube comments DataFrame.
    Returns: (enriched_df, summary_metrics)
    """
    if df is None or df.empty:
        empty_res = df.copy() if df is not None else pd.DataFrame()
        empty_res['polarity'] = pd.Series(dtype=float)
        empty_res['sentiment'] = pd.Series(dtype=str)
        return empty_res, {
            'total_comments': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'positive_pct': 0.0,
            'negative_pct': 0.0,
            'neutral_pct': 0.0,
            'mean_polarity': 0.0
        }

    if comment_col is None:
        comment_col = "comment_text" if "comment_text" in df.columns else ("comment" if "comment" in df.columns else None)

    if not comment_col or comment_col not in df.columns:
        raise ValueError(f"Comment text column not found in DataFrame. Available: {list(df.columns)}")

    data = df.copy()
    data['cleaned_comment'] = data[comment_col].astype(str).apply(clean_comment_text)
    data['polarity'] = data['cleaned_comment'].apply(compute_comment_polarity)
    data['sentiment_score'] = data['polarity']
    data['sentiment'] = data['polarity'].apply(classify_sentiment)

    total = len(data)
    pos_count = int((data['sentiment'] == 'Positive').sum())
    neg_count = int((data['sentiment'] == 'Negative').sum())
    neu_count = int((data['sentiment'] == 'Neutral').sum())

    pos_pct = round((pos_count / max(1, total)) * 100.0, 2)
    neg_pct = round((neg_count / max(1, total)) * 100.0, 2)
    neu_pct = round((neu_count / max(1, total)) * 100.0, 2)

    top_pos = (
        data[data['sentiment'] == 'Positive']
        .sort_values(by=['polarity', 'likes'] if 'likes' in data.columns else ['polarity'], ascending=[False, False] if 'likes' in data.columns else [False])
        .head(5)
    )
    top_neg = (
        data[data['sentiment'] == 'Negative']
        .sort_values(by=['polarity', 'likes'] if 'likes' in data.columns else ['polarity'], ascending=[True, False] if 'likes' in data.columns else [True])
        .head(5)
    )

    summary = {
        'total_comments': total,
        'positive_count': pos_count,
        'negative_count': neg_count,
        'neutral_count': neu_count,
        'positive_pct': pos_pct,
        'negative_pct': neg_pct,
        'neutral_pct': neu_pct,
        'mean_polarity': round(float(data['polarity'].mean()), 4) if total > 0 else 0.0,
        'method': 'Rule-Based Lexicon with Negation Inversion',
        'limitations': 'Approximation model; does not account for subtle sarcasm or non-English cultural colloquialisms.'
    }

    return data, summary
