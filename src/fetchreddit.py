import os
import pandas as pd
from datetime import datetime
from praw import Reddit
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Ensure .env is loaded regardless of current working directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

try:
    from config import STOCK_KEYWORDS, REDDIT_SUBREDDITS
except ModuleNotFoundError:
    from src.config import STOCK_KEYWORDS, REDDIT_SUBREDDITS

# PostgreSQL Connection
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sentimentanalyser")
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
        except (IntegrityError, SQLAlchemyError):
            skipped += 1  # duplicate based on PK
        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                skipped += 1
            else:
                print("Error inserting row:", e)
                skipped += 1
    
    print(f"✅ Inserted {inserted} rows, skipped {skipped} duplicates or errors.")
# Fetch Reddit Posts
def fetch_reddit_posts(keywords=None,limit=10):
    if keywords is None:
        from config import STOCK_KEYWORDS
        keywords=STOCK_KEYWORDS
    count=0
    maxposts=10
    all_posts = []
    for subreddit in REDDIT_SUBREDDITS:
        if count >= maxposts:
            break
        for keyword in keywords:
            if count >= maxposts:
                break
            print(f"📥 Fetching posts for '{keyword}' from r/{subreddit}...")
            try:
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
                    count += 1
                    if count >= maxposts:
                        break
            except Exception as search_err:
                print(f"Warning: Reddit search for '{keyword}' in '{subreddit}' failed: {search_err}")
                continue
    df = pd.DataFrame(all_posts)
    insert_df_to_db(df, "reddit_posts")
    print(f"✅ Reddit posts inserted (duplicates skipped).")

    # AWS S3 Data Lake Archive Hook
    try:
        from aws_s3_service import archive_raw_payload
        s3_key = archive_raw_payload("reddit", all_posts)
        if s3_key:
            print(f"☁️ Archived Reddit payload to S3: {s3_key}")
    except Exception as s3_err:
        pass

# Run standalone 
if __name__ == "__main__":
    fetch_reddit_posts(limit=10)
