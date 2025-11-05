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


class HNScraper:
    """Scraper for HackerNews Who's Hiring threads"""
    
    BASE_URL = "https://news.ycombinator.com"
    
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
    
    def fetch_thread(self, thread_url: str) -> BeautifulSoup:
        """Fetch and parse the HN thread HTML"""
        response = self.session.get(thread_url)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    
    def extract_comment_id(self, comment_elem) -> Optional[str]:
        """Extract comment ID from comment element"""
        # HN comments have IDs like "c_12345678" in anchor links
        # Look for anchor with href="#c_12345678" pattern
        anchor = comment_elem.find('a', href=re.compile(r'#c_\d+'))
        if anchor:
            href = anchor.get('href', '')
            match = re.search(r'c_\d+', href)
            if match:
                return match.group()
        
        # Try to find ID in the element itself
        if comment_elem.get('id'):
            return comment_elem.get('id')
        
        # Look for parent tr with id
        parent_tr = comment_elem.find_parent('tr')
        if parent_tr and parent_tr.get('id'):
            return parent_tr.get('id')
        
        return None
    
    def parse_comment_text(self, comment_elem) -> str:
        """Extract the text content from a comment element"""
        # HN comments can be in span.commtext or div.commtext
        comment_text = comment_elem.find('span', class_='commtext')
        if not comment_text:
            comment_text = comment_elem.find('div', class_='commtext')
        if not comment_text:
            # Fallback: try to find any element with commtext class
            comment_text = comment_elem.find(class_=re.compile(r'commtext'))
        if not comment_text:
            return ""
        
        # Get all text, preserving some structure
        text = comment_text.get_text(separator='\n', strip=True)
        return text
    
    def extract_company_name(self, text: str) -> str:
        """Extract company name from comment text"""
        lines = text.split('\n')
        if not lines:
            return "Unknown"
        
        first_line = lines[0].strip()
        
        # Common patterns:
        # "Company Name | Role"
        # "Company Name - Role"
        # "Company Name: Role"
        # Sometimes company name is in bold or at the start
        
        # Try to extract from common separators
        for separator in ['|', '-', ':', '•']:
            if separator in first_line:
                parts = first_line.split(separator, 1)
                company = parts[0].strip()
                if company and len(company) < 100:  # Reasonable company name length
                    return company
        
        # If no separator, use first line but limit length
        company = first_line[:100].strip()
        if not company:
            return "Unknown"
        
        return company
    
    def extract_job_title(self, text: str) -> str:
        """Extract job title from comment text"""
        lines = text.split('\n')
        if not lines:
            return "Software Engineer"
        
        first_line = lines[0].strip()
        
        # Try to extract title from common patterns
        for separator in ['|', '-', ':', '•']:
            if separator in first_line:
                parts = first_line.split(separator, 1)
                if len(parts) > 1:
                    title = parts[1].strip()
                    if title:
                        return title[:100]  # Limit length
        
        # Look for common job title keywords in first few lines
        title_keywords = [
            'engineer', 'developer', 'software', 'swe', 'sde',
            'backend', 'frontend', 'fullstack', 'full-stack',
            'devops', 'sre', 'data', 'ml', 'ai', 'architect'
        ]
        
        for line in lines[:5]:
            line_lower = line.lower()
            for keyword in title_keywords:
                if keyword in line_lower:
                    # Extract a reasonable title from this line
                    words = line.split()
                    if len(words) <= 8:  # Reasonable title length
                        return line[:100]
        
        return "Software Engineer"
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from comment text"""
        # Common location patterns
        location_patterns = [
            r'\b(remote|onsite|hybrid|anywhere)\b',
            r'\b(san francisco|sf|bay area|new york|nyc|seattle|austin|boston|chicago|los angeles|la)\b',
            r'\b(usa|united states|us|canada|uk|united kingdom|london|berlin|paris|amsterdam)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})\b',  # City, State format
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+)\b',  # City, Country format
        ]
        
        text_lower = text.lower()
        
        # Check for remote/hybrid first
        for pattern in location_patterns[:1]:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                return matches[0].title()
        
        # Check for specific locations
        for pattern in location_patterns[1:]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Look for location keywords in first few lines
        location_keywords = ['location', 'based', 'office', 'headquarters']
        lines = text.split('\n')[:10]
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in location_keywords):
                # Try to extract location from this line
                for pattern in location_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        return matches[0]
        
        return None
    
    def extract_tech_stack(self, text: str) -> List[str]:
        """Extract tech stack mentions from comment text"""
        text_lower = text.lower()
        found_tech = []
        
        for tech in self.TECH_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(tech.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_tech.append(tech.lower())
        
        return list(set(found_tech))  # Remove duplicates
    
    def extract_application_url(self, comment_elem, text: str) -> Optional[str]:
        """Extract application URL from comment"""
        # Look for links in the comment element
        links = comment_elem.find_all('a', href=True)
        
        # Common patterns for application URLs
        application_patterns = [
            r'apply|application|careers|jobs|hiring|lever\.co|greenhouse|workable|linkedin\.com/jobs',
            r'jobs\.|careers\.|hiring\.',
        ]
        
        for link in links:
            href = link.get('href', '')
            if not href or href.startswith('#'):
                continue
            
            # Check if it looks like a job application URL
            href_lower = href.lower()
            for pattern in application_patterns:
                if re.search(pattern, href_lower):
                    return href
            
            # Also check link text
            link_text = link.get_text().lower()
            if any(keyword in link_text for keyword in ['apply', 'application', 'careers', 'jobs']):
                return href
        
        # Look for URLs in text
        url_pattern = r'https?://[^\s<>"]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            url_lower = url.lower()
            if any(pattern in url_lower for pattern in ['apply', 'jobs', 'careers', 'lever', 'greenhouse', 'workable']):
                return url
        
        return None
    
    def parse_job_from_comment(self, comment_elem, thread_url: str) -> Optional[JobPosting]:
        """Parse a single comment into a JobPosting"""
        text = self.parse_comment_text(comment_elem)
        
        if not text or len(text.strip()) < 20:  # Skip very short comments
            return None
        
        # Skip if it looks like a reply or not a job posting
        text_lower = text.lower()
        skip_keywords = ['reply', '^', 'this', 'thanks', 'interested', 'pm me']
        if any(text_lower.startswith(keyword) for keyword in skip_keywords):
            return None
        
        # Skip if it's clearly a reply (looks for indentation or reply indicators)
        first_line = text.split('\n')[0] if text else ''
        if first_line.strip().startswith('>'):  # Quote indicator
            return None
        
        # Skip if doesn't contain job-related keywords
        job_keywords = ['hiring', 'engineer', 'developer', 'software', 'position', 'role', 'job', 'opportunity']
        if not any(keyword in text_lower for keyword in job_keywords):
            return None
        
        # Try to extract fields
        company = self.extract_company_name(text)
        title = self.extract_job_title(text)
        location = self.extract_location(text)
        tech_stack = self.extract_tech_stack(text)
        comment_id = self.extract_comment_id(comment_elem)
        application_url = self.extract_application_url(comment_elem, text)
        
        return JobPosting(
            company=company,
            title=title,
            location=location,
            tech_stack=tech_stack,
            raw_text=text,
            source='HN Who\'s Hiring',
            source_url=thread_url,
            scraped_at=datetime.now(),
            comment_id=comment_id,
            url=application_url
        )
    
    def scrape_thread(self, thread_url: str) -> List[JobPosting]:
        """Scrape all job postings from an HN Who's Hiring thread"""
        print(f"Fetching thread: {thread_url}")
        soup = self.fetch_thread(thread_url)
        
        # HN comments are in div.comment elements
        # Find all comment divs
        comment_divs = soup.find_all('div', class_='comment')
        
        print(f"Found {len(comment_divs)} comment elements")
        
        jobs = []
        for comment_div in comment_divs:
            job = self.parse_job_from_comment(comment_div, thread_url)
            if job:
                jobs.append(job)
        
        print(f"Extracted {len(jobs)} job postings")
        return jobs

