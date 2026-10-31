import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini safely
genai_available = False
model = None

try:
    import google.generativeai as genai
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        genai_available = True
except Exception as init_err:
    print(f"Notice: Gemini initialization deferred: {init_err}")

def get_gemini_summary_from_combined(combined_df: pd.DataFrame, keywords: list[str]):
    """
    Use Gemini (with robust analytical fallback) to generate financial sentiment summaries 
    based on combined Reddit & News data.
    """
    if combined_df is None or combined_df.empty:
        return "No data to summarize.", ""

    want_all = (not keywords) or (len(keywords) == 1 and keywords[0].strip().lower() == "all")
    kws = [k.strip().lower() for k in keywords] if not want_all else None

    df = combined_df.copy()
    if "keyword" not in df.columns:
        return "No matching keywords found to summarize.", ""

    df["keyword_lower"] = df["keyword"].astype(str).str.lower()

    if not want_all and kws:
        df = df[df["keyword_lower"].isin(kws)]

    if df.empty:
        return "No matching keywords found to summarize.", ""

    df = df.drop_duplicates(subset=["keyword_lower"])

    sentiment_data = []
    for _, row in df.iterrows():
        sentiment_data.append({
            "keyword": row["keyword"],
            "reddit_sent": round(float(row.get("avg_sentiment_reddit", 0) if pd.notnull(row.get("avg_sentiment_reddit")) else 0), 2),
            "news_sent": round(float(row.get("avg_sentiment_news", 0) if pd.notnull(row.get("avg_sentiment_news")) else 0), 2),
            "overall_sent": round(float(row.get("avg_sentiment_total", 0) if pd.notnull(row.get("avg_sentiment_total")) else 0), 2)
        })

    # Try Gemini API first
    if genai_available and model:
        try:
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
            if response and response.text:
                return response.text, sentiment_data
        except Exception as api_err:
            print(f"Notice: Gemini API call failed ({api_err}). Using automated analytical summary.")

    # Intelligent Analytical Fallback (Zero-crash guarantee)
    fallback_lines = ["### 📊 Market Sentiment Analysis Digest\n"]
    for item in sentiment_data:
        score = item["overall_sent"]
        if score >= 0.15:
            sentiment_label = "🟢 Bullish (Positive)"
        elif score <= -0.15:
            sentiment_label = "🔴 Bearish (Negative)"
        else:
            sentiment_label = "⚪ Neutral / Consolidation"

        divergence = abs(item["reddit_sent"] - item["news_sent"])
        if divergence >= 0.40:
            divergence_note = f" ⚠️ **High Retail vs Institutional Divergence** (Spread: {divergence:.2f})"
        else:
            divergence_note = ""

        fallback_lines.append(
            f"- **{item['keyword']}**: **{sentiment_label}** — Overall Score: `{score:+.2f}` "
            f"(Reddit: `{item['reddit_sent']:+.2f}` | News: `{item['news_sent']:+.2f}`){divergence_note}"
        )

    return "\n".join(fallback_lines), sentiment_data