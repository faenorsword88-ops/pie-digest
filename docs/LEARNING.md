# PIE Digest — What We Built and What We Learned

## What This Project Actually Is
A personal intelligence engine that:
- Fetches articles from curated RSS feeds every morning
- Scores them 1-3 using Claude API (signal vs noise)
- Generates a plain-English digest written for a credit professional learning fintech
- Serves it as a webpage you can bookmark on your phone
- Runs automatically every weekday at 6am via GitHub Actions

---

## The Stack and Why We Chose It

| Tool | Job | Why |
|------|-----|-----|
| Python | Scripts that run the pipeline | Readable, widely used, good libraries |
| feedparser | Pulls RSS feeds | Simple, reliable, no API needed |
| anthropic | Talks to Claude API | Scoring and briefing generation |
| python-dotenv | Reads .env file for API key | Keeps secrets out of code |
| SQLite (memory.db) | Local article database | Built into Python, no setup needed |
| GitHub | Code storage + automation | Free, version controlled |
| GitHub Actions | Runs pipeline automatically | Free on public repos, cron scheduling |
| GitHub Pages | Serves the digest as a webpage | Free, instant, works on phone |

---

## Project File Structure

```
pie-digest/
├── collect.py          # Fetches articles from RSS, saves to memory.db
├── score.py            # Scores each article 1-3 using Claude API
├── brief.py            # Generates HTML digest from scored articles
├── .env                # Your API key (NEVER pushed to GitHub)
├── .gitignore          # Tells git what to ignore (.env, memory.db, venv/)
├── memory.db           # SQLite database (local only, gitignored)
├── index.html          # Generated digest (pushed to GitHub Pages)
├── venv/               # Python virtual environment (local only)
└── .github/
    └── workflows/
        └── daily_digest.yml   # GitHub Actions automation
```

---

## Key Design Decisions and Why

**Scoring 1-3 instead of weighted dimensions**
We originally considered a complex 5-dimension weighted scoring model. We rejected it because weighted scores can remove articles you need to see due to a weird weight somewhere. Simple is more reliable. 1 = noise, 2 = useful context, 3 = something structurally changed.

**Fed and CFPB get a separate treatment**
These are maximum credibility sources but content ranges from market-moving to routine bank merger approvals. Instead of forcing the scorer to handle this, the digest shows a collapsible notice: "X Federal Reserve/CFPB items today" so you're never blindsided but not forced to read everything.

**Cut TechCrunch and a16z**
TechCrunch: high noise ratio, conference promos, gossip. Proven immediately when 3 of 5 first articles were ads.
a16z: VC firm publishing content to move markets and recruit. Dressed as insight, actually marketing.

**Public GitHub repo**
Code is harmless. .env is gitignored so API key never touches GitHub. Being public unlocks free GitHub Actions and GitHub Pages.

**No CLI, no email, no Notion for delivery**
CLI: already living in terminal at work, don't need it at home.
Email: "I just won't open it, I know me."
Notion: good for documents, awkward as a feed reader.
Result: clean HTML page at a bookmarkable URL.

---

## How the Pipeline Works (Plain English)

**collect.py**
- Loops through the SOURCES list
- For each source, parses the RSS feed using feedparser
- Takes the top N articles (varies by source quality)
- Saves title, URL, source, summary, and timestamp to memory.db
- Skips duplicates (UNIQUE constraint on URL)

