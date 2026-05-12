import feedparser
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

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

def fetch_articles():
    new_count = 0
    for name, url, limit in SOURCES:
        print(f"Fetching {name}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")[:500]

            try:
                supabase.table("articles").insert({
                    "title": title,
                    "url": link,
                    "source": name,
                    "summary": summary,
                    "fetched_at": datetime.now().isoformat()
                }).execute()
                new_count += 1
            except Exception:
                pass  # Duplicate URL, skip it

    print(f"\nDone. {new_count} new articles saved.")

if __name__ == "__main__":
    fetch_articles()
