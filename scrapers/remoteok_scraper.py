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


class RemoteOKScraper:
    """Scraper for RemoteOK jobs"""
    
    BASE_URL = "https://remoteok.com"
    JOBS_URL = "https://remoteok.com"
    
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
        """Fetch and parse the RemoteOK jobs page"""
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
        """Scrape job postings from RemoteOK"""
        print(f"Fetching RemoteOK Jobs: {self.JOBS_URL}")
        soup = self.fetch_jobs_page()
        
        jobs = []
        
        # RemoteOK typically has job listings in table rows or divs
        job_rows = soup.find_all('tr', class_=re.compile(r'job', re.I))
        
        if not job_rows:
            # Try alternative: look for job cards or listings
            job_cards = soup.find_all(['div', 'article'], class_=re.compile(r'job|listing', re.I))
            
            for card in job_cards[:50]:  # Limit
                try:
                    # Extract company
                    company_elem = card.find(['h2', 'h3', 'strong'])
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    
                    # Extract title
                    title_elem = card.find(['h2', 'h3', 'a'])
                    title = title_elem.get_text(strip=True) if title_elem else "Software Engineer"
                    
                    # Extract URL
                    url_elem = card.find('a', href=True)
                    url = url_elem.get('href') if url_elem else None
                    if url and not url.startswith('http'):
                        url = self.BASE_URL + url
                    
                    # RemoteOK is all remote
                    location = "Remote"
                    
                    # Extract tech stack
                    card_text = card.get_text()
                    tech_stack = self.extract_tech_stack(card_text)
                    
                    job = JobPosting(
                        company=company[:100],
                        title=title[:100],
                        location=location,
                        tech_stack=tech_stack,
                        raw_text=card_text[:500],
                        source='RemoteOK',
                        source_url=url or self.JOBS_URL,
                        scraped_at=datetime.now(),
                        url=url,
                        posted_date=None
                    )
                    
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing RemoteOK job: {e}")
                    continue
        
        else:
            # Parse table rows
            for row in job_rows[:50]:  # Limit
                try:
                    # Extract company and title from row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    # Company is usually in first or second cell
                    company = cells[0].get_text(strip=True) if cells else "Unknown"
                    title = cells[1].get_text(strip=True) if len(cells) > 1 else "Software Engineer"
                    
                    # Extract URL
                    url_elem = row.find('a', href=True)
                    url = url_elem.get('href') if url_elem else None
                    if url and not url.startswith('http'):
                        url = self.BASE_URL + url
                    
                    # Extract tech stack from row
                    row_text = row.get_text()
                    tech_stack = self.extract_tech_stack(row_text)
                    
                    job = JobPosting(
                        company=company[:100],
                        title=title[:100],
                        location="Remote",
                        tech_stack=tech_stack,
                        raw_text=row_text[:500],
                        source='RemoteOK',
                        source_url=url or self.JOBS_URL,
                        scraped_at=datetime.now(),
                        url=url,
                        posted_date=None
                    )
                    
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing RemoteOK job row: {e}")
                    continue
        
        print(f"Extracted {len(jobs)} jobs from RemoteOK")
        return jobs

