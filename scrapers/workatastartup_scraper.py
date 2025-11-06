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


class WorkatastartupScraper:
    """Scraper for Work at a Startup job board"""
    
    BASE_URL = "https://www.workatastartup.com"
    JOBS_URL = "https://www.workatastartup.com/jobs"
    
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
    
    
    def scrape_company_page(self, company_url: str) -> List[JobPosting]:
        """Scrape all jobs from a company page"""
        soup = self.fetch_page(company_url)
        if not soup:
            return []
        
        company_jobs = []
        
        # Extract company name from URL
        company_name = self.extract_company_from_url(company_url + "/jobs/dummy")
        if not company_name:
            match = re.search(r'/companies/([^/]+)', company_url)
            if match:
                company_slug = match.group(1)
                company_name = re.sub(r'-\d+$', '', company_slug).replace('-', ' ').title()
        
        # Find all job links on the company page
        job_links = soup.find_all('a', href=re.compile(r'/jobs/', re.I))
        
        for link in job_links[:20]:  # Limit to avoid too many requests
            job_path = link.get('href', '')
            if not job_path:
                continue
            
            # Make full URL
            if not job_path.startswith('http'):
                job_url = "https://www.ycombinator.com" + job_path
            else:
                job_url = job_path
            
            # Only process if it's a job posting URL
            if '/companies/' not in job_url or '/jobs/' not in job_url:
                continue
            
            # Fetch job details
            print(f"  Fetching job: {job_url}")
            details = self.fetch_job_details(job_url)
            
            if details:
                company = details.get('company') or company_name or "Unknown"
                title = details.get('title') or link.get_text(strip=True) or "Software Engineer"
                location = details.get('location')
                tech_stack = details.get('tech_stack', [])
                description = details.get('description', '')
                
                # Clean up title
                if title and title.endswith('Jobs'):
                    title = title[:-4].strip()
                
                job = JobPosting(
                    company=company[:100] if company else "Unknown",
                    title=title[:100] if title else "Software Engineer",
                    location=location,
                    tech_stack=tech_stack,
                    raw_text=description[:500] if description else '',
                    source='Workatastartup',
                    source_url=self.JOBS_URL,
                    scraped_at=datetime.now(),
                    url=job_url,
                    posted_date=datetime.now()
                )
                
                company_jobs.append(job)
                time.sleep(0.3)  # Rate limiting
        
        return company_jobs
    
    def extract_company_from_url(self, url: str) -> Optional[str]:
        """Extract company name from Workatastartup job URL format: /companies/company-name/jobs/..."""
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
        """Scrape all job postings from Work at a Startup"""
        print(f"Fetching Work at a Startup jobs")
        
        jobs = []
        
        # Define all job categories to scrape
        job_categories = [
            "software-engineer",
            "product-manager", 
            "designer",
            "recruiting",
            "science",
            "operations",
            "sales-manager",
            "marketing",
            "legal",
            "finance"
        ]
        
        # Scrape each category
        for category in job_categories:
            print(f"\nScraping category: {category}")
            category_jobs = self.scrape_category(category)
            jobs.extend(category_jobs)
            time.sleep(1)  # Rate limiting between categories
        
        print(f"\nExtracted {len(jobs)} total jobs from Work at a Startup")
        return jobs
    
    def scrape_category(self, category: str, max_pages: int = 5) -> List[JobPosting]:
        """Scrape jobs from a specific category with pagination"""
        category_jobs = []
        
        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"https://www.workatastartup.com/jobs/l/{category}"
            else:
                url = f"https://www.workatastartup.com/jobs/l/{category}?page={page}"
            
            print(f"  Fetching page {page}: {url}")
            soup = self.fetch_page(url)
            
            if not soup:
                print(f"    Failed to fetch page {page}")
                break
            
            # Find all job links on this page
            job_links = soup.find_all('a', href=re.compile(r'(companies/|jobs/|apply)', re.I))
            
            if not job_links:
                print(f"    No jobs found on page {page}, stopping pagination")
                break
            
            page_jobs = self.process_job_links(job_links, f"{category} page {page}")
            
            if not page_jobs:
                print(f"    No valid jobs processed on page {page}, stopping pagination")
                break
            
            category_jobs.extend(page_jobs)
            print(f"    Found {len(page_jobs)} jobs on page {page}")
            
            # Rate limiting between pages
            time.sleep(0.5)
        
        return category_jobs
    
    def process_job_links(self, job_links, source_description: str) -> List[JobPosting]:
        """Process a list of job links and extract job information"""
        jobs = []
        processed_count = 0
        
        for link in job_links:
            if processed_count >= 50:  # Limit per page to avoid too many requests
                break
            
            try:
                job_url = link.get('href', '')
                if not job_url:
                    continue
                
                # Skip internal navigation and non-job links
                skip_patterns = ['#', 'javascript:', 'mailto:', '/companies?', 'login', 'signup']
                if any(skip in job_url.lower() for skip in skip_patterns):
                    continue
                
                # Skip role category pages
                if '/jobs/role/' in job_url.lower():
                    continue
                
                # Skip location category pages
                if '/jobs/location/' in job_url.lower():
                    continue
                
                # Make full URL
                if not job_url.startswith('http'):
                    if job_url.startswith('/companies/'):
                        job_url = "https://www.ycombinator.com" + job_url
                    else:
                        job_url = self.BASE_URL + job_url
                
                # Only process company/job URLs
                if '/companies/' not in job_url:
                    continue
                
                # Check if it's a company page or job page
                is_job_page = '/companies/' in job_url and '/jobs/' in job_url
                
                if not is_job_page:
                    continue
                
                # Extract company name from URL
                company = self.extract_company_from_url(job_url)
                
                # Extract title and company from link
                parent = link.find_parent(['div', 'article', 'li', 'section'])
                link_text = link.get_text(strip=True)
                
                title = None
                if parent:
                    title_elem = parent.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'title|role|position|job', re.I))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # Fetch job details
                details = self.fetch_job_details(job_url)
                
                if details:
                    company = details.get('company') or company or "Unknown"
                    title = details.get('title') or title or link_text
                    location = details.get('location')
                    tech_stack = details.get('tech_stack', [])
                    description = details.get('description', '')
                    time.sleep(0.3)  # Rate limiting
                else:
                    # Use fallback data
                    if not company:
                        company = self.extract_company_from_url(job_url) or "Unknown"
                    if not title:
                        title = link_text or "Software Engineer"
                    location = self.extract_location_from_text(link_text)
                    tech_stack = self.extract_tech_stack(link_text)
                    description = link_text
                
                # Skip if we don't have minimum required info
                if company == "Unknown" and not title:
                    continue
                
                # Clean up title
                if title and title.endswith('Jobs'):
                    title = title[:-4].strip()
                
                # Create job posting
                job = JobPosting(
                    company=company[:100] if company else "Unknown",
                    title=title[:100] if title else "Software Engineer",
                    location=location,
                    tech_stack=tech_stack,
                    raw_text=description[:500] if description else link_text,
                    source='Workatastartup',
                    source_url=self.JOBS_URL,
                    scraped_at=datetime.now(),
                    url=job_url,
                    posted_date=datetime.now()
                )
                
                jobs.append(job)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing link: {e}")
                continue
        
        return jobs
