# Job Aggregator - Hidden SWE Roles Finder

A web scraper and job aggregator that finds "hidden" software engineering roles from non-mainstream sources like HN Who's Hiring threads, YC jobs, and VC portfolio pages.

## Architecture Overview

```
Job Aggregator/
├── scrapers/           # Scraper modules for different sources
│   ├── __init__.py
│   └── hn_scraper.py   # HackerNews Who's Hiring scraper
├── models.py           # Data models (JobPosting)
├── scraper.py          # Main script to run scrapers
├── config.json         # Configuration file for source URLs
├── data/               # Output directory for scraped jobs
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

### Current Status: MVP - HN Scraper ✅

**Implemented:**
- ✅ HN Who's Hiring thread scraper
- ✅ Job parsing (company, title, location, tech stack)
- ✅ JSON export with statistics

**Planned:**
- ⏳ YC Jobs scraper
- ⏳ VC portfolio scraper
- ⏳ Database storage (Postgres)
- ⏳ Hidden score calculation
- ⏳ Deduplication logic
- ⏳ Backend API (Flask/FastAPI)
- ⏳ Frontend (React)

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure sources (optional):**
   - Edit `config.json` to add HN thread URLs and other sources
   - Set `"active": true` for sources you want to scrape
   - Example:
   ```json
   {
     "sources": {
       "hn_whos_hiring": [
         {
           "name": "November 2025",
           "url": "https://news.ycombinator.com/item?id=45800465",
           "active": true
         }
       ]
     }
   }
   ```

3. **Run the scraper:**
```bash
# Scrape all active sources from config.json
python scraper.py

# Or scrape a specific URL
python scraper.py https://news.ycombinator.com/item?id=XXXXX
```

## How It Works

### HN Scraper (`scrapers/hn_scraper.py`)

The `HNScraper` class:
1. Fetches the HN thread HTML
2. Parses all comments
3. Extracts job information using pattern matching:
   - **Company name**: First line or before separators (|, -, :, •)
   - **Job title**: After separator or keywords like "engineer", "developer"
   - **Location**: Pattern matching for cities, countries, remote
   - **Tech stack**: Keyword matching against common technologies

### Data Model (`models.py`)

The `JobPosting` dataclass stores:
- Company name
- Job title
- Location (optional)
- Tech stack (list of technologies)
- Raw comment text
- Source information
- Timestamp

### Output

Jobs are saved to `data/hn_jobs_TIMESTAMP.json` with:
- All job postings as JSON
- Statistics: top companies, tech stacks, locations

## Example Output

```json
{
  "company": "Example Corp",
  "title": "Senior Software Engineer",
  "location": "Remote",
  "tech_stack": ["python", "react", "postgresql", "aws"],
  "raw_text": "Example Corp | Senior Software Engineer...",
  "source": "HN Who's Hiring",
  "source_url": "https://news.ycombinator.com/item?id=XXXXX",
  "scraped_at": "2024-11-15T10:30:00",
  "comment_id": "c_12345678"
}
```

## Next Steps

1. **Test with real HN thread** - Get actual November 2024 thread URL and verify extraction
2. **Improve parsing** - Tune regex patterns based on real data
3. **Add YC Jobs scraper** - Next source to integrate
4. **Database integration** - Move from JSON to Postgres
5. **Hidden score algorithm** - Calculate based on recency, platform obscurity, estimated applicants

## Technical Details

### Parsing Challenges

HN comments are unstructured, so we use heuristics:
- Company names usually appear first
- Common separators help split company/title
- Tech keywords are matched with word boundaries
- Location patterns cover common formats

### Future Improvements

- Machine learning for better entity extraction
- Deduplication across sources
- Hidden score calculation (recency + platform obscurity)
- Email alerts for new matching jobs
- User preference filtering

## License

MIT

