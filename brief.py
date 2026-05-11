import sqlite3
import os
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

SYSTEM_PROMPT = """You are a briefing writer for a senior credit professional who moved from commercial banking into fintech. He deeply understands credit risk, capital allocation, unit economics, and regulatory pressure. He is building knowledge in payments infrastructure, card network economics, fintech business models, crypto infrastructure, and AI in financial services.

For each article write:
- A 4-6 line executive summary that connects the news to concepts he already understands from banking. Use analogies to credit risk, lending, capital markets, or regulation where helpful.
- One line: "Why this matters to you:" that is direct and specific to his world.
- If knowledge_gap_flag is true, add one line: "Knowledge builder:" that explains a concept this article illustrates.

Write in plain clear english. No hype. No jargon without explanation. Treat him as smart but new to this specific domain."""

def generate_brief():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    # Get scored articles - 3s first then 2s
    c.execute("""
        SELECT title, url, source, summary, score, score_reason, knowledge_gap_flag, gap_area
        FROM articles
        WHERE score >= 2
        AND source NOT IN ('Federal Reserve', 'CFPB Newsroom')
        ORDER BY score DESC, fetched_at DESC
    """)
    articles = c.fetchall()

    # Get primary source items scored below threshold or any score
    c.execute("""
        SELECT title, url, score
        FROM articles
        WHERE source IN ('Federal Reserve', 'CFPB Newsroom')
        ORDER BY score DESC
    """)
    primary_items = c.fetchall()

    print(f"Building digest from {len(articles)} articles...\n")

    # Build the prompt for Claude
    articles_text = ""
    for i, (title, url, source, summary, score, reason, gap_flag, gap_area) in enumerate(articles, 1):
        priority = "MUST READ" if score == 3 else "WORTH READING"
        gap = f"Knowledge gap area: {gap_area}" if gap_flag else ""
        articles_text += f"""
Article {i} [{priority}]
Source: {source}
Title: {title}
Summary: {summary}
Scorer note: {reason}
{gap}
URL: {url}
---"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Write a morning briefing for these articles:\n{articles_text}"}]
    )

    briefing_content = response.content[0].text

    # Build HTML
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    must_reads = [a for a in articles if a[4] == 3]
    worth_reads = [a for a in articles if a[4] == 2]

    # Primary source notice
    primary_notice = ""
    if primary_items:
        primary_notice = f"""
        <div class="primary-notice">
            📋 <strong>{len(primary_items)} Federal Reserve / CFPB items</strong> published today.
            <details>
                <summary>Review them</summary>
                <ul>
                    {"".join(f'<li><a href="{url}" target="_blank">[{score}] {title}</a></li>' for title, url, score in primary_items)}
                </ul>
            </details>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PIE Digest — {date_str}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f9f7f4;
            color: #2c2c2c;
            line-height: 1.7;
        }}
        h1 {{
            font-size: 1.4rem;
            border-bottom: 2px solid #2c2c2c;
            padding-bottom: 0.5rem;
            margin-bottom: 0.25rem;
        }}
        .date {{ color: #666; font-size: 0.9rem; margin-bottom: 2rem; }}
        .stats {{ font-size: 0.85rem; color: #666; margin-bottom: 2rem; }}
        .section-header {{
            font-size: 0.75rem;
            font-weight: bold;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #666;
            margin: 2rem 0 1rem 0;
            border-bottom: 1px solid #ddd;
            padding-bottom: 0.25rem;
        }}
        .article {{
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid #e8e4df;
        }}
        .article h2 {{
            font-size: 1.05rem;
            margin-bottom: 0.25rem;
        }}
        .article h2 a {{
            color: #2c2c2c;
            text-decoration: none;
        }}
        .article h2 a:hover {{ text-decoration: underline; }}
        .source {{ font-size: 0.8rem; color: #888; margin-bottom: 0.75rem; }}
        .must-read {{ border-left: 3px solid #c0392b; padding-left: 1rem; }}
        .worth-read {{ border-left: 3px solid #2980b9; padding-left: 1rem; }}
        .gap-flag {{
            display: inline-block;
            font-size: 0.7rem;
            background: #f0e6ff;
            color: #6c3483;
            padding: 0.1rem 0.4rem;
            border-radius: 3px;
            margin-left: 0.5rem;
        }}
        .primary-notice {{
            background: #fff8e1;
            border: 1px solid #ffe082;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            font-size: 0.85rem;
            margin-bottom: 2rem;
        }}
        .primary-notice details {{ margin-top: 0.5rem; }}
        .primary-notice ul {{ margin: 0.5rem 0 0 1rem; padding: 0; }}
        .primary-notice li {{ margin-bottom: 0.25rem; }}
        .primary-notice a {{ color: #555; }}
    </style>
</head>
<body>
    <h1>PIE Daily Digest</h1>
    <div class="date">{date_str}</div>
    <div class="stats">{len(must_reads)} must-read · {len(worth_reads)} worth reading · {len(primary_items)} primary source items</div>

    {primary_notice}

    <div class="section-header">Must Read — Structural Changes</div>
    {"".join(f'''
    <div class="article must-read">
        <h2><a href="{a[1]}" target="_blank">{a[0]}</a>{' <span class="gap-flag">🎯 knowledge builder</span>' if a[6] else ''}</h2>
        <div class="source">{a[2]}</div>
    </div>''' for a in must_reads)}

    <div class="section-header">Worth Reading — Useful Context</div>
    {"".join(f'''
    <div class="article worth-read">
        <h2><a href="{a[1]}" target="_blank">{a[0]}</a>{' <span class="gap-flag">🎯 knowledge builder</span>' if a[6] else ''}</h2>
        <div class="source">{a[2]}</div>
    </div>''' for a in worth_reads)}

    <div style="margin-top: 3rem; font-size: 0.75rem; color: #aaa;">
        Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} · PIE Digest
    </div>

    <div style="margin-top: 2rem; border-top: 1px solid #ddd; padding-top: 1.5rem;">
        <div class="section-header">Briefing</div>
        <div style="white-space: pre-wrap; font-size: 0.95rem;">{briefing_content}</div>
    </div>

</body>
</html>"""

    # Write the file
    output_path = os.path.expanduser("~/pie-digest/digest.html")
    with open(output_path, "w") as f:
        f.write(html)

    conn.close()
    print(f"Digest written to {output_path}")
    print(f"\nSummary: {len(must_reads)} must-read, {len(worth_reads)} worth reading, {len(primary_items)} primary source items")

if __name__ == "__main__":
    generate_brief()
