"""
Page 2: YouTube Collection.
Supports:
- Keyword-based YouTube video search with Brand attribution
- Video metadata harvesting
- Direct video URL / ID comment scraping
- Brand CSV and Excel dataset uploads
"""

from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
import pandas as pd

from src.youtube_scraper import (
    get_api_status,
    search_videos,
    scrape_video_comments,
    get_video_details,
    extract_video_id
)
from src.dataset_manager import (
    load_file_buffer,
    load_file_to_dataframe,
    validate_brand_dataset,
    reset_session_state,
    clean_comment_data,
    clean_video_metadata,
)


def render_page_collection():
    st.title("YouTube Social Media Data Collection")
    st.markdown("""
    Harvest live YouTube video metadata and user comment threads via the official **YouTube Data API v3**,
    or upload authentic brand social datasets.
    """)
    st.divider()

    # Active Brand Configuration Bar
    b_col1, b_col2 = st.columns([2, 1])
    brand_target = b_col1.text_input("Active Target Brand:", value=st.session_state.get("brand_name", "Audionic"), help="Brand name attributed to newly harvested data.")
    st.session_state["brand_name"] = brand_target
    platform_target = b_col2.selectbox("Platform:", ["YouTube", "Multi-Platform"], index=0)
    st.session_state["platform"] = platform_target

    api_stat = get_api_status()
    if not api_stat["configured"]:
        st.warning("""
        **Notice:** YouTube Data API key not configured in `.env`.
        You can enter an API key below for this session, or upload genuine brand datasets in Tab 3.
        """)
        user_key = st.text_input("Enter YouTube API Key (Optional for current session):", type="password")
    else:
        st.success(f"YouTube Data API is ready: `{api_stat['status_label']}`")
        user_key = None

    tab1, tab2, tab3 = st.tabs(["1. Keyword Video Search", "2. Video Comment Scraper", "3. Upload Brand Datasets"])

    # --- TAB 1: Search ---
    with tab1:
        st.subheader("Search Brand Videos by Keyword or Topic")
        st.caption("Search YouTube across any brand topic, campaign, or product line, extracting full metadata.")

        col_q, col_max, col_order = st.columns([3, 1, 1])
        default_q = f"{brand_target} reviews and unboxing" if brand_target else "Pakistan tech trends"
        query = col_q.text_input("Search Keyword / Query:", value=st.session_state.get("search_query", default_q))
        max_vids = col_max.slider("Max Videos:", min_value=5, max_value=50, value=15, step=5)
        order = col_order.selectbox("Sort By:", ["relevance", "date", "viewCount", "rating"])

        if st.button("🔍 Search & Harvest Video Metadata"):
            with st.spinner(f"Searching YouTube for '{query}'..."):
                v_df, err = search_videos(query=query, max_results=max_vids, order=order, api_key=user_key, brand_name=brand_target)
                if err:
                    st.error(f"Search Error: {err}")
                elif v_df.empty:
                    st.warning("No videos found matching your query.")
                else:
                    v_df["brand_name"] = brand_target
                    v_df["platform"] = platform_target
                    st.session_state["videos_data"] = v_df
                    st.session_state["videos_source"] = f"Live Search: '{query}'"
                    st.session_state["data_source"] = f"Live API Search ('{query}')"
                    st.session_state["search_query"] = query
                    st.session_state["collection_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                    # Persist to data/raw/videos
                    p_dir = Path("data/raw/videos")
                    p_dir.mkdir(parents=True, exist_ok=True)
                    fname = f"{brand_target.lower().replace(' ', '_')}_videos.csv"
                    v_df.to_csv(p_dir / fname, index=False, encoding="utf-8")

                    st.success(f"Successfully harvested metadata for {len(v_df)} videos for brand **{brand_target}**! Saved to `data/raw/videos/{fname}`.")

        v_current = st.session_state.get("videos_data")
        if v_current is not None and not v_current.empty:
            st.dataframe(v_current, use_container_width=True)
            csv_bytes = v_current.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Raw Videos CSV", data=csv_bytes, file_name=f"{brand_target.lower()}_raw_videos.csv", mime="text/csv")

    # --- TAB 2: Direct Comment Scraper ---
    with tab2:
        st.subheader("Collect Comments by Video URL or ID")
        st.caption("Harvest comment threads for a specific video with full pagination support and brand tagging.")

        col_u, col_c = st.columns([3, 1])
        video_input = col_u.text_input("YouTube Video URL or 11-char Video ID:", value="https://www.youtube.com/watch?v=k4yXQkG2s1E")
        max_comments = col_c.slider("Max Comments:", min_value=20, max_value=1000, value=100, step=20)

        if st.button("📥 Scrape Comments"):
            with st.spinner("Harvesting comments via YouTube Data API v3..."):
                c_df, err = scrape_video_comments(video_input, max_comments=max_comments, api_key=user_key, brand_name=brand_target, platform=platform_target)
                if err and (c_df is None or c_df.empty):
                    st.error(f"Scraper Notice: {err}")
                elif c_df is not None and not c_df.empty:
                    c_df["brand_name"] = brand_target
                    c_df["platform"] = platform_target
                    st.session_state["comments_data"] = c_df
                    vid = extract_video_id(video_input) or video_input
                    st.session_state["comments_source"] = f"Live Scrape (Video: {vid})"
                    st.session_state["data_source"] = f"Live Video Scrape ({vid})"
                    st.session_state["collection_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                    # Persist to data/raw/comments
                    c_dir = Path("data/raw/comments")
                    c_dir.mkdir(parents=True, exist_ok=True)
                    fname = f"{brand_target.lower().replace(' ', '_')}_comments.csv"
                    c_df.to_csv(c_dir / fname, index=False, encoding="utf-8")

                    st.success(f"Harvested {len(c_df):,} comments for brand **{brand_target}**! Saved to `data/raw/comments/{fname}`.")
                    if err:
                        st.info(f"API Note: {err}")

        c_current = st.session_state.get("comments_data")
        if c_current is not None and not c_current.empty:
            st.dataframe(c_current.head(50), use_container_width=True)
            c_bytes = c_current.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Raw Comments CSV", data=c_bytes, file_name=f"{brand_target.lower()}_raw_comments.csv", mime="text/csv")

    # --- TAB 3: File Upload ---
    with tab3:
        st.subheader("Upload Genuine Brand Social Datasets")
        st.caption("Upload verified CSV or Excel datasets for brand analytics.")

        uploaded = st.file_uploader("Choose a CSV or Excel file:", type=["csv", "xlsx", "xls"], key="collection_uploader")

        if uploaded:
            raw_df, err = load_file_to_dataframe(uploaded)
            if err:
                st.error(f"Error loading file: {err}")
            else:
                is_val, dtype, issues, stats = validate_brand_dataset(raw_df)
                if not is_val:
                    st.error("❌ Schema Validation Issues:")
                    for iss in issues:
                        st.write(f"- {iss}")
                else:
                    st.success(f"✅ Valid Brand {dtype.capitalize()} Dataset ({stats.get('rows', len(raw_df)):,} rows).")
                    if st.button("Activate Uploaded Brand Dataset", key="btn_activate_upload"):
                        raw_df["brand_name"] = brand_target
                        raw_df["platform"] = platform_target
                        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                        if dtype == "comments":
                            cleaned, c_metrics = clean_comment_data(raw_df)
                            st.session_state["comments_data"] = cleaned
                            st.session_state["comments_source"] = f"Upload: {uploaded.name}"
                            st.session_state["cleaning_audit"] = c_metrics
                        else:
                            cleaned, v_metrics = clean_video_metadata(raw_df)
                            st.session_state["videos_data"] = cleaned
                            st.session_state["videos_source"] = f"Upload: {uploaded.name}"
                            st.session_state["cleaning_audit"] = v_metrics

                        st.session_state["data_source"] = f"Uploaded Brand File ({uploaded.name})"
                        st.session_state["upload_filename"] = uploaded.name
                        st.session_state["collection_date"] = now_str

                        # Save into data/brand
                        b_dir = Path("data/brand")
                        b_dir.mkdir(parents=True, exist_ok=True)
                        save_p = b_dir / f"{brand_target.lower().replace(' ', '_')}_{uploaded.name}"
                        cleaned.to_csv(save_p, index=False, encoding="utf-8")

                        st.success(f"Activated brand dataset for **{brand_target}**!")
                        st.rerun()

        st.divider()
        if st.button("🔄 Clear Active Session Data"):
            reset_session_state()
            st.success("Session state cleared.")
            st.rerun()
