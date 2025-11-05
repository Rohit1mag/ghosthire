import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import sys
import os
import time

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from models import JobPosting


class YCScraper:
    """Scraper for Y Combinator Jobs board"""
    
    BASE_URL = "https://www.ycombinator.com"
    JOBS_URL = "https://www.ycombinator.com/jobs"
    
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
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_tech_stack(self, text: str) -> List[str]:
        """Extract tech stack mentions from text"""
        text_lower = text.lower()
        found_tech = []
        
        for tech in self.TECH_KEYWORDS:
            pattern = r'\b' + re.escape(tech.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_tech.append(tech.lower())
        
        return list(set(found_tech))
    
    def extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location from job description text"""
        from utils.location_validator import validate_and_normalize_location, VALID_LOCATIONS
        
        text_lower = text.lower()
        
        # Try to find location in text
        for location in VALID_LOCATIONS:
            pattern = r'\b' + re.escape(location) + r'\b'
            if re.search(pattern, text_lower):
                candidate = validate_and_normalize_location(location)
                if candidate:
                    return candidate
        
        return None
    
    def fetch_job_details(self, job_url: str) -> Optional[dict]:
        """Fetch detailed information from a single job posting page"""
        soup = self.fetch_page(job_url)
        if not soup:
            return None
        
        try:
            details = {}
            
            # Try to find job title
            title_elem = soup.find(['h1', 'h2'], class_=re.compile(r'title|heading|job-title', re.I))
            if not title_elem:
                title_elem = soup.find('h1')
            details['title'] = title_elem.get_text(strip=True) if title_elem else None
            
            # Try to find company name
            company_elem = soup.find(['div', 'span', 'a'], class_=re.compile(r'company', re.I))
            if not company_elem:
                # Look for company in metadata
                company_elem = soup.find('meta', property='og:site_name')
                if company_elem:
                    details['company'] = company_elem.get('content', '').strip()
                else:
                    details['company'] = None
            else:
                details['company'] = company_elem.get_text(strip=True)
            
            # Get full job description
            description_elem = soup.find(['div', 'section'], class_=re.compile(r'description|content|body|details', re.I))
            if not description_elem:
                # Fallback to finding the largest text block
                description_elem = soup.find('main') or soup.find('article') or soup.find('body')
            
            description_text = description_elem.get_text(separator=' ', strip=True) if description_elem else ''
            details['description'] = description_text
            
            # Extract location from description
            details['location'] = self.extract_location_from_text(description_text)
            
            # Extract tech stack from description
            details['tech_stack'] = self.extract_tech_stack(description_text)
            
            return details
            
        except Exception as e:
            print(f"Error parsing job details from {job_url}: {e}")
            return None
    
    def scrape_jobs(self) -> List[JobPosting]:
        """Scrape all job postings from YC Jobs"""
        print(f"Fetching YC Jobs: {self.JOBS_URL}")
        soup = self.fetch_page(self.JOBS_URL)
        
        if not soup:
            print("Failed to fetch YC jobs page")
            return []
        
        jobs = []
        
        # Find all job links on the main page
        # YC jobs typically link to company/job pages or external application pages
        job_links = soup.find_all('a', href=re.compile(r'(companies/|jobs/|apply)', re.I))
        
        if not job_links:
            # Fallback: find any links that might be jobs
            job_links = soup.find_all('a', href=True)
        
        print(f"Found {len(job_links)} potential job links")
        
        # Track visited URLs to avoid duplicates
        visited_urls = set()
        processed_count = 0
        
        for link in job_links:
            if processed_count >= 30:  # Limit to avoid too many requests
                break
            
            try:
                job_url = link.get('href', '')
                if not job_url:
                    continue
                
                # Skip internal navigation and non-job links
                if any(skip in job_url.lower() for skip in ['#', 'javascript:', 'mailto:', '/companies?', 'login', 'signup']):
                    continue
                
                # Make full URL
                if not job_url.startswith('http'):
                    job_url = self.BASE_URL + job_url
                
                # Skip if already visited
                if job_url in visited_urls:
                    continue
                visited_urls.add(job_url)
                
                # Extract company and title from the link card/element
                parent = link.find_parent(['div', 'article', 'li', 'section'])
                link_text = link.get_text(strip=True)
                parent_text = parent.get_text(separator=' ', strip=True) if parent else ''
                
                # Basic extraction from listing
                company = None
                title = None
                
                # Try to find company and title in parent element
                if parent:
                    company_elem = parent.find(['h3', 'h4', 'strong', 'div'], class_=re.compile(r'company|name', re.I))
                    title_elem = parent.find(['h2', 'h3', 'span'], class_=re.compile(r'title|role|position', re.I))
                    
                    if company_elem:
                        company = company_elem.get_text(strip=True)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # If we don't have enough info, try fetching the actual job page (rate limit)
                if not company or not title:
                    # Only fetch details if the link looks promising
                    if 'job' in job_url.lower() or 'careers' in job_url.lower() or 'companies/' in job_url:
                        print(f"Fetching details from: {job_url}")
                        details = self.fetch_job_details(job_url)
                        if details:
                            company = details.get('company') or company or "Unknown"
                            title = details.get('title') or title or link_text
                            location = details.get('location')
                            tech_stack = details.get('tech_stack', [])
                            description = details.get('description', '')
                            
                            # Rate limiting
                            time.sleep(0.5)
                        else:
                            continue
                    else:
                        # Use what we have from the listing
                        company = company or link_text.split('|')[0].strip() if '|' in link_text else "Unknown"
                        title = title or link_text or "Software Engineer"
                        location = self.extract_location_from_text(parent_text)
                        tech_stack = self.extract_tech_stack(parent_text + " " + link_text)
                        description = parent_text
                else:
                    # Use listing info
                    location = self.extract_location_from_text(parent_text)
                    tech_stack = self.extract_tech_stack(parent_text + " " + link_text)
                    description = parent_text
                
                # Skip if we don't have minimum required info
                if company == "Unknown" and title == "Software Engineer":
                    continue
                
                # Create job posting
                job = JobPosting(
                    company=company[:100],
                    title=title[:100],
                    location=location,
                    tech_stack=tech_stack,
                    raw_text=description[:500] if description else link_text,
                    source='YC',
                    source_url=self.JOBS_URL,
                    scraped_at=datetime.now(),
                    url=job_url,
                    posted_date=datetime.now()  # YC doesn't show exact dates
                )
                
                jobs.append(job)
                processed_count += 1
                
                print(f"Processed {processed_count}/30: {company} - {title}")
                
            except Exception as e:
                print(f"Error processing link: {e}")
                continue
        
        print(f"Extracted {len(jobs)} jobs from YC")
        return jobs
