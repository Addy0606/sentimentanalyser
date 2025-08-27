import os
from sqlalchemy import text
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
    
    # Combine text depending on table
    if table_name == "reddit_posts":
        df["combined_text"] = df["title"].fillna("") + " " + df["selftext"].fillna("")
    elif table_name == "news_posts":
        df["combined_text"] = df["title"].fillna("") + " " + df["description"].fillna("")
    else:
        df["combined_text"] = df[text_column].fillna("")
    
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
def get_label(score):
        if score > 0:
            return "Positive"
        elif score < 0:
            return "Negative"
        else:
            return "Neutral"
def keyword_sentiment_summary(table_name="reddit_posts", source=None):
    query = f"""
    SELECT 
        keyword,
        COUNT(*) AS post_count,
        AVG(sentiment) AS avg_sentiment,
        SUM(CASE WHEN label = 'Positive' THEN 1 ELSE 0 END) AS positive_count,
        SUM(CASE WHEN label = 'Negative' THEN 1 ELSE 0 END) AS negative_count,
        SUM(CASE WHEN label = 'Neutral' THEN 1 ELSE 0 END) AS neutral_count
    FROM {table_name}
    GROUP BY keyword
    ORDER BY post_count DESC;
    """
    df = pd.read_sql(query, engine)
    
    if source:
        df["source"] = source
    
    return df
if __name__ == "__main__":
    process_table("reddit_posts", "combined_text", "post_id")
    # Add sentiment labels after sentiment scores have been updated
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
        print("✅ Sentiment labels added to reddit_posts.")
    keyword_sentiment_summary("reddit_posts")
    process_table("news_posts", "combined_text", "id")  # 'id' is PK in news_posts
    # Add sentiment labels after sentiment scores have been updated
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
        print("✅ Sentiment labels added to news_posts.")
    keyword_sentiment_summary("news_posts")
    

