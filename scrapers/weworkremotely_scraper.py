import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from models import JobPosting


class WeWorkRemotelyScraper:
    """Scraper for We Work Remotely jobs"""
    
    BASE_URL = "https://weworkremotely.com"
    JOBS_URL = "https://weworkremotely.com/categories/remote-programming-jobs"
    
    TECH_KEYWORDS = [
        'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
        'node', 'go', 'golang', 'rust', 'java', 'c++', 'cpp', 'c#',
        'php', 'ruby', 'rails', 'django', 'flask', 'fastapi',
        'postgresql', 'postgres', 'mysql', 'mongodb', 'redis',
        'aws', 'gcp', 'azure', 'kubernetes', 'docker', 'terraform',
        'graphql', 'rest', 'gRPC', 'microservices', 'serverless',
        'react', 'vue', 'angular', 'svelte', 'nextjs', 'remix',
        'tailwind', 'bootstrap', 'css', 'html', 'webpack', 'vite'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_jobs_page(self, url: str = None) -> BeautifulSoup:
        """Fetch and parse the We Work Remotely jobs page"""
        url = url or self.JOBS_URL
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    
    def extract_tech_stack(self, text: str) -> List[str]:
        """Extract tech stack mentions from text"""
        text_lower = text.lower()
        found_tech = []
        
        for tech in self.TECH_KEYWORDS:
            pattern = r'\b' + re.escape(tech.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_tech.append(tech.lower())
        
        return list(set(found_tech))
    
    def parse_posted_date(self, date_str: str) -> Optional[datetime]:
        """Parse posted date from various formats"""
        if not date_str:
            return None
        
        date_str_lower = date_str.lower().strip()
        
        if 'day' in date_str_lower or 'hour' in date_str_lower:
            return datetime.now()
        elif 'week' in date_str_lower:
            return datetime.now()
        elif 'month' in date_str_lower:
            return datetime.now()
        
        try:
            return datetime.fromisoformat(date_str)
        except:
            pass
        
        return None
    
    def scrape_jobs(self) -> List[JobPosting]:
        """Scrape job postings from We Work Remotely"""
        print(f"Fetching We Work Remotely Jobs: {self.JOBS_URL}")
        soup = self.fetch_jobs_page()
        
        jobs = []
        
        # We Work Remotely typically uses job listings in sections or divs
        job_listings = soup.find_all('li', class_=re.compile(r'feature|job', re.I))
        
        if not job_listings:
            # Try alternative: look for article tags or divs
            job_listings = soup.find_all(['article', 'div'], class_=re.compile(r'job|listing', re.I))
        
        for listing in job_listings[:50]:  # Limit
            try:
                # Extract company
                company_elem = listing.find(['span', 'div'], class_=re.compile(r'company', re.I))
                if not company_elem:
                    company_elem = listing.find('h3')
                company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                
                # Extract title
                title_elem = listing.find(['h2', 'h3', 'a'], class_=re.compile(r'title', re.I))
                if not title_elem:
                    title_elem = listing.find('a')
                title = title_elem.get_text(strip=True) if title_elem else "Software Engineer"
                
                # Extract URL
                url_elem = listing.find('a', href=True)
                url = url_elem.get('href') if url_elem else None
                if url and not url.startswith('http'):
                    url = self.BASE_URL + url
                
                # Extract tech stack
                listing_text = listing.get_text()
                tech_stack = self.extract_tech_stack(listing_text)
                
                # Extract posted date
                posted_date = None
                date_elem = listing.find('time')
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text()
                    posted_date = self.parse_posted_date(date_str)
                
                job = JobPosting(
                    company=company[:100],
                    title=title[:100],
                    location="Remote",
                    tech_stack=tech_stack,
                    raw_text=listing_text[:500],
                    source='WeWorkRemotely',
                    source_url=url or self.JOBS_URL,
                    scraped_at=datetime.now(),
                    url=url,
                    posted_date=posted_date
                )
                
                jobs.append(job)
            except Exception as e:
                print(f"Error parsing We Work Remotely job: {e}")
                continue
        
        print(f"Extracted {len(jobs)} jobs from We Work Remotely")
        return jobs

