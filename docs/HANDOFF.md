# PIE Digest — Session Handoff Document
*For the next Claude session. Read this fully before making any suggestions.*

---

## Who You Are Talking To

Senior credit professional, recently moved from commercial banking into fintech. Deep background in credit risk, capital allocation, unit economics, regulatory pressure, and commercial portfolio management. Actively building technical literacy. Comfortable in terminal, recently pushed and merged his first code at work. Uses GitHub daily. Learning Python as a stretch project. Not a developer but not intimidated either.

His goal: become dangerous in a room full of tech people. Stop being caught off-guard by fintech concepts, payments infrastructure, and AI discussions. He comes from a world where he never thought about payment systems ("like the sewer — I just don't think about it").

**How to work with him:**
- Be direct and adversarial when needed — he responded well to pushback
- Don't over-engineer. He caught us doing this multiple times.
- He will push back if you spiral or contradict yourself. Good.
- He thinks in terms of ROI and sustainability: "will I actually use this?"
- Make decisions cleanly. When you have a recommendation, say it directly.
- Don't cross streams — if you start giving a code block, finish it cleanly before pivoting

---

## Current State — What Is Fully Working

The pipeline runs end-to-end automatically every weekday at 6am EST via GitHub Actions:

1. **collect.py** — fetches articles from 10 RSS sources, saves to Supabase
2. **score.py** — scores unscored articles 1-3 using Claude API, writes scores back to Supabase
3. **brief.py** — pulls scored articles, generates HTML digest via Claude API, writes index.html
4. **GitHub Actions** — deploys index.html to GitHub Pages on main branch

**Digest URL:** `https://faenorsword88-ops.github.io/pie-digest`
**GitHub repo:** `https://github.com/faenorsword88-ops/pie-digest` (public)
**Local location:** `~/pie-digest` on Ubuntu/WSL
**Database:** Supabase (cloud Postgres) — articles persist permanently across runs

---

## Current File Structure

```
pie-digest/
├── collect.py          # Fetches RSS, inserts to Supabase
├── score.py            # Scores unscored articles via Claude API, updates Supabase
├── brief.py            # Generates HTML digest from Supabase data
├── .env                # ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY (local only, gitignored)
├── .gitignore
├── index.html          # Generated digest, pushed to GitHub Pages
├── venv/               # Local only
└── .github/
    └── workflows/
        └── daily_digest.yml
```

**memory.db is gone.** SQLite has been fully replaced by Supabase. Do not reference it.

---

## GitHub Secrets (All Three Required)

| Secret Name | What It Is |
|-------------|------------|
| ANTHROPIC_API_KEY | Claude API key |
| SUPABASE_URL | Base URL only — `https://rjewhspxxduqlxflfubi.supabase.co` — NO trailing slash, NO /rest/v1/ |
| SUPABASE_KEY | Supabase secret key (not the publishable/anon key) |

---

## Supabase Setup

- **Project name:** pie-digest
- **Region:** East US
- **Table:** articles
- **RLS:** disabled (single user tool, no need for row-level security)

**Articles table schema:**
```sql
CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source TEXT,
    summary TEXT,
    score INTEGER,
    score_reason TEXT,
    knowledge_gap_flag BOOLEAN DEFAULT FALSE,
    gap_area TEXT,
    fetched_at TIMESTAMP DEFAULT NOW(),
    scored_at TIMESTAMP
);
```

---

## Key Design Decisions — Do Not Revisit Without Good Reason

**Scoring model: 1-3 only**
Rejected a complex weighted 5-dimension model. Simple is more reliable. 1 = noise, 2 = useful context, 3 = structural change.

**Fed/CFPB articles get a separate footer notice**
Not scored out, just surfaced separately. Maximum credibility sources but wildly variable content relevance.

**Sources (current):**
- Payments Dive (5), American Banker (5), The Block (5), CFPB Newsroom (5), Federal Reserve (5), Finextra (8), MIT Tech Review (5), PYMNTS (3), Banking Dive (5), Reuters Finance (5)
- Cut: TechCrunch (noise ratio too high), a16z (VC marketing dressed as insight)

