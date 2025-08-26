import os
import tweepy
from dotenv import load_dotenv

load_dotenv()


TWITTER_BEARER = os.getenv("TWITTER_BEARER")

if not TWITTER_BEARER:
    raise RuntimeError("Missing TWITTER_BEARER token in .env!")


client = tweepy.Client(bearer_token=TWITTER_BEARER)

def fetch_tweets(query, max_results=20):
    """
    Fetch tweets based on a search query.
    """
    response = client.search_recent_tweets(
        query=query,
        max_results=max_results,
        tweet_fields=["id", "text", "created_at", "author_id", "lang"]
    )

    tweets = []
    if response.data:
        for tweet in response.data:
            tweets.append({
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "author_id": tweet.author_id,
                "lang": tweet.lang
            })
    return tweets

if __name__ == "__main__":
    tweets = fetch_tweets("AI OR ChatGPT")
    for t in tweets:
        print(t)
