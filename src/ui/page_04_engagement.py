"""
Page 4: Engagement Analytics & Attention Inequality.
Evaluates parametric/non-parametric statistics, Gini coefficient (G),
percentile distributions, and temporal pacing across brand social data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.statistics import calculate_descriptive_statistics
from src.text_temporal import analyze_temporal


def render_page_engagement():
    st.title("Engagement Analytics & Attention Inequality")
    st.markdown("""
    Quantify audience attention distribution, parametric moments, engagement concentration,
    and longitudinal activity pacing across brand social commentary.
    """)
    st.divider()

    brand_name = st.session_state.get("brand_name", "None")
    data_source = st.session_state.get("data_source", "None")

    st.caption(f"**Target Brand:** {brand_name} | **Active Data Source:** {data_source}")

    df = st.session_state.get("comments_data")
    if df is None or df.empty:
        st.info(f"ℹ️ **No active comments dataset loaded for brand '{brand_name}'.** Active directories are clean. Please harvest brand comments via **Stage 2: YouTube Collection** or upload a genuine brand dataset on **Stage 1: Overview**.")
        return

    # 1. Descriptive Statistics & Inequality
    st.subheader(f"1. Descriptive Engagement Statistics ({brand_name})")
    stats = calculate_descriptive_statistics(df)

    if "likes" in stats:
        likes_s = stats["likes"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean Likes", f"{likes_s['mean']:.2f}")
        c2.metric("Median Likes", f"{likes_s['median']:.1f}")
        c3.metric("Gini Coefficient (G)", f"{likes_s['gini_coefficient']:.4f}")
        c4.metric("Top 1% Like Share", f"{likes_s['top_1_pct_share']:.1f}%")

        st.caption(f"""
        **Gini Coefficient Analysis ($G = {likes_s['gini_coefficient']:.4f}$):**  
        A Gini coefficient near 1.0 represents extreme Pareto attention concentration, where a small minority of brand comments
        captures the vast majority of community reactions, while {likes_s['zero_pct']}% of comments receive zero likes.
        """)

    with st.expander("📊 Full Statistical Moments (Likes & Replies)"):
        stat_rows = []
        for metric, data in stats.items():
            if isinstance(data, dict) and "mean" in data:
                row = {"Metric": metric}
                row.update(data)
                stat_rows.append(row)
        if stat_rows:
            st.dataframe(pd.DataFrame(stat_rows), use_container_width=True)

    st.divider()

    # 2. Visual Distributions
    st.subheader("2. Engagement Distribution Visualizations")
    if "likes" in df.columns:
        likes_data = pd.to_numeric(df["likes"], errors="coerce").dropna()
        if not likes_data.empty:
            fig_hist = px.histogram(
                x=likes_data,
                nbins=30,
                log_y=True,
                title=f"Like Count Distribution - {brand_name} (Logarithmic Scale)",
                labels={"x": "Likes", "y": "Log Frequency"},
                color_discrete_sequence=["#1f77b4"]
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # 3. Temporal Activity Trends
    st.divider()
    st.subheader("3. Temporal Pacing Analysis")
    temp_data = analyze_temporal(df)

    if temp_data and temp_data.get("yearly_distribution"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            dow_df = pd.DataFrame(list(temp_data["day_of_week_distribution"].items()), columns=["Day", "Comments"])
            fig_dow = px.bar(dow_df, x="Day", y="Comments", title=f"{brand_name}: Activity by Day of Week", color_discrete_sequence=["#2ca02c"])
            st.plotly_chart(fig_dow, use_container_width=True)

        with col_t2:
            hour_df = pd.DataFrame(list(temp_data["hour_of_day_distribution_utc"].items()), columns=["Hour (UTC)", "Comments"])
            fig_hour = px.line(hour_df, x="Hour (UTC)", y="Comments", title=f"{brand_name}: Activity by Hour of Day (UTC)", markers=True)
            st.plotly_chart(fig_hour, use_container_width=True)

    # 4. Top Outlier Comments
    st.divider()
    st.subheader(f"4. Top Engaged Comments for {brand_name}")
    top_liked = stats.get("top_5_liked_comments", [])
    if top_liked:
        st.dataframe(pd.DataFrame(top_liked), use_container_width=True)
