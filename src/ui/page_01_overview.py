"""
Page 1: Overview & Brand Dataset Ingestion.
Displays system overview, brand provenance indicators, empty-state banners,
and brand-only CSV/Excel dataset upload with strict schema validation.
"""

from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
import pandas as pd

from src.youtube_scraper import (
    get_api_status,
    VIDEO_SCHEMA_COLUMNS,
    COMMENT_SCHEMA_COLUMNS,
    BRAND_VIDEO_SCHEMA_COLUMNS,
    BRAND_COMMENT_SCHEMA_COLUMNS,
)
from src.dataset_manager import (
    load_file_to_dataframe,
    validate_brand_dataset,
    clean_comment_data,
    clean_video_metadata,
)


def render_page_overview():
    st.title("Project 3: Brand Social Data & Preprocessing Pipeline")
    st.markdown("""
    **Foundation for Pakistan Social Audience & Campaign Intelligence Engine.**  
    Ingests, validates, standardizes, and inspects brand-related social media datasets across YouTube and social channels.
    """)
    st.divider()

    # 1. Active Brand Provenance & Telemetry
    st.subheader("1. Active Brand Data & Provenance Status")
    
    comments_df = st.session_state.get("comments_data")
    videos_df = st.session_state.get("videos_data")
    brand_name = st.session_state.get("brand_name", "None")
    platform = st.session_state.get("platform", "YouTube")
    data_source = st.session_state.get("data_source", "None")
    upload_file = st.session_state.get("upload_filename", "None")

    col1, col2, col3, col4 = st.columns(4)
    api_stat = get_api_status()
    col1.metric("YouTube Data API", "Active" if api_stat["configured"] else "Not Set", api_stat["status_label"])
    col2.metric("Target Brand", brand_name if brand_name else "Not Set", f"Platform: {platform}")
    col3.metric("Brand Comments", f"{len(comments_df):,}" if comments_df is not None else "0 (Empty)", f"Source: {data_source[:15]}")
    col4.metric("Brand Posts/Videos", f"{len(videos_df):,}" if videos_df is not None else "0 (Empty)", f"File: {upload_file[:15]}")

    # Empty State Notice
    if comments_df is None and videos_df is None:
        st.info("ℹ️ **Active Brand Data Status:** No brand dataset is currently loaded. Active directories (`data/raw/`, `data/processed/`, `data/brand/`) are clean and ready. Upload a genuine brand dataset below or collect live data in **Stage 2: YouTube Data Collection**.")
    else:
        st.success(f"✅ **Active Brand Dataset Loaded:** Analyzing `{brand_name}` on `{platform}` from `{data_source}` ({f'{len(comments_df):,} comments' if comments_df is not None else ''} {f'{len(videos_df):,} videos' if videos_df is not None else ''}).")

    st.divider()

    # 2. Genuine Brand Dataset Ingestion
    st.subheader("2. Ingest Genuine Brand Social Dataset (CSV / Excel)")
    st.caption("Upload authentic brand-related social media data. Synthetic or music-video datasets are prohibited in active analytics.")

    with st.expander("📥 Upload Brand Dataset", expanded=(comments_df is None and videos_df is None)):
        up_col1, up_col2 = st.columns([2, 1])
        with up_col1:
            uploaded_file = st.file_uploader(
                "Choose a brand social dataset (.csv, .xlsx, .xls)",
                type=["csv", "xlsx", "xls"],
                key="brand_file_uploader"
            )
        with up_col2:
            target_brand = st.text_input("Brand Name", value=brand_name if brand_name else "Audionic", help="e.g., Audionic, Zero Lifestyle, Khaadi, Jazz")
            target_platform = st.selectbox("Platform", ["YouTube", "Instagram", "Facebook", "TikTok", "Multi-Platform"], index=0)

        if uploaded_file is not None:
            raw_df, err = load_file_to_dataframe(uploaded_file)
            if err:
                st.error(f"Failed to load file: {err}")
            else:
                is_valid, dtype, issues, stats = validate_brand_dataset(raw_df)
                if not is_valid:
                    st.error("❌ Schema Validation Failed:")
                    for issue in issues:
                        st.write(f"- {issue}")
                else:
                    st.success(f"✅ Schema Validation Passed: Identified as **Brand {dtype.capitalize()} Dataset** ({stats.get('rows', len(raw_df)):,} rows).")
                    
                    if st.button("Ingest & Activate Brand Dataset", type="primary"):
                        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        clean_target = raw_df.copy()
                        clean_target["brand_name"] = target_brand
                        clean_target["platform"] = target_platform

                        if dtype == "comments":
                            cleaned, c_metrics = clean_comment_data(clean_target)
                            st.session_state["comments_data"] = cleaned
                            st.session_state["comments_source"] = f"Uploaded Brand CSV ({uploaded_file.name})"
                            st.session_state["cleaning_audit"] = c_metrics
                        else:
                            cleaned, v_metrics = clean_video_metadata(clean_target)
                            st.session_state["videos_data"] = cleaned
                            st.session_state["videos_source"] = f"Uploaded Brand CSV ({uploaded_file.name})"
                            st.session_state["cleaning_audit"] = v_metrics

                        st.session_state["brand_name"] = target_brand
                        st.session_state["platform"] = target_platform
                        st.session_state["data_source"] = f"Uploaded Brand File ({uploaded_file.name})"
                        st.session_state["upload_filename"] = uploaded_file.name
                        st.session_state["collection_date"] = now_utc

                        # Save into data/brand for persistent retention
                        brand_dir = Path("data/brand")
                        brand_dir.mkdir(parents=True, exist_ok=True)
                        save_p = brand_dir / f"{target_brand.lower().replace(' ', '_')}_{dtype}_{uploaded_file.name}"
                        cleaned.to_csv(save_p, index=False, encoding="utf-8")

                        st.success(f"Brand dataset for **{target_brand}** successfully activated and saved to `{save_p}`!")
                        st.rerun()

    st.divider()

    # 3. Standardized Schemas Summary
    st.subheader("3. Enforced Standardized Schemas (Brand Social Data)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Brand Video/Post Metadata Schema**")
        st.code("""
- platform (e.g. YouTube, Instagram)
- brand_name (e.g. Audionic, Zero Lifestyle)
- video_id / post_id (canonical identifier)
- video_title / caption
- video_description
- channel_name / account_name
- published_at (ISO 8601 UTC)
- views (nullable numeric count)
- likes (nullable numeric count)
- comments_count (nullable numeric count)
- source_url
- collected_at (ISO 8601 UTC)
        """, language="text")

    with c2:
        st.markdown("**Brand Comment Telemetry Schema**")
        st.code("""
- platform (e.g. YouTube, Instagram)
- brand_name (e.g. Audionic, Zero Lifestyle)
- video_id / post_id (parent reference)
- comment_id (unique comment ID)
- author (handle / username)
- comment_text (normalized string)
- likes (nullable numeric count)
- reply_count (nullable numeric count)
- published_at (ISO 8601 UTC)
- collected_at (ISO 8601 UTC)
        """, language="text")
