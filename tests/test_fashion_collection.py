"""
Unit and Integration Tests for Phase 2: Real Pakistani Fashion Audience Data Collection.
Verifies relevance filtering, multilingual detection, schema compliance,
provenance attribution, and dataset integrity.
"""

import os
import pytest
import pandas as pd

from run_fashion_collection import is_valid_fashion_video, detect_language, TARGET_BRANDS


def test_fashion_video_relevance_filter():
    # Khaadi tests
    assert is_valid_fashion_video("Khaadi", "Khaadi Summer Lawn 2024 Collection", "New unstitched suits") is True
    assert is_valid_fashion_video("Khaadi", "Khaadi X Esra | My Symphony", "Official fashion commercial") is True
    assert is_valid_fashion_video("Khaadi", "Khadi Natural Herbal Amla Shampoo Review", "Ayurvedic hair oil") is False
    assert is_valid_fashion_video("Khaadi", "Khadi India Ashram Handloom Khadi", "Khadi Gramodyog Bhavan") is False

    # Sapphire tests
    assert is_valid_fashion_video("Sapphire", "Sapphire Pakistan Lawn 2024 Collection", "Ready to wear prêt") is True
    assert is_valid_fashion_video("Sapphire", "Sapphire Sale Shopping Haul", "Unstitched 3 piece suits from Dolmen Mall") is True
    assert is_valid_fashion_video("Sapphire", "Pokemon Ruby and Sapphire Commercial", "Nintendo Game Boy Advance") is False
    assert is_valid_fashion_video("Sapphire", "Sapphire Radeon RX 7800 XT Graphic Card", "AMD GPU Benchmark Review") is False
    assert is_valid_fashion_video("Sapphire", "Natural Blue Sapphire Gemstone Ring", "Certified Ceylon Sapphire") is False

    # Gul Ahmed tests
    assert is_valid_fashion_video("Gul Ahmed", "Gul Ahmed Summer Lawn 2024 Collection", "Unstitched lawn collection") is True
    assert is_valid_fashion_video("Gul Ahmed", "Ideas by Gul Ahmed Winter Sale Haul", "Shopping from Ideas outlet") is True
    assert is_valid_fashion_video("Gul Ahmed", "WWE Wrestling Gul Ahmed", "Action match") is False


def test_detect_language():
    # Urdu script
    assert detect_language("بہت خوبصورت کپڑے ہیں ماشاءاللہ") == "Urdu"
    # English
    assert detect_language("The fabric quality is really amazing and vibrant!") == "English"
    # Roman Urdu
    assert detect_language("ye suit bohat acha hai kya price hai?") == "Roman Urdu"
    assert detect_language("bohot pyara color hai mujhe bhi chahiye") == "Roman Urdu"
    # Mixed
    assert detect_language("Amazing quality بہت خوبصورت") == "Mixed (Urdu-English)"
    # Empty / whitespace
    assert detect_language("") == "Unknown"
    assert detect_language("   ") == "Unknown"


def test_real_fashion_dataset_integrity_and_schemas():
    comments_path = os.path.join("data", "raw", "real_fashion_comments.csv")
    videos_path = os.path.join("data", "raw", "real_fashion_videos.csv")

    if not os.path.exists(comments_path) or not os.path.exists(videos_path):
        pytest.skip("Real fashion datasets have not been collected yet.")

    c_df = pd.read_csv(comments_path)
    v_df = pd.read_csv(videos_path)

    # 1. Non-empty and volume validation (target 2,000–5,000)
    assert len(c_df) >= 2000, f"Comment count {len(c_df)} is below 2,000 target"
    assert len(v_df) >= 20, f"Video count {len(v_df)} is unexpectedly low"

    # 2. Schema columns validation
    required_comment_cols = [
        "comment_id", "video_id", "comment_text", "author",
        "likes", "reply_count", "parent_comment_id", "brand_name",
        "source_platform", "data_provenance", "data_role"
    ]
    for col in required_comment_cols:
        assert col in c_df.columns, f"Missing required column in comments: {col}"

    required_video_cols = [
        "video_id", "video_title", "channel_id", "channel_name",
        "view_count", "like_count", "comment_count", "brand_name",
        "source_platform", "data_provenance", "data_role"
    ]
    for col in required_video_cols:
        assert col in v_df.columns, f"Missing required column in videos: {col}"

    # 3. Provenance and governance tokens
    assert (c_df["data_provenance"] == "real_public").all()
    assert (c_df["data_role"] == "analysis").all()
    assert (c_df["source_platform"] == "YouTube").all()

    assert (v_df["data_provenance"] == "real_public").all()
    assert (v_df["data_role"] == "analysis").all()
    assert (v_df["source_platform"] == "YouTube").all()

    # 4. Brand coverage across all 3 target brands
    for b in TARGET_BRANDS:
        assert (c_df["brand_name"] == b).sum() > 0, f"No comments found for brand {b}"
        assert (v_df["brand_name"] == b).sum() > 0, f"No videos found for brand {b}"

    # 5. Exact deduplication on comment_id
    assert c_df.duplicated(subset=["comment_id"]).sum() == 0, "Duplicate comment_ids found in dataset"

    # 6. Verify separation from synthetic development dataset
    synth_path = os.path.join("data", "processed", "fashion_development.csv")
    if os.path.exists(synth_path):
        s_df = pd.read_csv(synth_path)
        assert len(s_df) == 436, f"Synthetic dataset was altered! Length: {len(s_df)}"
        assert (s_df["data_provenance"] == "synthetic").all()
