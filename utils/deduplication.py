from typing import List, Optional
from models import JobPosting


def is_duplicate(new_job: JobPosting, existing_jobs: List[JobPosting], 
                 similarity_threshold: float = 0.85) -> bool:
    """
    Check if a job is a duplicate of an existing job.
    
    Uses fuzzy matching on company + title combination.
    Falls back to simple string comparison if rapidfuzz not available.
    
    Args:
        new_job: The new job to check
        existing_jobs: List of existing jobs
        similarity_threshold: Threshold for similarity (0-1), default 0.85
    
    Returns:
        True if duplicate found, False otherwise
    """
    new_company_lower = new_job.company.lower().strip()
    new_title_lower = new_job.title.lower().strip()
    new_key = f"{new_company_lower}|{new_title_lower}"
    
    # Try using rapidfuzz if available
    try:
        from rapidfuzz import fuzz
        
        for existing_job in existing_jobs:
            existing_company_lower = existing_job.company.lower().strip()
            existing_title_lower = existing_job.title.lower().strip()
            existing_key = f"{existing_company_lower}|{existing_title_lower}"
            
            # Check full string similarity
            ratio = fuzz.ratio(new_key, existing_key) / 100.0
            if ratio >= similarity_threshold:
                return True
            
            # Also check company similarity (sometimes titles vary slightly)
            company_ratio = fuzz.ratio(new_company_lower, existing_company_lower) / 100.0
            if company_ratio >= 0.95:  # Very similar company names
                # Check if titles are somewhat similar
                title_ratio = fuzz.ratio(new_title_lower, existing_title_lower) / 100.0
                if title_ratio >= 0.7:  # Titles are similar enough
                    return True
    
    except ImportError:
        # Fallback to simple string comparison
        for existing_job in existing_jobs:
            existing_company_lower = existing_job.company.lower().strip()
            existing_title_lower = existing_job.title.lower().strip()
            
            # Exact match check
            if (new_company_lower == existing_company_lower and 
                new_title_lower == existing_title_lower):
                return True
            
            # Similar company name check (simple)
            if new_company_lower == existing_company_lower:
                # Check if titles are very similar (simple substring check)
                if (new_title_lower in existing_title_lower or 
                    existing_title_lower in new_title_lower):
                    return True
    
    return False


def deduplicate_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    """
    Remove duplicate jobs from a list.
    
    Args:
        jobs: List of jobs to deduplicate
    
    Returns:
        Deduplicated list of jobs
    """
    if not jobs:
        return []
    
    unique_jobs = []
    seen_ids = set()
    
    for job in jobs:
        job_id = job.generate_id()
        
        # Check by ID first (fastest)
        if job_id in seen_ids:
            continue
        
        # Check by similarity
        if is_duplicate(job, unique_jobs):
            continue
        
        # Add to unique jobs
        unique_jobs.append(job)
        seen_ids.add(job_id)
    
    return unique_jobs

