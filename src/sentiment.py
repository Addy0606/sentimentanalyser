# src/sentiment.py
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", future=True)
analyzer = SentimentIntensityAnalyzer()
def analyze_sentiment(text):
    """Return compound sentiment score of the text"""
    return analyzer.polarity_scores(text)["compound"]
def process_table(table_name, text_column, id_column):
    """Fetch rows, analyze sentiment, and update DB"""
    df = pd.read_sql(f"SELECT * FROM {table_name};", engine)
    if df.empty:
        print(f"No rows in {table_name} to process.")
        return
    # Combine title and selftext
    df["combined_text"] = df["title"].fillna("") + " " + df["selftext"].fillna("")
    df["sentiment"] = df["combined_text"].apply(analyze_sentiment) 
    # Update database with new sentiment scores
    with engine.begin() as conn:  # automatically handles transaction
        for _, row in df.iterrows():
            stmt = text(f"""
                UPDATE {table_name}
                SET sentiment = :sentiment
                WHERE {id_column} = :row_id
            """)
            conn.execute(stmt, {"sentiment": row["sentiment"], "row_id": row[id_column]})

    print(f"✅ Sentiment analysis completed for {table_name}.")
if __name__ == "__main__":
    process_table("reddit_posts", "combined_text", "post_id")
