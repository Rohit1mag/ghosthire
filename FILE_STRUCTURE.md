# Job Aggregator - File Structure

## Project Overview
A no-backend job aggregator that scrapes "hidden" software engineering roles from multiple sources and displays them in a static web frontend.

## Directory Structure

```
Job Aggregator/
│
├── 📁 scrapers/                    # Web scraper modules
│   ├── __init__.py                 # Package initialization
│   ├── hn_scraper.py               # HackerNews Who's Hiring scraper
│   ├── yc_scraper.py               # Y Combinator Jobs scraper
│   ├── wellfound_scraper.py        # Wellfound (AngelList) scraper
│   ├── remoteok_scraper.py         # RemoteOK scraper
│   └── weworkremotely_scraper.py   # We Work Remotely scraper
│
├── 📁 utils/                        # Utility functions
│   ├── __init__.py                 # Package initialization
│   ├── hidden_score.py             # Calculates "hidden score" (0-100)
│   └── deduplication.py            # Removes duplicate job postings
│
├── 📁 frontend/                     # Static web frontend
│   ├── index.html                  # Main HTML page
│   ├── style.css                   # Stylesheet
│   ├── app.js                      # JavaScript for filtering/searching
│   ├── jobs.json                   # Generated job data (updated by scraper)
│   └── .nojekyll                   # Tells GitHub Pages to skip Jekyll
│
├── 📁 data/                        # Historical scraped data (optional)
│   └── hn_jobs_*.json              # Timestamped backup files
│
├── 📁 .github/
│   └── workflows/
│       └── scrape.yml             # GitHub Actions workflow (daily auto-scrape)
│
├── 📄 scraper.py                   # Main entry point - orchestrates all scrapers
├── 📄 models.py                    # JobPosting data model definition
├── 📄 config.json                  # Configuration for scraper sources
├── 📄 jobs.json                    # Unified output file (all jobs combined)
├── 📄 requirements.txt             # Python dependencies
├── 📄 README.md                    # Project documentation
├── 📄 .gitignore                   # Git ignore rules
├── 📄 vercel.json                  # Vercel deployment config
└── 📄 _config.yml                  # GitHub Pages config (optional)
```

## File Descriptions

### Core Python Files

**`scraper.py`** - Main orchestrator
- Imports all scrapers
- Runs scraping from config.json
- Applies deduplication
- Calculates hidden scores
- Saves unified `jobs.json` output

**`models.py`** - Data model
- Defines `JobPosting` dataclass
- Fields: company, title, location, tech_stack, url, source, posted_date, hidden_score
- Methods: `generate_id()`, `to_dict()`, `from_dict()`

**`config.json`** - Source configuration
- Lists all job sources (HN threads, YC, Wellfound, etc.)
- `active: true/false` toggles scraping for each source
- Add new sources here

### Scraper Modules (`scrapers/`)

Each scraper follows the same pattern:
- `scrape_jobs()` or `scrape_thread()` method
- Extracts: company, title, location, tech_stack, url, posted_date
- Returns list of `JobPosting` objects

**`hn_scraper.py`** - HN Who's Hiring
- Parses HN comment threads
- Extracts job info from unstructured comments
- Handles comment replies and filtering

**`yc_scraper.py`** - Y Combinator Jobs
- Scrapes YC jobs board
- Parses structured job listings

**`wellfound_scraper.py`** - Wellfound/AngelList
- Scrapes Wellfound job board
- May need JavaScript rendering for full functionality

**`remoteok_scraper.py`** - RemoteOK
- Scrapes RemoteOK job board
- Focuses on remote positions

**`weworkremotely_scraper.py`** - We Work Remotely
- Scrapes We Work Remotely programming jobs
- Remote-focused positions

### Utility Modules (`utils/`)

**`hidden_score.py`** - Scoring algorithm
- Source weights: HN (90), YC (80), Wellfound (70), others (20)
- Recency bonus: 24hrs (+10), 1 week (+5), 2 weeks (0)
- Returns score 0-100

**`deduplication.py`** - Duplicate removal
- Uses fuzzy matching (rapidfuzz library)
- Compares company + title similarity
- Prevents duplicate job postings

### Frontend (`frontend/`)

**`index.html`** - Main page structure
- Search input
- Location dropdown
- Tech stack filter tags
- Job cards container

**`app.js`** - Frontend logic
- Fetches `jobs.json` on load
- Client-side filtering (search, location, tech stack)
- Renders job cards
- Sorts by hidden_score

**`style.css`** - Styling
- Modern, responsive design
- Card-based layout
- Gradient headers
- Mobile-friendly

**`jobs.json`** - Generated data file
- Created by `scraper.py`
- Unified format with all jobs
- Sorted by hidden_score (descending)
- Updated daily via GitHub Actions

### Configuration Files

**`requirements.txt`** - Python dependencies
- beautifulsoup4 (HTML parsing)
- requests (HTTP requests)
- lxml (XML/HTML parser)
- python-dateutil (date parsing)
- rapidfuzz (fuzzy string matching)

**`config.json`** - Scraper configuration
- Defines which sources to scrape
- Lists HN thread URLs
- Can enable/disable sources

**`.github/workflows/scrape.yml`** - Automation
- Runs daily at 2 AM UTC
- Installs dependencies
- Runs scraper
- Commits updated jobs.json
- Can be triggered manually

**`vercel.json`** - Vercel deployment
- Configures static file serving
- Routes requests to frontend/

**`_config.yml`** - GitHub Pages config
- Optional Jekyll configuration

### Output Files

**`jobs.json`** (root) - Main output
- All scraped jobs in unified format
- Used by frontend

**`frontend/jobs.json`** - Copy for frontend
- Same as root jobs.json
- Makes it accessible to frontend

**`data/hn_jobs_*.json`** - Historical backups
- Timestamped files from previous runs
- Useful for debugging/testing

## Data Flow

```
1. scraper.py reads config.json
2. Runs each active scraper (HN, YC, etc.)
3. Each scraper returns JobPosting objects
4. scraper.py:
   - Calculates hidden_score for each job
   - Deduplicates using fuzzy matching
   - Sorts by hidden_score
5. Saves to jobs.json (root + frontend/)
6. Frontend loads jobs.json
7. User filters/searches client-side
8. GitHub Actions runs daily to update jobs.json
```

## Key Design Decisions

1. **No Backend**: Everything is static files - jobs.json + frontend
2. **Unified Output**: Single jobs.json file with consistent schema
3. **Client-Side Filtering**: No server needed, all filtering in browser
4. **Daily Updates**: GitHub Actions runs scrapers automatically
5. **Modular Scrapers**: Each source has its own scraper module
6. **Deduplication**: Prevents same job appearing multiple times
7. **Hidden Score**: Ranks jobs by "hidden-ness" (source + recency)

## How to Add a New Scraper

1. Create `scrapers/new_scraper.py`
2. Implement `scrape_jobs()` method returning `JobPosting` objects
3. Add to `scrapers/__init__.py` exports
4. Update `scraper.py` to call new scraper
5. Add source config to `config.json`
6. Add source weight to `utils/hidden_score.py`

## Deployment Files

- **GitHub Pages**: Uses `frontend/` directory, `.nojekyll` file
- **Vercel**: Uses `vercel.json` config
- **GitHub Actions**: Automatically updates jobs.json daily

