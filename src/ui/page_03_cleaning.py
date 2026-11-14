"""
Page 3: Data Cleaning & Preprocessing.
Executes standardized data cleaning, whitespace normalization, ISO 8601 timestamp conversion,
and deduplication for video metadata and comment datasets.
"""

from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
import pandas as pd
from src.cleaner import clean_comment_data, clean_video_metadata
from src.inspection import inspect_dataset
from src.dataset_manager import load_file_to_dataframe, validate_brand_dataset


def render_page_cleaning():
    st.title("Data Cleaning & Preprocessing Engine")
    st.markdown("""
    Standardize raw social media datasets by stripping invalid whitespace, parsing ISO 8601 UTC dates,
    coercing numeric engagement counts, and removing duplicate records while preserving legitimate repeated comments.
    """)
    st.divider()

    brand_name = st.session_state.get("brand_name", "None")
    data_source = st.session_state.get("data_source", "None")

    st.caption(f"**Target Brand:** {brand_name} | **Active Data Source:** {data_source}")

    dataset_choice = st.radio("Select Active Dataset to Clean:", ["Comments Dataset", "Videos Dataset"], horizontal=True)

    if dataset_choice == "Comments Dataset":
        target_df = st.session_state.get("comments_data")
        source_label = st.session_state.get("comments_source", "None")
    else:
        target_df = st.session_state.get("videos_data")
        source_label = st.session_state.get("videos_source", "None")

    if target_df is None or target_df.empty:
        st.info(f"ℹ️ **No active {dataset_choice.lower()} loaded.** Active directories are clean. You can upload an uncleaned dataset below or collect live data in **Stage 2: YouTube Collection**.")

        with st.expander(f"📥 Quick Upload {dataset_choice}", expanded=True):
            up = st.file_uploader(f"Choose a {dataset_choice.lower()} file (CSV or Excel):", type=["csv", "xlsx", "xls"], key="clean_quick_up")
            if up:
                raw_df, err = load_file_to_dataframe(up)
                if err:
                    st.error(f"Upload error: {err}")
                else:
                    is_val, dtype, issues, stats = validate_brand_dataset(raw_df)
                    if not is_val:
                        st.error("Validation issues: " + "; ".join(issues))
                    else:
                        if st.button("Load and Inspect"):
                            raw_df["brand_name"] = brand_name
                            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                            if dtype == "comments":
                                st.session_state["comments_data"] = raw_df
                                st.session_state["comments_source"] = f"Uploaded Raw: {up.name}"
                            else:
                                st.session_state["videos_data"] = raw_df
                                st.session_state["videos_source"] = f"Uploaded Raw: {up.name}"
                            st.session_state["data_source"] = f"Uploaded File ({up.name})"
                            st.session_state["upload_filename"] = up.name
                            st.session_state["collection_date"] = now_str
                            st.rerun()
        return

    st.subheader(f"1. Raw Dataset Inspection: {source_label}")
    raw_insp = inspect_dataset(target_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Raw Rows", f"{raw_insp['total_rows']:,}")
    col2.metric("Raw Columns", f"{raw_insp['total_columns']}")
    col3.metric("Full Duplicates", f"{raw_insp['full_duplicate_rows']}")
    col4.metric("Memory Footprint", f"{raw_insp['memory_mb']:.2f} MB")

    with st.expander("🔍 Inspect Raw Missing Values and Data Types"):
        col_df = pd.DataFrame.from_dict(raw_insp["column_inspection"], orient="index")
        st.dataframe(col_df, use_container_width=True)

    st.divider()

    st.subheader("2. Execute Standardized Preprocessing Pipeline")
    if st.button("🧹 Run Cleaning & Standardization Pipeline", type="primary"):
        with st.spinner("Executing cleaning transformations..."):
            if dataset_choice == "Comments Dataset":
                cleaned_df, metrics = clean_comment_data(target_df)
                cleaned_df["brand_name"] = brand_name
                st.session_state["comments_data"] = cleaned_df
                st.session_state["comments_source"] = f"Cleaned: {source_label}"
                # Save to processed
                p_dir = Path("data/processed/comments")
                p_dir.mkdir(parents=True, exist_ok=True)
                cleaned_df.to_csv(p_dir / f"cleaned_{brand_name.lower().replace(' ', '_')}_comments.csv", index=False, encoding="utf-8")
            else:
                cleaned_df, metrics = clean_video_metadata(target_df)
                cleaned_df["brand_name"] = brand_name
                st.session_state["videos_data"] = cleaned_df
                st.session_state["videos_source"] = f"Cleaned: {source_label}"
                # Save to processed
                p_dir = Path("data/processed/videos")
                p_dir.mkdir(parents=True, exist_ok=True)
                cleaned_df.to_csv(p_dir / f"cleaned_{brand_name.lower().replace(' ', '_')}_videos.csv", index=False, encoding="utf-8")

            st.session_state["cleaning_audit"] = metrics
            st.success(f"Cleaning pipeline executed successfully! Cleaned data saved to `data/processed/`.")

    audit = st.session_state.get("cleaning_audit")
    if audit:
        st.subheader("3. Cleaning & Integrity Audit Log")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Initial Rows", f"{audit.get('initial_rows', 0):,}")
        m_col2.metric("Final Rows", f"{audit.get('final_rows', 0):,}")
        m_col3.metric("Dropped Duplicates", f"{audit.get('dropped_duplicates', 0):,}")
        if "repeated_comment_texts" in audit:
            m_col4.metric("Preserved Repetitions", f"{audit.get('repeated_comment_texts', 0):,}")
        else:
            m_col4.metric("Schema Type", audit.get("dataset_type", "Standard"))

        st.markdown("**Standardized Dataset Preview:**")
        st.dataframe(target_df.head(25), use_container_width=True)

        clean_csv = target_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Cleaned Dataset (CSV)",
            data=clean_csv,
            file_name=f"cleaned_{brand_name.lower()}_{dataset_choice.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )
