"""
YouTube Social Media Data Collection & Preprocessing Pipeline
Streamlit Master Application.

A modular, multi-paradigm data engineering pipeline for harvesting, cleaning,
and analyzing YouTube video metadata and user comments.
Foundation for Project 3: Pakistan Social Audience & Campaign Intelligence Engine.
"""

import streamlit as st

# Configure Streamlit page layout
st.set_page_config(
    page_title="YouTube Data Collection & Preprocessing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize in-memory session state
from src.dataset_manager import initialize_session_state
initialize_session_state()

# Import the 6 modular UI page renderers
from src.ui.page_01_overview import render_page_overview
from src.ui.page_02_collection import render_page_collection
from src.ui.page_03_cleaning import render_page_cleaning
from src.ui.page_04_engagement import render_page_engagement
from src.ui.page_05_sentiment import render_page_sentiment
from src.ui.page_06_exports import render_page_exports

# Master 6-Page Navigation Registry
PAGES = {
    "1. Overview & Architecture": render_page_overview,
    "2. YouTube Data Collection": render_page_collection,
    "3. Data Cleaning & Preprocessing": render_page_cleaning,
    "4. Engagement Analytics": render_page_engagement,
    "5. Sentiment Analysis (Optional)": render_page_sentiment,
    "6. Data Export & Reports": render_page_exports,
}

# Sidebar Navigation Hub
with st.sidebar:
    st.title("Navigation Hub")
    st.markdown("**Project 3: Brand Intelligence Engine**")
    
    selected_page_title = st.selectbox(
        "Select Pipeline Stage:",
        list(PAGES.keys()),
        index=0
    )
    
    st.divider()
    
    # Active Brand Provenance & Telemetry
    b_name = st.session_state.get("brand_name", "None")
    plat = st.session_state.get("platform", "YouTube")
    src = st.session_state.get("data_source", "None")
    fname = st.session_state.get("upload_filename", "None")
    c_df = st.session_state.get("comments_data")
    v_df = st.session_state.get("videos_data")
    
    st.markdown("### Brand Provenance")
    st.caption(f"**Target Brand:** {b_name}")
    st.caption(f"**Platform:** {plat}")
    st.caption(f"**Data Source:** {src}")
    if fname != "None":
        st.caption(f"**File:** `{fname}`")
    
    st.divider()
    st.markdown("### Active Telemetry")
    st.caption(f"**Brand Comments:** {len(c_df):,} rows" if c_df is not None else "**Brand Comments:** None (Empty)")
    st.caption(f"**Brand Posts/Videos:** {len(v_df):,} rows" if v_df is not None else "**Brand Posts/Videos:** None (Empty)")
    
    audit = st.session_state.get("cleaning_audit")
    if audit:
        st.caption(f"**Duplicates Dropped:** {audit.get('dropped_duplicates', 0)}")
    
    st.divider()
    st.caption("DS391 Big Data Analytics | Project 3 Foundation")

# Execute active page renderer
renderer = PAGES[selected_page_title]
renderer()
