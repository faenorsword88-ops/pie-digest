import feedparser
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SOURCES = [
    ("Payments Dive", "https://www.paymentsdive.com/feeds/news/", 5),
    ("American Banker", "https://www.americanbanker.com/feed", 5),
    ("The Block", "https://www.theblock.co/rss.xml", 5),
    ("CFPB Newsroom", "https://www.consumerfinance.gov/about-us/newsroom/feed/", 5),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", 5),
    ("Finextra", "https://www.finextra.com/rss/headlines.aspx", 8),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/", 5),
    ("PYMNTS", "https://www.pymnts.com/feed/", 3),
    ("Banking Dive", "https://www.bankingdive.com/feeds/news/", 5),
    ("Reuters Finance", "https://feeds.reuters.com/reuters/financesNews", 5),
]

def init_db():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT UNIQUE,
        source TEXT,
        summary TEXT,
        published TEXT,
        fetched_at TEXT
    )''')
    conn.commit()
    return conn

def fetch_articles():
    conn = init_db()
    c = conn.cursor()
    new_count = 0

    for name, url, limit in SOURCES:
        print(f"Fetching {name}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")[:500]
            published = entry.get("published", str(datetime.now()))
            try:
                c.execute('''INSERT INTO articles
                    (title, url, source, summary, published, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (title, link, name, summary, published, str(datetime.now())))
                new_count += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()
    print(f"\nDone. {new_count} new articles saved.")

if __name__ == "__main__":
    fetch_articles()
