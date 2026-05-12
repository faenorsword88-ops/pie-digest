import sqlite3
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

SYSTEM_PROMPT = """You are a news scoring assistant for a senior credit professional who recently moved from commercial banking into fintech. He understands credit risk, capital allocation, unit economics, and regulatory pressure deeply. He is building knowledge in payments infrastructure, card network economics, fintech business models, crypto infrastructure, and AI in financial services.

Score each article 1-3:
3 = Something structurally changed. A regulator acted, infrastructure shifted, major capital moved, or a business model changed in a way that matters. He needs to know this.
2 = Useful context. Worth reading, builds knowledge, relevant to his world.
1 = Noise. Drama, speculation, price chatter, conference promos, or gossip with no structural impact.

Also flag if the article touches his specific knowledge gaps:
- Payments infrastructure (how money actually moves)
- Card network economics (Visa/Mastercard/interchange dynamics)
- Credit in a tech context (BNPL, embedded lending, underwriting models)
- Fintech regulation (CFPB, OCC, Fed actions)
- AI applied to financial services

Respond only in JSON, no other text:
{
  "score": 1-3,
  "reason": "one sentence explanation",
  "knowledge_gap_flag": true/false,
  "gap_area": "which gap area or null"
}"""

def score_articles():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    # Add scoring columns if they don't exist
    try:
        c.execute("ALTER TABLE articles ADD COLUMN score INTEGER")
        c.execute("ALTER TABLE articles ADD COLUMN score_reason TEXT")
        c.execute("ALTER TABLE articles ADD COLUMN knowledge_gap_flag INTEGER")
        c.execute("ALTER TABLE articles ADD COLUMN gap_area TEXT")
        conn.commit()
    except:
        pass

    # Get unscored articles
    c.execute("SELECT id, title, summary, source FROM articles WHERE score IS NULL")
    articles = c.fetchall()

    print(f"Scoring {len(articles)} articles...\n")

    for article_id, title, summary, source in articles:
        prompt = f"Source: {source}\nTitle: {title}\nSummary: {summary}"

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)

            score = result.get("score", 1)
            reason = result.get("reason", "")
            gap_flag = 1 if result.get("knowledge_gap_flag") else 0
            gap_area = result.get("gap_area", None)

            c.execute("""UPDATE articles
                SET score=?, score_reason=?, knowledge_gap_flag=?, gap_area=?
                WHERE id=?""",
                (score, reason, gap_flag, gap_area, article_id))
            conn.commit()

            flag = "🎯" if gap_flag else "  "
            print(f"[{score}] {flag} {title[:60]}")

        except Exception as e:
            print(f"Error scoring '{title[:40]}': {e}")

    conn.close()
    print("\nScoring complete.")

if __name__ == "__main__":
    score_articles()
