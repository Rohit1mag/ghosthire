# Job Aggregator - YC Jobs Focus

A web scraper and job aggregator that finds software engineering roles from Y Combinator companies in W24, S24, and W25 batches.

## Architecture Overview

```
Job Aggregator/
├── scrapers/           # Scraper modules for different sources
│   ├── __init__.py
│   └── yc_scraper.py  # Y Combinator Jobs scraper
├── models.py           # Data models (JobPosting)
├── scraper.py          # Main script to run scrapers
├── config.json         # Configuration file for source URLs
├── data/               # Output directory for scraped jobs
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

### Current Status: YC Jobs Scraper ✅

**Implemented:**
- ✅ YC Jobs scraper
- ✅ Batch filtering (W24, S24, W25)
- ✅ Job parsing (company, title, location, tech stack)
- ✅ JSON export with statistics

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure sources (optional):**
   - Edit `config.json` to configure YC Jobs source
   - Set `"active": true` for sources you want to scrape
   - Example:
   ```json
   {
     "sources": {
       "yc_jobs": [
         {
           "name": "YC Jobs Board",
           "url": "https://www.ycombinator.com/jobs",
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
```

## How It Works

### YC Scraper (`scrapers/yc_scraper.py`)

The `YCScraper` class:
1. Fetches the YC Jobs page
2. Extracts company URLs from job listings
3. Validates companies against criteria:
   - **Batch**: Must be W24, S24, or W25
4. Scrapes job details from company pages:
   - **Company name**: Extracted from URL and page content
   - **Job title**: Extracted from job posting page
   - **Location**: Pattern matching for cities, countries, remote
   - **Tech stack**: Keyword matching against common technologies

### Data Model (`models.py`)

The `JobPosting` dataclass stores:
- Company name
- Job title
- Location (optional)
- Tech stack (list of technologies)
- Raw job description text
- Source information
- Timestamp

### Output

Jobs are saved to `jobs.json` and `frontend/jobs.json` with:
- All job postings as JSON
- Statistics: top companies, tech stacks, locations
- Metadata: last updated timestamp, total job count

## Example Output

```json
{
  "company": "Example Corp",
  "title": "Senior Software Engineer",
  "location": "Remote",
  "tech_stack": ["python", "react", "postgresql", "aws"],
  "raw_text": "Example Corp is hiring...",
  "source": "YC",
  "source_url": "https://www.ycombinator.com/jobs",
  "scraped_at": "2024-11-15T10:30:00",
  "url": "https://www.ycombinator.com/companies/example/jobs/123"
}
```

## Filtering Criteria

The scraper only includes jobs from companies in the following batches:
- **Batch**: W24, S24, or W25

This ensures we focus on recent Y Combinator companies with active job postings.

## License

MIT

