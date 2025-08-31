📊 Sentiment Analyser Dashboard
Overview:

The Sentiment Analyser Dashboard is a data-driven web application built with Streamlit that collects Reddit posts and news articles, performs sentiment analysis, and provides interactive visualizations to help users understand market sentiment around specific keywords.

Users can:

Fetch Reddit and news data for selected keywords.

Analyze sentiment (positive, negative, neutral) using NLP techniques.

Visualize trends through charts, tables, and summaries.

Customize analysis by adding their own keywords dynamically.

This project demonstrates the integration of data collection, storage, processing, visualization, and interactivity in a seamless workflow.

✨ Key Features

🔍 Keyword-based sentiment analysis on Reddit + news data.

📥 Automatic data fetching from Reddit & news APIs.

📊 Interactive visualizations (bar charts, tables, sentiment summaries).

📝 User-defined keywords via Streamlit UI.

🗄 Persistent storage using PostgreSQL.

⚡ Fast and lightweight dashboard powered by Streamlit.

🛠 Technologies Used:
Frontend / Dashboard:

Streamlit
 → For building the interactive web UI.

Backend & Data Collection:

PRAW / Reddit API → To fetch Reddit posts.

News API → To fetch latest news headlines.

Requests → For making API calls.

JSON → Handling API responses.

Data Processing & Analysis

Pandas → Data wrangling and summarization.

NumPy → Numeric computations.

VADER Sentiment Analyzer → Rule-based sentiment classification.

Database:

PostgreSQL → Storing Reddit + news posts and sentiment results.

SQLAlchemy → ORM for database interaction.

Visualization:

Matplotlib / Plotly → Charts and graphs.

Streamlit Tables / DataFrames → Interactive data exploration.

Environment & Project Structure:

Python 3.10+

🔹 Demo

Click the "Fetch Latest Data" button to pull new Reddit posts and News articles and see the sentiment comparison.

🔹 Features

✅ Fetch Reddit posts from relevant subreddits

✅ Fetch News articles via NewsAPI

✅ Perform sentiment analysis using VADER

✅ Label posts/articles as Positive / Negative / Neutral

✅ Compare sentiment across Reddit and News

✅ Interactive bar charts and summary tables in Streamlit

⚙️ Getting Started (Local Setup)

Requirements: PostgreSQL, Reddit API credentials, NewsAPI credentials

1. Setup Reddit API

Go to Reddit Developer Portal

Create an app

Copy REDDIT_CLIENT_ID (highlighted in the app page)

Copy REDDIT_CLIENT_SECRET

Set a REDDIT_USER_AGENT (any descriptive string)

2. Setup NewsAPI

Go to NewsAPI

Click Get API Key

Copy your NEWS_API_KEY

3. Setup PostgreSQL

Download PostgreSQL from postgresql.org

Create a database and note: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

4. Clone the repo
git clone https://github.com/Addy0606/sentimentanalyser/
cd sentimentanalyser

5. Create a virtual environment
python -m venv sentimentanalyser-venv
# Windows
sentimentanalyser-venv\Scripts\activate
# Mac/Linux
source sentimentanalyser-venv/bin/activate

6. Install dependencies
pip install -r requirements.txt

7. Configure environment variables

Create a .env file in the main project directory with:

DB_USER=your_postgres_user

DB_PASSWORD=your_postgres_password

DB_HOST=localhost

DB_PORT=5432

DB_NAME=your_db_name

REDDIT_CLIENT_ID=your_reddit_client_id

REDDIT_CLIENT_SECRET=your_reddit_client_secret

REDDIT_USER_AGENT=your_reddit_user_agent

NEWS_API_KEY=your_newsapi_key

8. Create PostgreSQL tables

Reddit Posts Table

CREATE TABLE reddit_posts (
    post_id TEXT PRIMARY KEY,
    subreddit TEXT,
    keyword TEXT,
    title TEXT,
    url TEXT,
    created_utc TIMESTAMP,
    selftext TEXT,
    sentiment FLOAT,
    label TEXT
);


News Posts Table

CREATE TABLE news_posts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    url TEXT,
    published_at TIMESTAMP,
    source TEXT,
    keyword TEXT,
    description TEXT,
    content TEXT,
    sentiment FLOAT,
    label TEXT
);

▶️ Run the App
streamlit run src/app.py


Open the URL displayed in the terminal (usually http://localhost:8501)

Add stocks/keywords as desired.

Click "🔄 Fetch Latest Data" to fetch, analyze, and display data.

📁 Project Structure
sentimentanalyser/
│

├─ src/

│   ├─ __init__.py

│   ├─ app.py            # Streamlit dashboard

│   ├─ fetchreddit.py    # Reddit fetching module

│   ├─ fetchnews.py      # NewsAPI fetching module

│   ├─ sentiment.py      # Sentiment analysis & summary

│   └─ config.py         # Keywords and subreddits

│
├─ .env                  # Environment variables (not in repo)

├─ .gitignore

├─ requirements.txt      # Python dependencies

└─ README.md

⚠️ Notes

Free API limits: NewsAPI and Reddit API have request restrictions

Ensure PostgreSQL is running and accessible before fetching data

<img width="1917" height="854" alt="image" src="https://github.com/user-attachments/assets/0ea2fdda-7b4e-4c09-81a4-8fe1987c8df2" />

<img width="1919" height="814" alt="image" src="https://github.com/user-attachments/assets/a218469a-416c-47c6-b844-328c7123a58b" />



