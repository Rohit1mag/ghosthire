#!/usr/bin/env python3
"""
Main script to scrape all job sources and consolidate into unified jobs.json
"""

import sys
import json
import os
from datetime import datetime
from typing import List

# Import all scrapers
from scrapers.hn_scraper import HNScraper
from scrapers.yc_scraper import YCScraper
from scrapers.wellfound_scraper import WellfoundScraper
from scrapers.remoteok_scraper import RemoteOKScraper
from scrapers.weworkremotely_scraper import WeWorkRemotelyScraper

from models import JobPosting
from utils.hidden_score import calculate_hidden_score
from utils.deduplication import deduplicate_jobs


def save_jobs_to_json(jobs: List[JobPosting], filename: str):
    """Save jobs to JSON file"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # Convert to dict and sort by hidden_score descending
    data = [job.to_dict() for job in jobs]
    data.sort(key=lambda x: x.get('hidden_score', 0), reverse=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(jobs)} jobs to {filename}")


def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {"sources": {}}


def scrape_all_active_sources() -> List[JobPosting]:
    """Scrape all active sources from config.json"""
    config = load_config()
    all_jobs = []
    
    # Scrape HN Who's Hiring threads
    hn_sources = config.get("sources", {}).get("hn_whos_hiring", [])
    if hn_sources:
        scraper = HNScraper()
        for source in hn_sources:
            if source.get("active", False):
                print(f"\n{'='*60}")
                print(f"Scraping HN: {source.get('name', 'Unknown')}")
                print(f"URL: {source['url']}")
                print(f"{'='*60}")
                try:
                    jobs = scraper.scrape_thread(source['url'])
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error scraping HN {source['url']}: {e}")
                    continue
    
    # Scrape YC Jobs
    yc_sources = config.get("sources", {}).get("yc_jobs", [])
    if yc_sources:
        scraper = YCScraper()
        for source in yc_sources:
            if source.get("active", False):
                print(f"\n{'='*60}")
                print(f"Scraping YC Jobs")
                print(f"{'='*60}")
                try:
                    jobs = scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error scraping YC Jobs: {e}")
                    continue
    else:
        # Try scraping YC anyway if no config
        print(f"\n{'='*60}")
        print(f"Scraping YC Jobs")
        print(f"{'='*60}")
        try:
            scraper = YCScraper()
            jobs = scraper.scrape_jobs()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error scraping YC Jobs: {e}")
    
    # Scrape Wellfound
    wellfound_sources = config.get("sources", {}).get("wellfound", [])
    if wellfound_sources:
        scraper = WellfoundScraper()
        for source in wellfound_sources:
            if source.get("active", False):
                print(f"\n{'='*60}")
                print(f"Scraping Wellfound")
                print(f"{'='*60}")
                try:
                    jobs = scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error scraping Wellfound: {e}")
                    continue
    else:
        # Try scraping Wellfound anyway
        print(f"\n{'='*60}")
        print(f"Scraping Wellfound")
        print(f"{'='*60}")
        try:
            scraper = WellfoundScraper()
            jobs = scraper.scrape_jobs()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error scraping Wellfound: {e}")
    
    # Scrape RemoteOK
    remoteok_sources = config.get("sources", {}).get("remoteok", [])
    if remoteok_sources:
        scraper = RemoteOKScraper()
        for source in remoteok_sources:
            if source.get("active", False):
                print(f"\n{'='*60}")
                print(f"Scraping RemoteOK")
                print(f"{'='*60}")
                try:
                    jobs = scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error scraping RemoteOK: {e}")
                    continue
    else:
        # Try scraping RemoteOK anyway
        print(f"\n{'='*60}")
        print(f"Scraping RemoteOK")
        print(f"{'='*60}")
        try:
            scraper = RemoteOKScraper()
            jobs = scraper.scrape_jobs()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error scraping RemoteOK: {e}")
    
    # Scrape We Work Remotely
    wwr_sources = config.get("sources", {}).get("weworkremotely", [])
    if wwr_sources:
        scraper = WeWorkRemotelyScraper()
        for source in wwr_sources:
            if source.get("active", False):
                print(f"\n{'='*60}")
                print(f"Scraping We Work Remotely")
                print(f"{'='*60}")
                try:
                    jobs = scraper.scrape_jobs()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error scraping We Work Remotely: {e}")
                    continue
    else:
        # Try scraping We Work Remotely anyway
        print(f"\n{'='*60}")
        print(f"Scraping We Work Remotely")
        print(f"{'='*60}")
        try:
            scraper = WeWorkRemotelyScraper()
            jobs = scraper.scrape_jobs()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error scraping We Work Remotely: {e}")
    
    return all_jobs


def main():
    """Main entry point"""
    print("="*60)
    print("JOB AGGREGATOR - Scraping All Sources")
    print("="*60)
    
    # Scrape all sources
    try:
        all_jobs = scrape_all_active_sources()
    except Exception as e:
        print(f"Error scraping sources: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if not all_jobs:
        print("\nNo jobs found. Check your config.json or scraper implementations.")
        return
    
    print(f"\n{'='*60}")
    print(f"POST-PROCESSING")
    print(f"{'='*60}")
    print(f"Total jobs scraped: {len(all_jobs)}")
    
    # Calculate hidden scores
    print("\nCalculating hidden scores...")
    for job in all_jobs:
        if job.hidden_score is None:
            job.hidden_score = calculate_hidden_score(
                job.source,
                job.posted_date,
                job.scraped_at
            )
    
    # Deduplicate
    print("Deduplicating jobs...")
    unique_jobs = deduplicate_jobs(all_jobs)
    print(f"Removed {len(all_jobs) - len(unique_jobs)} duplicates")
    print(f"Final job count: {len(unique_jobs)}")
    
    # Sort by hidden_score descending
    unique_jobs.sort(key=lambda x: x.hidden_score or 0, reverse=True)
    
    # Save to unified jobs.json
    output_file = "jobs.json"
    save_jobs_to_json(unique_jobs, output_file)
    
    # Also save to frontend directory if it exists
    frontend_file = "frontend/jobs.json"
    if os.path.exists("frontend"):
        save_jobs_to_json(unique_jobs, frontend_file)
    
    # Print statistics
    print(f"\n{'='*60}")
    print("STATISTICS")
    print(f"{'='*60}")
    
    from collections import Counter
    
    # Source breakdown
    sources = Counter(job.source for job in unique_jobs)
    print(f"\nJobs by source:")
    for source, count in sources.most_common():
        print(f"  {source}: {count}")
    
    # Score distribution
    scores = [job.hidden_score or 0 for job in unique_jobs]
    if scores:
        print(f"\nHidden score distribution:")
        print(f"  Average: {sum(scores) / len(scores):.1f}")
        print(f"  Min: {min(scores)}")
        print(f"  Max: {max(scores)}")
        print(f"  Top 10 jobs have scores: {sorted(scores, reverse=True)[:10]}")
    
    # Top companies
    company_counts = Counter(job.company for job in unique_jobs)
    print(f"\nTop 10 companies:")
    for company, count in company_counts.most_common(10):
        print(f"  {company}: {count}")
    
    # Top tech stack
    all_tech = []
    for job in unique_jobs:
        all_tech.extend(job.tech_stack)
    tech_counts = Counter(all_tech)
    print(f"\nTop 10 tech stack mentions:")
    for tech, count in tech_counts.most_common(10):
        print(f"  {tech}: {count}")
    
    # Location breakdown
    locations = Counter(job.location for job in unique_jobs if job.location)
    print(f"\nTop 10 locations:")
    for location, count in locations.most_common(10):
        print(f"  {location}: {count}")


if __name__ == "__main__":
    main()

