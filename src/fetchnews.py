# src/fetch_news.py
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import requests
from src.config import STOCK_KEYWORDS

load_dotenv()

# PostgreSQL connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"

def insert_df_to_db(df, table_name):
    if df.empty:
        print("No news articles to insert.")
        return

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            row.to_frame().T.to_sql(table_name, engine, if_exists="append", index=False)
            inserted += 1
        except IntegrityError:
            skipped += 1
        except SQLAlchemyError as e:
            print("Error inserting row:", e)
            skipped += 1

    print(f"✅ Inserted {inserted} rows, skipped {skipped} duplicates or errors.")

def fetch_news_articles(limit_per_keyword=10):
    all_articles = []

    for keyword in STOCK_KEYWORDS:
        print(f"📥 Fetching news for '{keyword}'...")
        params = {
            "q": keyword,
            "apiKey": NEWS_API_KEY,
            "pageSize": limit_per_keyword,
            "language": "en",
            "sortBy": "publishedAt"
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if data.get("status") != "ok" or not data.get("articles"):
            continue

        for article in data["articles"]:
            all_articles.append({
                "title": article.get("title"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "source": article.get("source", {}).get("name"),
                "keyword": keyword,
                "description": article.get("description"),
                "content": article.get("content")
            })

    df = pd.DataFrame(all_articles)
    insert_df_to_db(df, "news_posts")
    print(f"✅ News articles inserted (duplicates skipped).")

if __name__ == "__main__":
    fetch_news_articles(limit_per_keyword=10)