**Delivery: GitHub Pages on main branch**
Rejected: CLI, email, Notion. Actions deploys directly to main — no gh-pages branch.

**Stack: Python + Supabase + GitHub Actions + GitHub Pages**
Free, works, already deployed.

---

## Next Session Priorities (In Order)

### 1. Fix Brief Layout (Start Here)
**The problem:** Claude's briefing content is generated as one large text block and dumped at the bottom of the page. It should appear as individual summaries directly under each article they describe.

**What needs building:**
- Prompt Claude in brief.py to return structured JSON — one summary object per article
- Parse the response and slot each summary under its article in the HTML
- This is a brief.py change only, maybe 30 minutes of work

### 2. Fix score.py Null Filter (Important — Will Degrade Over Time)
**The problem:** The correct Supabase null filter syntax (`is_("score", "null")` and `.filter("score", "is", "null")`) both returned PGRST125 errors. Current workaround pulls ALL articles from Supabase and filters for nulls in Python:
```python
response = supabase.table("articles").select("id, title, summary, source").execute()
articles = [a for a in response.data if a.get("score") is None]
```
This works now but will get slow as the database grows to thousands of rows. The correct fix is finding the right Supabase Python client syntax for IS NULL filtering. Worth investigating before the table gets large.

### 3. Build run.sh
Wrap local pipeline into one command:
```bash
python3 collect.py && python3 score.py && python3 brief.py
```
Into a `run.sh` script so local usage is one command instead of three.

### 4. Update LEARNING.md
Capture everything from session 2 — Supabase setup, the errors hit and how they were fixed, what PGRST125 means, git force push, the rebase conflict.

### 5. Knowledge Ramp (Longer Term)
Structured curriculum alongside the daily digest for payments infrastructure and card economics gaps. Not started. Worth revisiting once layout and scoring are solid.

---

## Technical Hiccups From Session 2 — Be Aware

**SUPABASE_URL must be base URL only**
Strip `/rest/v1/` from the end. The Supabase dashboard shows the full REST endpoint in some places. GitHub Secret and .env must have only `https://rjewhspxxduqlxflfubi.supabase.co`.

**Supabase null filter syntax is broken**
Both `.is_("score", "null")` and `.filter("score", "is", "null")` return PGRST125. Current fix is pull-all-filter-in-Python. See Priority #2 above.

**Git force push was used**
Local and remote diverged due to edits made directly in GitHub UI during the session. Resolved with `git rebase --abort` followed by `git push origin main --force`. Clean now.

**collect.py silently swallows insert errors**
The bare `except Exception: pass` on inserts means duplicate URL conflicts are silently skipped — which is correct behavior — but also means real connection failures are invisible locally. If collect.py ever returns 0 new articles unexpectedly, check that SUPABASE_URL and SUPABASE_KEY are loaded correctly.

**daily_digest.yml bookmark**
The .github folder is hidden on mobile GitHub. Bookmark this directly:
`https://github.com/faenorsword88-ops/pie-digest/blob/main/.github/workflows/daily_digest.yml`

**Claude API returns ```json markdown fences**
score.py strips these before parsing. Keep this line:
```python
raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
```

**Model name**
Using `claude-haiku-4-5-20251001` for scoring and briefing. Verify this is still current if errors appear.

**venv is fragile**
If the project folder moves, venv breaks. Recreate with:
```bash
python3 -m venv venv && source venv/bin/activate && pip install feedparser anthropic python-dotenv supabase
```

**nano is unreliable in WSL**
Use `echo` for single lines and `cat > file << 'EOF'` for full files.

---

## A Note to the Next Session

Two sessions in. The foundation is now genuinely solid — data persists, automation works end to end, Supabase is wired up correctly.

The next session is mostly refinement: fix the layout so summaries appear inline, fix the null filter before the table gets large, and build run.sh. None of these are hard.

Be decisive. When you have a recommendation, make it. Don't spiral on options. The user catches it every time and calls it out directly.

The user is genuinely learning. Explain what you're doing as you go. He wants to understand every line eventually.
