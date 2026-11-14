"""
Page 6: Data Export & Automated Report Generation.
Allows exporting standardized brand datasets (CSV / Excel) and generating
publication-ready Markdown and JSON analytical audit reports.
"""

import io
from datetime import datetime, timezone
import streamlit as st
import pandas as pd

from src.inspection import inspect_dataset
from src.statistics import calculate_descriptive_statistics
from src.text_temporal import analyze_temporal, analyze_text
from src.sentiment_engine import analyze_youtube_sentiment
from src.report_gen import generate_pipeline_report


def render_page_exports():
    st.title("Data Export & Automated Reporting")
    st.markdown("""
    Export clean, standardized brand datasets in CSV or Excel formats, and download comprehensive
    audit summaries for research or integration into downstream Project 3 intelligence engines.
    """)
    st.divider()

    brand_name = st.session_state.get("brand_name", "Brand")
    data_source = st.session_state.get("data_source", "None")
    c_df = st.session_state.get("comments_data")
    v_df = st.session_state.get("videos_data")

    st.caption(f"**Target Brand:** {brand_name} | **Active Data Source:** {data_source}")

    if (c_df is None or c_df.empty) and (v_df is None or v_df.empty):
        st.info(f"ℹ️ **No active brand dataset loaded.** Active data directories are clean. Please harvest brand data in **Stage 2: YouTube Collection** or upload a verified brand dataset in **Stage 1: Overview** to enable exports.")
        return

    # 1. Dataset Downloads
    st.subheader(f"1. Export Standardized Datasets ({brand_name})")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{brand_name} Comments Dataset**")
        if c_df is not None and not c_df.empty:
            st.write(f"Active records: **{len(c_df):,} rows**")
            csv_comments = c_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Comments as CSV",
                data=csv_comments,
                file_name=f"{brand_name.lower().replace(' ', '_')}_comments_cleaned.csv",
                mime="text/csv"
            )

            # Excel buffer export
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                c_df.to_excel(writer, index=False, sheet_name="Comments")
            st.download_button(
                label="📥 Download Comments as Excel (.xlsx)",
                data=excel_buf.getvalue(),
                file_name=f"{brand_name.lower().replace(' ', '_')}_comments_cleaned.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No comments data loaded for active brand.")

    with col2:
        st.markdown(f"**{brand_name} Video/Post Metadata Dataset**")
        if v_df is not None and not v_df.empty:
            st.write(f"Active records: **{len(v_df):,} rows**")
            csv_videos = v_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Videos as CSV",
                data=csv_videos,
                file_name=f"{brand_name.lower().replace(' ', '_')}_videos_cleaned.csv",
                mime="text/csv"
            )

            excel_vbuf = io.BytesIO()
            with pd.ExcelWriter(excel_vbuf, engine="openpyxl") as writer:
                v_df.to_excel(writer, index=False, sheet_name="Videos")
            st.download_button(
                label="📥 Download Videos as Excel (.xlsx)",
                data=excel_vbuf.getvalue(),
                file_name=f"{brand_name.lower().replace(' ', '_')}_videos_cleaned.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No video/post metadata loaded for active brand.")

    st.divider()

    # 2. Automated Pipeline Report Generation
    st.subheader(f"2. Automated Markdown Pipeline Report ({brand_name})")
    target_report_df = c_df if c_df is not None and not c_df.empty else v_df
    if target_report_df is not None and not target_report_df.empty:
        insp = inspect_dataset(target_report_df)
        audit = st.session_state.get("cleaning_audit")
        stats = calculate_descriptive_statistics(target_report_df)
        temp = analyze_temporal(target_report_df)
        txt = analyze_text(target_report_df)
        
        sent_sum = None
        if c_df is not None and not c_df.empty:
            try:
                _, sent_sum = analyze_youtube_sentiment(c_df)
            except Exception:
                sent_sum = None

        report_md = generate_pipeline_report(
            inspection=insp,
            cleaning_metrics=audit,
            statistics=stats,
            temporal=temp,
            text_data=txt,
            sentiment=sent_sum,
            dataset_name=f"{brand_name} Social Audience Intelligence",
            output_path="outputs/pipeline_audit_report.md"
        )

        st.download_button(
            label="📄 Download Markdown Audit Report",
            data=report_md.encode("utf-8"),
            file_name=f"{brand_name.lower().replace(' ', '_')}_pipeline_report.md",
            mime="text/markdown"
        )

        with st.expander("👁️ Preview Markdown Report"):
            st.markdown(report_md)
