"""
Page 5: Sentiment Analysis & Lexical Text Mining (Optional Supporting Module).
Performs lexicon-based sentiment polarity classification and keyword tokenization across brand commentary.
Academic Disclaimer:
Rule-based sentiment scores serve as an exploratory qualitative indicator,
not as human-annotated ground truth.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.sentiment_engine import analyze_youtube_sentiment
from src.text_temporal import analyze_text


def render_page_sentiment():
    st.title("Sentiment Analysis & Lexical Mining (Optional Module)")
    st.info("""
    **Methodological Scope & Academic Disclaimer:**  
    This is an optional supporting module utilizing a rule-based lexicon with negation inversion.
    It provides an exploratory qualitative pulse of audience sentiment and keyword vocabulary,
    serving as a baseline signal rather than definitive ground-truth annotation.
    """)
    st.divider()

    brand_name = st.session_state.get("brand_name", "None")
    data_source = st.session_state.get("data_source", "None")

    st.caption(f"**Target Brand:** {brand_name} | **Active Data Source:** {data_source}")

    df = st.session_state.get("comments_data")
    if df is None or df.empty:
        st.info(f"ℹ️ **No active comments loaded for brand '{brand_name}'.** Active directories are clean. Please harvest brand comments in **Stage 2: YouTube Collection** or upload a genuine brand dataset on **Stage 1: Overview**.")
        return

    # 1. Execute Sentiment Analysis
    st.subheader(f"1. Audience Sentiment Distribution ({brand_name})")
    with st.spinner("Evaluating comment sentiment polarity..."):
        try:
            sent_df, summary = analyze_youtube_sentiment(df)
        except Exception as e:
            st.error(f"Sentiment Analysis Error: {str(e)}")
            return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Analyzed Comments", f"{summary['total_comments']:,}")
    col2.metric("Positive Comments", f"{summary['positive_pct']:.1f}%", f"{summary['positive_count']:,} rows")
    col3.metric("Neutral Comments", f"{summary['neutral_pct']:.1f}%", f"{summary['neutral_count']:,} rows")
    col4.metric("Negative Comments", f"{summary['negative_pct']:.1f}%", f"{summary['negative_count']:,} rows")

    # 2. Charts
    c_pie, c_hist = st.columns(2)
    with c_pie:
        pie_df = pd.DataFrame({
            "Sentiment": ["Positive", "Neutral", "Negative"],
            "Count": [summary["positive_count"], summary["neutral_count"], summary["negative_count"]]
        })
        fig_pie = px.pie(
            pie_df,
            names="Sentiment",
            values="Count",
            title=f"{brand_name}: Sentiment Category Voice Share",
            color="Sentiment",
            color_discrete_map={"Positive": "#27ae60", "Neutral": "#95a5a6", "Negative": "#e74c3c"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_hist:
        fig_hist = px.histogram(
            sent_df,
            x="polarity",
            nbins=30,
            title=f"{brand_name}: Polarity Score Distribution [-1.0 to +1.0]",
            color_discrete_sequence=["#3498db"],
            labels={"polarity": "Continuous Polarity"}
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # 3. Dynamic Lexical Mining
    st.subheader(f"2. Lexical Keyword Frequency for {brand_name}")
    text_data = analyze_text(df)

    if text_data and text_data.get("top_keywords"):
        kw_df = pd.DataFrame(text_data["top_keywords"]).head(15)
        fig_kw = px.bar(
            kw_df,
            x="count",
            y="keyword",
            orientation="h",
            title=f"Top 15 Most Frequent Comment Keywords - {brand_name}",
            color="count",
            color_continuous_scale="Blues"
        )
        fig_kw.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_kw, use_container_width=True)

    # 4. Filterable Comments Viewer
    st.divider()
    st.subheader(f"3. Explore Comments by Sentiment for {brand_name}")
    selected_sent = st.selectbox("Filter Sentiment Category:", ["All", "Positive", "Neutral", "Negative"])
    filtered_df = sent_df if selected_sent == "All" else sent_df[sent_df["sentiment"] == selected_sent]

    show_cols = [c for c in ["author", "comment_text", "likes", "reply_count", "polarity", "sentiment"] if c in filtered_df.columns]
    st.dataframe(filtered_df[show_cols].head(50), use_container_width=True)
