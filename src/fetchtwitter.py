import os
import pandas as pd
from datetime import datetime
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from src.config import STOCK_KEYWORDS, TWITTER_LANG
load_dotenv()
#PostgreSQL Connection 
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
# Twitter Setup 
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
#  Insert with deduplication 
def insert_df_to_db(df, table_name):
    if df.empty:
        return
    for _, row in df.iterrows():
        try:
            row.to_frame().T.to_sql(table_name, engine, if_exists="append", index=False)
        except IntegrityError:
            continue  # skip duplicates
#  Create Twitter search URL 
def create_url(query, max_results=10):
    return f"https://api.twitter.com/2/tweets/search/recent?query={query} lang:{TWITTER_LANG}&max_results={max_results}&tweet.fields=created_at,public_metrics,lang"
# Fetch Tweets
def fetch_twitter_tweets(max_results=10):
    all_tweets = []
    for keyword in STOCK_KEYWORDS:
        print(f"🐦 Fetching tweets for '{keyword}'...")
        url = create_url(keyword, max_results=max_results)
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"⚠️ Error fetching {keyword}: {response.json()}")
            continue

        data = response.json().get("data", [])
        for tweet in data:
            all_tweets.append({
                "id": tweet["id"],
                "source": "twitter",
                "keyword": keyword,
                "text": tweet["text"],
                "created_at": datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")),
                "retweets": tweet["public_metrics"]["retweet_count"],
                "likes": tweet["public_metrics"]["like_count"],
                "replies": tweet["public_metrics"]["reply_count"],
            })

    df = pd.DataFrame(all_tweets)
    insert_df_to_db(df, "twitter_tweets")
    print(f"✅ Tweets inserted (duplicates skipped).")
# === Run standalone ===
if __name__ == "__main__":
    fetch_twitter_tweets(max_results=10)
