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
    
    def extract_company_from_url(self, url: str) -> Optional[str]:
        """Extract company name from YC job URL format: /companies/company-name/jobs/..."""
        match = re.search(r'/companies/([^/]+)/jobs/', url)
        if match:
            company_slug = match.group(1)
            # Convert slug to readable name (e.g., 'camber-2' -> 'Camber')
            # Remove trailing numbers and dashes, capitalize
            company_name = re.sub(r'-\d+$', '', company_slug)
            company_name = company_name.replace('-', ' ').title()
            return company_name
        return None
    
    def fetch_job_details(self, job_url: str) -> Optional[dict]:
        """Fetch detailed information from a single job posting page"""
        soup = self.fetch_page(job_url)
        if not soup:
            return None
        
        try:
            details = {}
            
            # First, try to extract company from URL
            company_from_url = self.extract_company_from_url(job_url)
            
            # Try to find job title - YC uses various structures
            title_elem = soup.find(['h1', 'h2'], class_=re.compile(r'title|heading|job-title', re.I))
            if not title_elem:
                title_elem = soup.find('h1')
            if not title_elem:
                # Look for title in breadcrumbs or navigation
                title_elem = soup.find('span', class_=re.compile(r'job-title|position', re.I))
            details['title'] = title_elem.get_text(strip=True) if title_elem else None
            
            # Try to find company name - check multiple locations
            company = None
            
            # 1. Look for company link or element
            company_elem = soup.find(['a', 'div', 'span'], class_=re.compile(r'company', re.I))
            if company_elem:
                company = company_elem.get_text(strip=True)
            
            # 2. Look in breadcrumbs or navigation
            if not company:
                breadcrumb = soup.find('nav') or soup.find('ol', class_=re.compile(r'breadcrumb', re.I))
                if breadcrumb:
                    company_links = breadcrumb.find_all('a', href=re.compile(r'/companies/'))
                    if company_links:
                        company = company_links[-1].get_text(strip=True)
            
            # 3. Look for company name in header or hero section
            if not company:
                header = soup.find('header') or soup.find(['div', 'section'], class_=re.compile(r'header|hero', re.I))
                if header:
                    company_elem = header.find(['a', 'h2', 'h3'], href=re.compile(r'/companies/'))
                    if company_elem:
                        company = company_elem.get_text(strip=True)
            
            # 4. Extract from URL if still not found
            if not company:
                company = company_from_url
            
            # 5. Fallback to meta tags
            if not company:
                company_elem = soup.find('meta', property='og:site_name')
                if company_elem:
                    company = company_elem.get('content', '').strip()
            
            details['company'] = company
            
            # Get full job description
            description_elem = soup.find(['div', 'section'], class_=re.compile(r'description|content|body|details|job-description', re.I))
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
            if processed_count >= 50:  # Limit to avoid too many requests
                break
            
            try:
                job_url = link.get('href', '')
                if not job_url:
                    continue
                
                # Skip internal navigation and non-job links
                skip_patterns = ['#', 'javascript:', 'mailto:', '/companies?', 'login', 'signup']
                if any(skip in job_url.lower() for skip in skip_patterns):
                    continue
                
                # CRITICAL: Skip role category pages (e.g., /jobs/role/software-engineer)
                # These are not individual job postings
                if '/jobs/role/' in job_url.lower():
                    continue
                
                # Skip location category pages
                if '/jobs/location/' in job_url.lower():
                    continue
                
                # Make full URL
                if not job_url.startswith('http'):
                    job_url = self.BASE_URL + job_url
                
                # Skip if already visited
                if job_url in visited_urls:
                    continue
                visited_urls.add(job_url)
                
                # Only process actual job posting URLs (company job pages)
                # Must contain /companies/.../jobs/ pattern
                if '/companies/' not in job_url or '/jobs/' not in job_url:
                    # Skip if it's not a company job page
                    continue
                
                # Extract company name from URL first
                company = self.extract_company_from_url(job_url)
                
                # Extract company and title from the link card/element
                parent = link.find_parent(['div', 'article', 'li', 'section'])
                link_text = link.get_text(strip=True)
                parent_text = parent.get_text(separator=' ', strip=True) if parent else ''
                
                # Extract title from listing
                title = None
                
                # Try to find title in parent element
                if parent:
                    title_elem = parent.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'title|role|position|job', re.I))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # Also try to find company name from listing
                    if not company:
                        company_elem = parent.find(['h3', 'h4', 'strong', 'div', 'a'], class_=re.compile(r'company|name', re.I))
                        if company_elem:
                            company = company_elem.get_text(strip=True)
                
                # Always fetch details from job page to get accurate info
                print(f"Fetching details from: {job_url}")
                details = self.fetch_job_details(job_url)
                
                if details:
                    # Use fetched details, with fallbacks
                    company = details.get('company') or company or "Unknown"
                    title = details.get('title') or title or link_text
                    location = details.get('location')
                    tech_stack = details.get('tech_stack', [])
                    description = details.get('description', '')
                    
                    # Rate limiting
                    time.sleep(0.5)
                else:
                    # If fetch failed, try to use what we have
                    if not company:
                        company = self.extract_company_from_url(job_url) or "Unknown"
                    if not title:
                        title = link_text or "Software Engineer"
                    location = self.extract_location_from_text(parent_text)
                    tech_stack = self.extract_tech_stack(parent_text + " " + link_text)
                    description = parent_text
                
                # Skip if we don't have minimum required info
                if company == "Unknown" and not title:
                    continue
                
                # Clean up title - remove "Jobs" suffix if present
                if title and title.endswith('Jobs'):
                    title = title[:-4].strip()
                
                # Clean up company - remove "Jobs by Role" if present
                if company and "Jobs by Role" in company:
                    company = "Unknown"
                
                # Create job posting
                job = JobPosting(
                    company=company[:100] if company else "Unknown",
                    title=title[:100] if title else "Software Engineer",
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
                
                print(f"Processed {processed_count}/50: {company} - {title}")
                
            except Exception as e:
                print(f"Error processing link: {e}")
                continue
        
        print(f"Extracted {len(jobs)} jobs from YC")
        return jobs
