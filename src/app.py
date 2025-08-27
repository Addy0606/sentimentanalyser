import streamlit as st
import pandas as pd
import time

# Local imports
from fetchreddit import fetch_reddit_posts
from fetchnews import fetch_news_articles
from sentiment import process_table, get_label, keyword_sentiment_summary, engine
from sqlalchemy import text

# ---------------------------
# Streamlit Page Config
# ---------------------------
st.set_page_config(
    page_title="📊 Keyword Sentiment Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Title
# ---------------------------
st.title("📊 Keyword Sentiment Dashboard")
st.write("Compare sentiment trends across **Reddit** and **News Articles** in real-time.")

# ---------------------------
# Fetch Data Button
# ---------------------------
if st.button("🔄 Fetch Latest Data"):
    progress = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Fetch Reddit
        status_text.text("Fetching Reddit posts...")
        fetch_reddit_posts(limit=10)
        progress.progress(20)
        time.sleep(0.5)

        # Step 2: Fetch News
        status_text.text("Fetching News articles...")
        fetch_news_articles(limit_per_keyword=10)
        progress.progress(40)
        time.sleep(0.5)

        # Step 3: Sentiment analysis - Reddit
        status_text.text("Analyzing Reddit sentiments...")
        process_table("reddit_posts", "combined_text", "post_id")
        df = pd.read_sql("SELECT post_id, sentiment FROM reddit_posts;", engine)
        if not df.empty:
            df["label"] = df["sentiment"].apply(get_label)
            with engine.begin() as conn:
                for _, row in df.iterrows():
                    stmt = text("""
                        UPDATE reddit_posts
                        SET label = :label
                        WHERE post_id = :row_id
                    """)
                    conn.execute(stmt, {"label": row["label"], "row_id": row["post_id"]})

        progress.progress(60)
        time.sleep(0.5)

        # Step 4: Sentiment analysis - News
        status_text.text("Analyzing News sentiments...")
        process_table("news_posts", "combined_text", "id")
        df = pd.read_sql("SELECT id, sentiment FROM news_posts;", engine)
        if not df.empty:
            df["label"] = df["sentiment"].apply(get_label)
            with engine.begin() as conn:
                for _, row in df.iterrows():
                    stmt = text("""
                        UPDATE news_posts
                        SET label = :label
                        WHERE id = :row_id
                    """)
                    conn.execute(stmt, {"label": row["label"], "row_id": row["id"]})

        progress.progress(90)
        time.sleep(0.5)

        status_text.text("✅ Data fetched and analyzed successfully!")
        progress.progress(100)
        time.sleep(0.5)

    except Exception as e:
        st.error(f"❌ Error while fetching or analyzing data: {e}")
    finally:
        progress.empty()
        status_text.empty()

# ---------------------------
# Display Sentiment Summary
# ---------------------------
st.subheader("📌 Sentiment Summary by Keyword")

# Get latest sentiment summary
reddit_df = keyword_sentiment_summary("reddit_posts", source="reddit")
news_df = keyword_sentiment_summary("news_posts", source="news")

df = pd.concat([reddit_df, news_df])


if df.empty:
    st.warning("⚠️ No data available yet. Please fetch latest data.")
else:
    # Split Reddit & News
    reddit_df = df[df["source"] == "reddit"]
    news_df = df[df["source"] == "news"]

    # Merge Reddit + News for comparison
    combined_df = pd.merge(
        reddit_df,
        news_df,
        on="keyword",
        how="outer",
        suffixes=("_reddit", "_news")
    )

    # Calculate overall average sentiment
    combined_df["avg_sentiment_total"] = combined_df[
        ["avg_sentiment_reddit", "avg_sentiment_news"]
    ].mean(axis=1)

    # Display table
    st.dataframe(combined_df, use_container_width=True)

    # Chart
    st.subheader("📈 Sentiment Comparison")
    chart_df = combined_df[
        ["keyword", "avg_sentiment_reddit", "avg_sentiment_news", "avg_sentiment_total"]
    ].set_index("keyword")
    st.bar_chart(chart_df)

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.caption("Made with ❤️ using Streamlit, Reddit API, NewsAPI, and Sentiment Analysis")
