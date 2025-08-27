import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from praw import Reddit
from config import STOCK_KEYWORDS, REDDIT_SUBREDDITS
load_dotenv()
# PostgreSQL Connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
# Reddit Setup 
reddit = Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)
#  Insert with deduplication 
def insert_df_to_db(df, table_name):
    if df.empty:
        print("No posts to insert.")
        return
    
    inserted = 0
    skipped = 0
    
    for _, row in df.iterrows():
        try:
            # convert the row to DataFrame and insert
            row.to_frame().T.to_sql(table_name, engine, if_exists="append", index=False)
            inserted += 1
        except IntegrityError:
            skipped += 1  # duplicate based on PK
        except SQLAlchemyError as e:
            print("Error inserting row:", e)
            skipped += 1
    
    print(f"✅ Inserted {inserted} rows, skipped {skipped} duplicates or errors.")
# Fetch Reddit Posts
def fetch_reddit_posts(limit=10):
    count=0
    maxposts=10
    all_posts = []
    for subreddit in REDDIT_SUBREDDITS:
        for keyword in STOCK_KEYWORDS:
            print(f"📥 Fetching posts for '{keyword}' from r/{subreddit}...")
            for post in reddit.subreddit(subreddit).search(keyword, limit=limit):
                all_posts.append({
                    "post_id": post.id,
                    "subreddit": subreddit,
                    "keyword": keyword,
                    "title": post.title,
                    "url": post.url,
                    "created_utc": datetime.utcfromtimestamp(post.created_utc),
                    "selftext": post.selftext
                })
                count+=1
                if count>=maxposts:
                    break
    df = pd.DataFrame(all_posts)
    insert_df_to_db(df, "reddit_posts")
    print(f"✅ Reddit posts inserted (duplicates skipped).")
# Run standalone 
if __name__ == "__main__":
    fetch_reddit_posts(limit=10)
