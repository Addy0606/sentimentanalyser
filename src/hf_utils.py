import os
import google.generativeai as genai
import pandas as pd
genai.configure(api_key=os.getenv("GOOGLE_API_KEY","AIzaSyB25kdhoc_KAfPF4_TOEyK96MoX0Y3LxJE"))
model = genai.GenerativeModel("gemini-1.5-flash")
def get_gemini_summary_from_combined(combined_df: pd.DataFrame, keywords: list[str]):
    """
    Use Gemini to generate financial sentiment summaries based on combined Reddit & News data.
    """
    if combined_df is None or combined_df.empty:
        return "No data to summarize.", ""

    want_all = (not keywords) or (len(keywords) == 1 and keywords[0].strip().lower() == "all")
    kws = [k.strip().lower() for k in keywords] if not want_all else None

    df = combined_df.copy()
    df["keyword_lower"] = df["keyword"].str.lower()

    if not want_all:
        df = df[df["keyword_lower"].isin(kws)]

    if df.empty:
        return "No matching keywords found to summarize.", ""

    df = df.drop_duplicates(subset=["keyword_lower"])


    sentiment_data = []
    for _, row in df.iterrows():
        sentiment_data.append({
            "keyword": row["keyword"],
            "reddit_sent": round(float(row.get("avg_sentiment_reddit", 0)), 2),
            "news_sent": round(float(row.get("avg_sentiment_news", 0)), 2),
            "overall_sent": round(float(row.get("avg_sentiment_total", 0)), 2)
        })

    prompt = f"""
    You are a financial sentiment analyst.

    Given the following sentiment scores (range -1 to 1, where >0 = positive, <0 = negative, 0 = neutral),
    summarize the outlook for each keyword in a clear, concise way.

    Sentiment data:
    {sentiment_data}

    For each keyword, give:
    - Overall sentiment ("Positive", "Negative", or "Neutral")
    - Brief reasoning using Reddit and News scores
    - Keep it short and bullet-pointed.
    """

    response = model.generate_content(prompt)
    return response.text, sentiment_data
