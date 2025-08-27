📊 Sentiment Analyser
A real-time dashboard that fetches Reddit posts and News articles for stock-related keywords, performs sentiment analysis, and visualizes trends across sources.

Demo

Click the "Fetch Latest Data" button to pull new Reddit posts and news articles, and see the sentiment comparison.

Features

✅ Fetch Reddit posts from relevant subreddits

✅ Fetch News articles via NewsAPI

✅ Perform sentiment analysis using VADER

✅ Label posts/articles as Positive / Negative / Neutral

✅ Compare sentiment across Reddit and News

✅ Interactive bar charts and summary tables in Streamlit

Getting Started (To run locally)
REQUIREMENTS: PostgreSQL, Reddit API Credentials, NewsAPI Credentials

To setup Reddit API:
Go to the Reddit Developer Portal : https://www.reddit.com/dev/api
Create an app 
The REDDIT_CLIENT_ID will be the string under:
<img width="307" height="105" alt="image" src="https://github.com/user-attachments/assets/d06ce684-fbe8-4f96-b55e-f6440948b3df" /> (Highlighted red box is the REDDIT_CLIENT_ID)
The REDDIT_CLIENT_SECRET will be near secret: in the app page.

To setup News API:
Go to the News API webpage : https://newsapi.org/
Click on Get API Key
Follow the steps to get your NEWS_API_KEY.

To setup PostgreSQL:
Download PostgreSQL from this site : https://www.postgresql.org/
Follow the steps and obtain your DB_USER, DB_PASSWORD, DB_HOST, DB_PORT and DB_NAME.

To setup the analyser locally:
1. Clone the repo
git clone <https://github.com/Addy0606/sentimentanalyser/>
cd sentimentanalyser

2. Create a virtual environment
python -m venv sentimentanalyser-venv
# Windows
sentimentanalyser-venv\Scripts\activate
# Mac/Linux
source sentimentanalyser-venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Copy the following lines , create a .env file in the main project directory, paste them there and fill in the variables with your corresponding credentials.
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent
NEWS_API_KEY=your_newsapi_key

5. Create PostgreSQL tables
In pgAdmin or SQL query tool, run the following commands
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

Run the App
streamlit run src/app.py


Open the URL displayed in the terminal (http://localhost:8501)

Click "🔄 Fetch Latest Data" to fetch, analyze, and display data

Project Structure
sentimentanalyser/
│
├─ src/
│   ├─__init__.py
│   ├─ app.py            # Streamlit dashboard
│   ├─ fetchreddit.py    # Reddit fetching module
│   ├─ fetchnews.py     # NewsAPI fetching module
│   ├─ sentiment.py      # Sentiment analysis & summary
│   └─ config.py         # Keywords and subreddits
│
├─ .env                # Environment variables (not in repo)
├─ .gitignore
├─ requirements.txt      # Python dependencies
└─ README.md

Notes
Free API limits: NewsAPI and Reddit API have request restrictions.
Make sure PostgreSQL is running and accessible.
