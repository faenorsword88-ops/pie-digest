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

---

## What Was Built in Session 1

A fully working Personal Intelligence Engine (PIE) that:

1. Fetches articles from 10 curated RSS sources (collect.py)
2. Scores each article 1-3 using Claude API (score.py)
3. Generates an HTML digest written for his banking background (brief.py)
4. Runs automatically every weekday at 6am EST via GitHub Actions
5. Serves the digest at: `https://faenorsword88-ops.github.io/pie-digest`

**GitHub repo:** `https://github.com/faenorsword88-ops/pie-digest` (public)

**Local location:** `~/pie-digest` on Ubuntu/WSL

---

## Current File Structure

```
pie-digest/
├── collect.py
├── score.py  
├── brief.py
├── .env                    # API key, local only, gitignored
├── .gitignore
├── memory.db               # SQLite database, local only, gitignored
├── index.html              # Generated digest, pushed to GitHub Pages
├── venv/                   # Local only
└── .github/
    └── workflows/
        └── daily_digest.yml
```

---

## Key Design Decisions — Do Not Revisit Without Good Reason

**Scoring model: 1-3 only**
Rejected a complex weighted 5-dimension model. Reason: weird weights remove articles he needs to see. Simple is more reliable. 1 = noise, 2 = useful context, 3 = structural change.

**Fed/CFPB articles get a separate footer notice**
Not scored out, just surfaced separately. Maximum credibility sources but wildly variable content relevance.

**Sources (current):**
- Payments Dive (5), American Banker (5), The Block (5), CFPB Newsroom (5), Federal Reserve (5), Finextra (8), MIT Tech Review (5), PYMNTS (3), Banking Dive (5), Reuters Finance (5)
- Cut: TechCrunch (noise ratio too high), a16z (VC marketing dressed as insight)

**Delivery: GitHub Pages**
Rejected: CLI (already lives in terminal at work), email ("I won't open it"), Notion (awkward as feed reader).

**Stack: Python + SQLite + GitHub Actions + GitHub Pages**
Free, works, already deployed.

---

## What Is NOT Done Yet — Next Session Priorities

### 1. Long-term Archive (Most Important)
**The problem:** GitHub Actions doesn't persist memory.db between runs. Every morning it starts fresh, scores new articles, and the database is wiped at the end of the run. Historical articles are lost.

**What was agreed:** Supabase (free tier Postgres) as the database. Reasons:
- Free tier is genuinely generous
- Postgres is what his company calls "core" — good learning tool
- Cloud-based so GitHub Actions can write to it
- Scales to future projects (guitar agent, astronomy database, etc.)
- SQLite stays for local development, Supabase for production

**What needs building:**
- Supabase project setup
- Replace SQLite writes in collect.py and score.py with Supabase inserts
- Add SUPABASE_URL and SUPABASE_KEY to GitHub Secrets
- Build a simple archive/search page

### 2. Single Run Script
Wrap the three commands into one:
```bash
python3 collect.py && python3 score.py && python3 brief.py
```
Into a single `run.sh` script so local usage is one command.

### 3. GitHub Actions Database Fix
Currently the Actions workflow runs but loses all data between runs because memory.db is gitignored and not persisted. This is broken until Supabase is wired up.

### 4. Knowledge Ramp (Longer Term)
He has knowledge gaps in payments infrastructure and card economics specifically. There was discussion of building a structured curriculum alongside the daily digest. Not started. Worth revisiting once the pipeline is solid.

---

## Technical Hiccups to Be Aware Of

**Claude API returns ```json markdown fences**
score.py strips these before parsing. If you rewrite score.py make sure this stays:
```python
raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
```

**Model name**
Using `claude-haiku-4-5-20251001` for scoring (fast, cheap). Using same for briefing. Check current model names — they change.

**venv is fragile**
If the project folder moves, venv breaks. Always recreate with:
```bash
python3 -m venv venv && source venv/bin/activate && pip install feedparser anthropic python-dotenv
```

**nano is unreliable in WSL**
Use `echo` for single lines and `cat > file << 'EOF'` for full files. Don't send him into nano.

**paste in terminal**
Right-click to paste in WSL terminal. Ctrl+Shift+V is unreliable. Keep commands short enough to paste cleanly.

---

## A Note to the Next Session

The previous session made good decisions but also spiralled a few times — on model names, on the Notion vs GitHub Pages vs Supabase debate, on hosting options. The user caught all of it and called it out directly.

Be decisive. When you have a recommendation, make it. When you're uncertain, say so cleanly rather than generating four contradictory options.

The Supabase direction was well-reasoned and agreed upon. Don't second-guess it without a compelling reason. But also: he specifically said "encourage the new session to make its own decisions." So read this as context, not constraint. If you see something we got wrong, say so.

The user is genuinely learning. He wants to understand every line of code eventually, not just have things built for him. Explain as you go. The LEARNING.md document in this repo captures what was covered in session 1.

The pipeline works. The foundation is solid. Next session is about persistence, automation that actually works end to end, and starting to think about what the second project looks like.