**score.py**
- Pulls all unscored articles from memory.db
- For each article, sends title + summary to Claude API
- Claude returns JSON: score (1-3), reason, knowledge_gap_flag, gap_area
- Saves scores back to memory.db
- Strips markdown code fences from Claude response before JSON parsing (```json wrapping issue)

**brief.py**
- Pulls all articles scored 2+ from memory.db (excluding Fed/CFPB which get separate treatment)
- Sends them all to Claude API with your background context in the system prompt
- Claude writes executive summaries connecting news to banking concepts you already know
- Builds an HTML page with must-reads (score 3) and worth-reading (score 2) sections
- Writes index.html which GitHub Pages serves as your digest URL

---

## Hiccups We Hit and How We Fixed Them

### The venv breaking after moving folders
**What happened:** We moved ~/pie-digest to ~/pie-digest-old and cloned a fresh repo. The terminal still showed (venv) in the prompt but venv was pointing to the old folder path which no longer existed.

**How we identified it:** Every Python command returned `-bash: /home/dmron/pie-digest/venv/bin/python3: No such file or directory` — the path in the error was the old location, not the new one. The (venv) prompt was a ghost.

**How we fixed it:**
```bash
deactivate                    # exit the broken venv
python3 -m venv venv          # create fresh venv in new location
source venv/bin/activate      # activate the real one
pip install feedparser anthropic python-dotenv   # reinstall packages
```

**Lesson:** When you move a project folder, the venv always breaks. Always recreate it. Venvs are not portable — they contain hardcoded absolute paths.

### API key truncation
**What happened:** Anthropic console displays a truncated key with `...` in the middle. Copied that instead of the full key. Got 401 authentication errors on every API call.

**How we fixed it:** Delete the key in Anthropic console, create a new one, copy the FULL string the moment it appears before clicking away. It only shows the complete key once at creation.

**Lesson:** API keys only show in full at creation. Save them immediately to a password manager or .env file before doing anything else.

### Claude returning ```json instead of raw JSON
**What happened:** Score.py was getting `Expecting value: line 1 column 1` JSON parse errors even though the API key was working. Claude was wrapping responses in markdown code fences (```json ... ```) despite being told to return only JSON.

**How we identified it:** Ran a debug script that printed `repr()` of the raw response, which showed the backtick wrapping clearly.

**How we fixed it:**
```python
raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
```

**Lesson:** Always strip markdown fences from Claude API responses before JSON parsing, even when your prompt says "return only JSON."

### nano being unreliable for paste
**What happened:** Ctrl+Shift+V in nano was deleting content instead of pasting, or only pasting partial text. Made editing .env unreliable.

**How we fixed it:** Stopped using nano for anything important. Used `echo` for single line writes and `cat >` with heredoc for full files.

```bash
# Single line (like .env):
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Full file:
cat > filename.py << 'EOF'
...file contents...
EOF
```

**Lesson:** Nano works fine for simple edits on a server but fights you in WSL when pasting from a modern clipboard. Use echo and cat heredoc instead.

---

## Terminal Cheat Sheet

### Navigation
```bash
pwd                    # where am I right now
ls                     # list files in current directory
ls -la                 # list all files including hidden ones (like .env)
cd ~/pie-digest        # go to pie-digest folder
cd ~                   # go to home directory
cd ..                  # go up one level
```

### Python and venv
```bash
python3 --version                          # check Python version
python3 -m venv venv                       # create virtual environment
source venv/bin/activate                   # activate venv (prompt shows (venv))
deactivate                                 # exit venv
pip install feedparser anthropic python-dotenv   # install packages
pip list                                   # see installed packages
python3 script.py                          # run a Python script
```

### Files
```bash
cat filename                               # print file contents
echo "text" > file.txt                     # write single line to file (overwrites)
echo "text" >> file.txt                    # append line to file
cp source destination                      # copy file
mv source destination                      # move or rename file
rm filename                                # delete file
touch filename                             # create empty file
```

### Git
```bash
git status                                 # what has changed
git add filename                           # stage a file for commit
git add .                                  # stage all changed files
git commit -m "message"                    # commit with message
git push origin main                       # push to GitHub
git pull origin main                       # pull latest from GitHub
git log --oneline                          # see commit history
```

### SQLite (checking your database)
```bash
# Quick peek at articles
python3 -c "import sqlite3; conn = sqlite3.connect('memory.db'); c = conn.cursor(); c.execute('SELECT source, title, score FROM articles ORDER BY score DESC LIMIT 10'); [print(r) for r in c.fetchall()]"
```

### Useful one-liners
```bash
# Test API key is loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY')[:15])"

# Run full pipeline in one command
python3 collect.py && python3 score.py && python3 brief.py

# Check what's in your database
python3 -c "import sqlite3; conn = sqlite3.connect('memory.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM articles'); print(c.fetchone())"
```

---

## Key Concepts Explained Simply

**RSS Feed**
A standardized format websites use to publish their latest content. Instead of scraping a webpage, you request the RSS URL and get back a clean list of articles with titles, summaries, and links. feedparser handles this for us.

**Virtual Environment (venv)**
A sandboxed Python installation for a specific project. Keeps packages isolated so project A's dependencies don't conflict with project B's. Always activate it before running scripts (`source venv/bin/activate`). Always recreate it if you move the project folder.

**SQLite**
A database that lives in a single file (memory.db). No server, no setup, built into Python. Good for personal projects. The step up from this is Postgres (what your company calls "core").

**GitHub Actions**
Automated workflows that run on GitHub's servers on a schedule or trigger. Free on public repos. Our workflow runs at 6am EST Monday-Friday using cron syntax: `0 11 * * 1-5` (11 UTC = 6am EST).

**Cron syntax**
`0 11 * * 1-5` means: at minute 0, hour 11, any day of month, any month, Monday through Friday.

**API Key**
A secret password that identifies you to an external service (Claude, OpenAI, etc.). Treat like a password: never paste in chat, never push to GitHub, always store in .env file.

**System Prompt**
Instructions given to an AI model that set context and behavior before the conversation starts. In score.py and brief.py our system prompt tells Claude who you are, what your background is, and exactly how to format the response.

**JSON**
A standard data format for structured information. Looks like: `{"score": 3, "reason": "structural change"}`. We use it to get structured scores back from Claude reliably.

**GitHub Pages**
Free static website hosting built into GitHub. Serves HTML files directly from your repo as a real URL. Our digest lives at `https://faenorsword88-ops.github.io/pie-digest`.
