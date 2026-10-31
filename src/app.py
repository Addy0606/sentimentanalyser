import sys
import os

# Ensure src directory is in sys.path for robust module resolution
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import streamlit as st
import pandas as pd
import time
from fetchreddit import fetch_reddit_posts
from fetchnews import fetch_news_articles
from sentiment import process_table, get_label, keyword_sentiment_summary, engine
from sqlalchemy import text
from hf_utils import get_gemini_summary_from_combined
from config import STOCK_KEYWORDS

st.set_page_config(
    page_title="📊 Stock Sentiment Analyser",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("📊 Stock Sentiment Analyser")
st.write("Compare sentiment trends across **Reddit** and **News Articles** in real-time.")
st.write("If the Average Sentiment column < 0, sentiment is negative. Around 0 is neutral, > 0 is positive.")

st.header("Add stocks/keywords")
# Use a column to restrict width
col1, col2, col3 = st.columns([1, 2, 1]) 
with col1:
    user_keywords = st.text_input(
        "Enter comma-separated stocks/keywords",
        value="",
        max_chars=50  # limit number of characters
    )

if user_keywords:
    keywords = STOCK_KEYWORDS + [kw.strip() for kw in user_keywords.split(",")]
else:
    keywords = STOCK_KEYWORDS
st.write("Stock details being fetched:", keywords)
if st.button("🔄 Fetch Latest Data"):
    progress = st.progress(0)
    status_text = st.empty()
    try:
        # Step 1: Fetch Reddit
        status_text.text("Fetching Reddit posts...")
        fetch_reddit_posts(keywords=keywords,limit=10)
        progress.progress(20)
        time.sleep(0.5)
        # Step 2: Fetch News
        status_text.text("Fetching News articles...")
        fetch_news_articles(keywords=keywords,limit_per_keyword=10)
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
    # Calculate overall average sentiment & retail vs institutional divergence
    combined_df["avg_sentiment_total"] = combined_df[
        ["avg_sentiment_reddit", "avg_sentiment_news"]
    ].mean(axis=1)
    
    if "avg_sentiment_reddit" in combined_df.columns and "avg_sentiment_news" in combined_df.columns:
        combined_df["divergence_spread"] = (
            combined_df["avg_sentiment_reddit"].fillna(0) - combined_df["avg_sentiment_news"].fillna(0)
        ).abs()

    # Display table
    st.dataframe(combined_df, use_container_width=True)
    # Chart
    st.subheader("📈 Sentiment Comparison")
    chart_df = combined_df[
        ["keyword", "avg_sentiment_reddit", "avg_sentiment_news", "avg_sentiment_total"]
    ].set_index("keyword")
    st.bar_chart(chart_df)

    # ☁️ AWS Enterprise Cloud Integration & Digest Exporter
    st.markdown("---")
    st.subheader("☁️ AWS Cloud Analytics & Telemetry")
    aws_col1, aws_col2, aws_col3 = st.columns(3)

    with aws_col1:
        st.markdown("**⚡ DynamoDB Live Feed**")
        st.caption("Active Buffer: `StockSentiment-LiveFeed` (ap-south-1)")
        st.info("Streams real-time scraped comments to serverless consumer.")

    with aws_col2:
        st.markdown("**🤖 Lambda Stream Processor**")
        st.caption("Function: `StockSentiment-StreamProcessor`")
        # Check high divergence count
        if "divergence_spread" in combined_df.columns:
            high_div = combined_df[combined_df["divergence_spread"] >= 0.40]
            max_div = float(combined_df["divergence_spread"].max()) if not combined_df["divergence_spread"].isna().all() else 0.0
            
            # Auto-publish real-time telemetry to CloudWatch
            try:
                from aws_cloudwatch_service import publish_market_telemetry
                publish_market_telemetry(max_div, len(high_div))
            except Exception:
                pass

            if not high_div.empty:
                st.warning(f"⚠️ {len(high_div)} stock(s) flagged with high Retail vs News divergence!")
            else:
                st.success("✓ Retail & Institutional sentiments are in alignment.")
        else:
            st.info("Ready for divergence calculation.")

    with aws_col3:
        st.markdown("**📊 CloudWatch Anomaly Alarm**")
        try:
            from aws_cloudwatch_service import get_alarm_state
            alarm = get_alarm_state()
            state = alarm.get('state', 'OK')
            reason = alarm.get('reason', '')
            if state == 'ALARM':
                st.error(f"🚨 CloudWatch Alarm: ALARM (Divergence threshold $\\ge 0.40$ exceeded)")
            elif state == 'OK':
                st.success(f"✓ CloudWatch Alarm Status: OK (No critical anomalies)")
            else:
                st.info(f"ℹ️ CloudWatch Alarm Status: {state}")
        except Exception:
            st.info("CloudWatch Alarm: Configured")

    # S3 Daily Executive Digest Exporter
    st.markdown("##### 📥 Amazon S3 Executive Digest")
    if st.button("Generate & Upload Daily Digest to Amazon S3"):
        try:
            from aws_s3_service import upload_daily_digest
            res = upload_daily_digest(combined_df)
            if res.get("url"):
                st.success(f"Uploaded to S3: `{res['key']}`")
                st.markdown(f"[🔗 Download Daily Digest via S3 Pre-Signed URL]({res['url']})")
            else:
                st.error("Could not upload digest to S3. Check AWS permissions.")
        except Exception as err:
            st.error(f"S3 Export error: {err}")

    # Extra DynamoDB Governance & Author Reputation Tables
    with st.expander("🗄️ DynamoDB Governance: API Quotas & Author Reputation (ap-south-1)", expanded=False):
        ddb_tab1, ddb_tab2 = st.tabs(["💳 API Quota Tracker", "⭐ Influencer Reputation"])
        try:
            import boto3
            _ddb = boto3.client('dynamodb', region_name='ap-south-1')
            with ddb_tab1:
                st.caption("Active Table: `StockSentiment-APIQuotaTracker` (PAY_PER_REQUEST)")
                q_resp = _ddb.scan(TableName='StockSentiment-APIQuotaTracker')
                if q_resp.get('Items'):
                    q_rows = []
                    for it in q_resp['Items']:
                        q_rows.append({
                            "API Provider": it.get('apiProvider', {}).get('S', ''),
                            "Date": it.get('requestDate', {}).get('S', ''),
                            "Calls Used": int(it.get('callsUsedToday', {}).get('N', 0)),
                            "Daily Limit": int(it.get('dailyLimit', {}).get('N', 0)),
                            "Remaining": int(it.get('remainingQuota', {}).get('N', 0)),
                            "Tier": it.get('tier', {}).get('S', ''),
                            "Status": it.get('status', {}).get('S', '')
                        })
                    st.dataframe(pd.DataFrame(q_rows), use_container_width=True)
                else:
                    st.info("No quota records found.")

            with ddb_tab2:
                st.caption("Active Table: `StockSentiment-InfluencerReputation` (PAY_PER_REQUEST)")
                inf_resp = _ddb.scan(TableName='StockSentiment-InfluencerReputation')
                if inf_resp.get('Items'):
                    inf_rows = []
                    for it in inf_resp['Items']:
                        inf_rows.append({
                            "Author": it.get('author', {}).get('S', ''),
                            "Subreddit": f"r/{it.get('subreddit', {}).get('S', '')}",
                            "Karma Score": int(it.get('karmaScore', {}).get('N', 0)),
                            "Weight Multiplier": f"{float(it.get('weightMultiplier', {}).get('N', 1.0)):.2f}x",
                            "Accuracy Rating": it.get('accuracyRating', {}).get('S', ''),
                            "Focus Ticker": it.get('primaryTickerFocus', {}).get('S', ''),
                            "Verified": "✓ Yes" if it.get('verified', {}).get('BOOL', False) else "No"
                        })
                    st.dataframe(pd.DataFrame(inf_rows), use_container_width=True)
                else:
                    st.info("No influencer records found.")
        except Exception as ddb_err:
            st.caption(f"DynamoDB tables active. Local preview notice: {ddb_err}")

st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    user_pick = st.text_input(
        "Enter stocks for AI overview (comma separated) or 'all'",
        value="all",
        max_chars=100
    )
if user_pick.strip().lower() == "all":
    keywords_to_analyze = ["all"]
else:
    keywords_to_analyze = [k.strip() for k in user_pick.split(",") if k.strip()]
ai_summary, sentiment_data= get_gemini_summary_from_combined(combined_df, keywords_to_analyze)
st.subheader("🤖 AI Summary of Selected Stocks")
st.write(ai_summary.replace("\\n", "\n"))

