from datetime import datetime, timedelta
from typing import Optional


def calculate_hidden_score(source: str, posted_date: Optional[datetime] = None, 
                          scraped_at: Optional[datetime] = None) -> int:
    """
    Calculate hidden score based on source weight and recency.
    
    Source weights:
    - HN comments: 90
    - YC jobs: 80
    - Wellfound: 70
    - Others: 20
    
    Recency bonus:
    - Within 24 hours: +10
    - Within 1 week: +5
    - Within 2 weeks: +0
    
    Returns score 0-100
    """
    # Source weight mapping
    source_weights = {
        'hn': 90,
        'hn who\'s hiring': 90,
        'hackernews': 90,
        'yc': 80,
        'ycombinator': 80,
        'wellfound': 70,
        'angellist': 70,
        'remoteok': 60,
        'weworkremotely': 50,
        'github jobs': 40,
        'stackoverflow': 30,
    }
    
    # Normalize source name
    source_lower = source.lower().strip()
    
    # Get base score from source
    base_score = source_weights.get(source_lower, 20)
    
    # Calculate recency bonus
    recency_bonus = 0
    if posted_date:
        date_to_check = posted_date
    elif scraped_at:
        date_to_check = scraped_at
    else:
        date_to_check = datetime.now()
    
    now = datetime.now()
    age = now - date_to_check
    
    if age <= timedelta(hours=24):
        recency_bonus = 10
    elif age <= timedelta(days=7):
        recency_bonus = 5
    elif age <= timedelta(days=14):
        recency_bonus = 0
    # Older than 2 weeks gets no bonus
    
    # Calculate final score (cap at 100)
    final_score = min(base_score + recency_bonus, 100)
    
    return final_score

