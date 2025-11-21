import requests
import re
import json
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from models import JobPosting

class A16ZScraper:
    """Scraper for Andreessen Horowitz (a16z) job board"""
    
    BASE_URL = "https://jobs.a16z.com"
    JOBS_URL = "https://jobs.a16z.com/jobs?department=engineering"
    API_URL = "https://jobs.a16z.com/api/jobs"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': self.BASE_URL,
            'Origin': self.BASE_URL
        })
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a webpage and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_jobs_from_js(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract job data from JavaScript embedded in the page"""
        jobs = []
        
        # Find the script tag containing serverInitialData
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'serverInitialData' in script.string:
                # Extract the JSON data from the JavaScript
                js_content = script.string
                
                # Find the serverInitialData object
                match = re.search(r'window\.serverInitialData\s*=\s*({.*?});', js_content, re.DOTALL)
                if match:
                    try:
                        data_str = match.group(1)
                        # Clean up the JSON string
                        data_str = data_str.replace('\\u002F', '/')
                        data_str = data_str.replace('\\', '')
                        data_str = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), data_str)
                        
                        data = json.loads(data_str)
                        
                        # Try to find jobs in the data structure
                        if 'jobs' in data:
                            jobs = data['jobs']
                        elif 'results' in data:
                            jobs = data['results']
                        elif 'listings' in data:
                            jobs = data['listings']
                        
                        print(f"Found {len(jobs)} jobs in JavaScript data")
                        
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JavaScript data: {e}")
                        continue
                    except Exception as e:
                        print(f"Error extracting jobs: {e}")
                        continue
        
        return jobs
    
    def fetch_api_jobs(self) -> List[Dict]:
        """Try to fetch jobs from the API endpoint"""
        try:
            # Try different API endpoints
            api_endpoints = [
                "https://jobs.a16z.com/api/jobs?department=engineering",
                "https://jobs.a16z.com/api/v1/jobs?department=engineering",
                "https://jobs.a16z.com/api/jobs",
                "https://jobs.a16z.com/api/v1/jobs"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'jobs' in data:
                            return data['jobs']
                        elif 'results' in data:
                            return data['results']
                        elif isinstance(data, list):
                            return data
                except Exception as e:
                    print(f"API endpoint {endpoint} failed: {e}")
                    continue
            
        except Exception as e:
            print(f"Error fetching from API: {e}")
        
        return []
    
    def parse_job_from_data(self, job_data: Dict) -> Optional[JobPosting]:
        """Parse job data from API/JS response into JobPosting"""
        try:
            # Extract basic job information - handle different data structures
            title = (
                job_data.get('title') or 
                job_data.get('name') or 
                job_data.get('position') or 
                "Engineering Role"
            )
            
            company = (
                job_data.get('company', {}).get('name') if 'company' in job_data else
                job_data.get('companyName') or
                job_data.get('company_name') or
                job_data.get('organization') or
                "a16z Portfolio Company"
            )
            
            location = (
                job_data.get('location', {}).get('name') if 'location' in job_data else
                job_data.get('city') or
                job_data.get('locationName') or
                job_data.get('location') or
                "Remote/On-site"
            )
            
            # Extract job URL
            job_url = (
                job_data.get('url') or
                job_data.get('applyUrl') or
                job_data.get('application_url') or
                f"{self.BASE_URL}/jobs/{job_data.get('id', '')}"
            )
            
            # Make URL absolute
            if job_url and not job_url.startswith('http'):
                job_url = self.BASE_URL + job_url
            
            # Extract description
            description = (
                job_data.get('description') or
                job_data.get('summary') or
                job_data.get('content') or
                f"Engineering position at {company}"
            )
            
            # Extract tech stack from description and title
            tech_stack = self.extract_tech_stack(title + " " + description)
            
            # Clean up title
            if title and title.endswith('Jobs'):
                title = title[:-4].strip()
            
            # Filter for engineering roles only
            if not self.is_engineering_role(title):
                return None
            
            return JobPosting(
                company=company[:100] if company else "Unknown",
                title=title[:100] if title else "Engineering Role",
                location=location,
                tech_stack=tech_stack,
                raw_text=description[:500] if description else title,
                source='A16Z',
                source_url=self.JOBS_URL,
                scraped_at=datetime.now(),
                url=job_url,
                posted_date=datetime.now()
            )
            
        except Exception as e:
            print(f"Error parsing job data: {e}")
            return None
    
    def is_engineering_role(self, title: str) -> bool:
        """Check if the job title is an engineering role"""
        if not title:
            return False
        
        title_lower = title.lower()
        
        # Engineering keywords
        engineering_keywords = [
            'engineer', 'developer', 'software', 'backend', 'frontend', 'full-stack',
            'full stack', 'devops', 'sre', 'site reliability', 'infrastructure',
            'platform', 'systems', 'security', 'data', 'machine learning', 'ml',
            'ai', 'artificial intelligence', 'mobile', 'ios', 'android', 'web',
            'qa', 'quality assurance', 'test', 'automation', 'cloud', 'network',
            'database', 'api', 'architecture', 'technical', 'coding', 'programming'
        ]
        
        # Exclude non-engineering roles
        exclude_keywords = [
            'sales engineer', 'solutions engineer', 'customer success', 'support',
            'product manager', 'designer', 'marketing', 'recruiter', 'hr',
            'finance', 'accounting', 'legal', 'operations', 'business analyst'
        ]
        
        # Check if title contains engineering keywords
        has_engineering = any(keyword in title_lower for keyword in engineering_keywords)
        
        # Check if title should be excluded
        should_exclude = any(keyword in title_lower for keyword in exclude_keywords)
        
        return has_engineering and not should_exclude
    
    def extract_tech_stack(self, text: str) -> List[str]:
        """Extract tech stack from job text"""
        if not text:
            return []
        
        tech_keywords = [
            'python', 'javascript', 'typescript', 'java', 'go', 'golang', 'rust',
            'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'perl',
            'react', 'vue', 'angular', 'svelte', 'node', 'nodejs', 'express',
            'django', 'flask', 'spring', 'rails', 'laravel', 'nextjs', 'nuxt',
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'vercel', 'netlify',
            'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'github',
            'gitlab', 'ci/cd', 'cicd', 'microservices', 'serverless', 'graphql',
            'rest', 'api', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql',
            'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'tensorflow', 'pytorch',
            'spark', 'hadoop', 'linux', 'ubuntu', 'windows', 'macos', 'unix'
        ]
        
        text_lower = text.lower()
        found_tech = []
        
        for tech in tech_keywords:
            if tech in text_lower:
                found_tech.append(tech)
        
        return list(set(found_tech))  # Remove duplicates
    
    def scrape_jobs(self) -> List[JobPosting]:
        """Scrape engineering jobs from a16z job board"""
        print(f"Fetching A16Z engineering jobs")
        
        jobs = []
        
        # First try API approach
        print("Trying API approach...")
        api_jobs = self.fetch_api_jobs()
        if api_jobs:
            print(f"Found {len(api_jobs)} jobs from API")
            for job_data in api_jobs:
                job = self.parse_job_from_data(job_data)
                if job:
                    jobs.append(job)
                    time.sleep(0.1)  # Rate limiting
        
        # If API fails, try JavaScript parsing
        if not jobs:
            print("API failed, trying JavaScript parsing...")
            soup = self.fetch_page(self.JOBS_URL)
            if soup:
                js_jobs = self.extract_jobs_from_js(soup)
                if js_jobs:
                    print(f"Found {len(js_jobs)} jobs from JavaScript")
                    for job_data in js_jobs:
                        job = self.parse_job_from_data(job_data)
                        if job:
                            jobs.append(job)
                            time.sleep(0.1)  # Rate limiting
        
        # If both fail, try basic HTML parsing
        if not jobs:
            print("JavaScript parsing failed, trying HTML parsing...")
            soup = self.fetch_page(self.JOBS_URL)
            if soup:
                # Look for job listings in HTML
                job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|position|listing', re.I))
                
                for element in job_elements:
                    try:
                        # Extract basic info from HTML
                        title_elem = element.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|position|role', re.I))
                        company_elem = element.find(['span', 'div', 'a'], class_=re.compile(r'company|organization', re.I))
                        location_elem = element.find(['span', 'div'], class_=re.compile(r'location|city|place', re.I))
                        link_elem = element.find('a', href=True)
                        
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        company = company_elem.get_text(strip=True) if company_elem else "a16z Portfolio Company"
                        location = location_elem.get_text(strip=True) if location_elem else "Remote/On-site"
                        job_url = link_elem.get('href') if link_elem else ""
                        
                        if job_url and not job_url.startswith('http'):
                            job_url = self.BASE_URL + job_url
                        
                        if title and self.is_engineering_role(title):
                            tech_stack = self.extract_tech_stack(title)
                            
                            job = JobPosting(
                                company=company[:100],
                                title=title[:100],
                                location=location,
                                tech_stack=tech_stack,
                                raw_text=title,
                                source='A16Z',
                                source_url=self.JOBS_URL,
                                scraped_at=datetime.now(),
                                url=job_url,
                                posted_date=datetime.now()
                            )
                            jobs.append(job)
                            
                    except Exception as e:
                        print(f"Error parsing HTML job element: {e}")
                        continue
        
        print(f"Extracted {len(jobs)} engineering jobs from A16Z")
        return jobs
