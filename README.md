📊 Sentiment Analyser

A real-time dashboard that fetches Reddit posts and News articles for stock-related keywords, performs sentiment analysis, and visualizes trends across sources.

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

<img width="1901" height="856" alt="image" src="https://github.com/user-attachments/assets/61177316-3b7d-4456-9704-f2f90547b2a2" />

