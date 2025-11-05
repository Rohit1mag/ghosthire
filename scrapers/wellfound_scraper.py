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


class WellfoundScraper:
    """Scraper for Wellfound (formerly AngelList) jobs"""
    
    BASE_URL = "https://wellfound.com"
    JOBS_URL = "https://wellfound.com/jobs"
    
    # Common tech stack keywords to look for
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
        """Fetch and parse the Wellfound jobs page"""
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
        """Scrape job postings from Wellfound"""
        print(f"Fetching Wellfound Jobs: {self.JOBS_URL}")
        soup = self.fetch_jobs_page()
        
        jobs = []
        
        # Wellfound uses JavaScript rendering, so we may need to look for data attributes
        # Try to find job listings in various ways
        job_cards = soup.find_all(['div', 'article', 'section'], 
                                 class_=re.compile(r'job|listing|posting|card', re.I))
        
        if not job_cards:
            # Try finding links to job pages
            job_links = soup.find_all('a', href=re.compile(r'/job/|/jobs/|/role/'))
            
            for link in job_links[:50]:  # Limit to avoid too many
                try:
                    job_url = link.get('href', '')
                    if not job_url.startswith('http'):
                        job_url = self.BASE_URL + job_url
                    
                    # Extract text from link and nearby elements
                    link_text = link.get_text(strip=True)
                    if not link_text or len(link_text) < 5:
                        continue
                    
                    # Try to find company name from parent or sibling elements
                    parent = link.find_parent(['div', 'article', 'section'])
                    company = "Unknown"
                    
                    if parent:
                        # Look for company name in various places
                        company_elem = parent.find(['h3', 'h4', 'span', 'div'], 
                                                   class_=re.compile(r'company|name', re.I))
                        if company_elem:
                            company = company_elem.get_text(strip=True)
                        else:
                            # Sometimes company is in a separate element
                            company_elem = parent.find(string=re.compile(r'[A-Z][a-z]+', re.I))
                            if company_elem:
                                company = company_elem.strip()
                    
                    # Title is usually the link text
                    title = link_text[:100]
                    
                    # Extract tech stack and location from surrounding text
                    parent_text = ""
                    if parent:
                        parent_text = parent.get_text()
                    
                    tech_stack = self.extract_tech_stack(parent_text + " " + link_text)
                    
                    # Extract location
                    location = None
                    location_patterns = [
                        r'\b(remote|onsite|hybrid|anywhere)\b',
                        r'\b(san francisco|sf|bay area|new york|nyc|seattle|austin|boston|chicago|los angeles|la)\b',
                        r'\b(usa|united states|us|canada|uk|united kingdom|london|berlin|paris|amsterdam)\b',
                    ]
                    
                    for pattern in location_patterns:
                        match = re.search(pattern, parent_text.lower(), re.I)
                        if match:
                            location = match.group(1).title()
                            break
                    
                    # Extract posted date
                    posted_date = None
                    date_match = re.search(r'(\d+\s*(day|week|month)s?\s*ago)', parent_text.lower())
                    if date_match:
                        posted_date = self.parse_posted_date(date_match.group(1))
                    
                    job = JobPosting(
                        company=company[:100] if company else "Unknown",
                        title=title,
                        location=location,
                        tech_stack=tech_stack,
                        raw_text=parent_text[:500] if parent_text else link_text,
                        source='Wellfound',
                        source_url=job_url,
                        scraped_at=datetime.now(),
                        url=job_url,
                        posted_date=posted_date
                    )
                    
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Wellfound job link: {e}")
                    continue
        
        else:
            # Parse structured job cards
            for card in job_cards:
                try:
                    # Extract company
                    company_elem = card.find(['h2', 'h3', 'h4', 'strong', 'span'], 
                                            class_=re.compile(r'company|name', re.I))
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    
                    # Extract title
                    title_elem = card.find(['h2', 'h3', 'h4', 'a'], 
                                          class_=re.compile(r'title|position|role', re.I))
                    if not title_elem:
                        title_elem = card.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else "Software Engineer"
                    
                    # Extract URL
                    url_elem = card.find('a', href=True)
                    url = url_elem.get('href') if url_elem else None
                    if url and not url.startswith('http'):
                        url = self.BASE_URL + url
                    
                    # Extract location
                    location = None
                    location_elem = card.find(string=re.compile(r'remote|onsite|hybrid|location', re.I))
                    if location_elem:
                        location = location_elem.strip()
                    
                    # Extract tech stack
                    card_text = card.get_text()
                    tech_stack = self.extract_tech_stack(card_text)
                    
                    # Extract posted date
                    date_elem = card.find(string=re.compile(r'day|week|month|ago', re.I))
                    posted_date = None
                    if date_elem:
                        posted_date = self.parse_posted_date(date_elem)
                    
                    job = JobPosting(
                        company=company[:100],
                        title=title[:100],
                        location=location,
                        tech_stack=tech_stack,
                        raw_text=card_text[:500],
                        source='Wellfound',
                        source_url=url or self.JOBS_URL,
                        scraped_at=datetime.now(),
                        url=url,
                        posted_date=posted_date
                    )
                    
                    jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Wellfound job card: {e}")
                    continue
        
        print(f"Extracted {len(jobs)} jobs from Wellfound")
        return jobs

