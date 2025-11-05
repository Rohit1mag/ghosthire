from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json
import hashlib


@dataclass
class JobPosting:
    """Represents a scraped job posting"""
    company: str
    title: str
    location: Optional[str]
    tech_stack: List[str]
    raw_text: str
    source: str
    source_url: str
    scraped_at: datetime
    comment_id: Optional[str] = None
    url: Optional[str] = None  # Application URL
    posted_date: Optional[datetime] = None  # Original post date
    hidden_score: Optional[int] = None  # Calculated hidden score (0-100)
    
    def generate_id(self) -> str:
        """Generate unique ID from company + title"""
        combined = f"{self.company.lower().strip()}|{self.title.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization (unified format)"""
        posted_date_str = self.posted_date.isoformat() if self.posted_date else None
        return {
            'id': self.generate_id(),
            'company': self.company,
            'title': self.title,
            'location': self.location,
            'tech_stack': self.tech_stack,
            'url': self.url or self.source_url,  # Fallback to source_url if no URL
            'source': self.source.lower() if self.source else 'unknown',
            'posted_date': posted_date_str or self.scraped_at.isoformat(),
            'hidden_score': self.hidden_score or 0
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'JobPosting':
        """Create from dictionary"""
        posted_date = None
        if data.get('posted_date'):
            posted_date = datetime.fromisoformat(data['posted_date'])
        
        return cls(
            company=data['company'],
            title=data['title'],
            location=data.get('location'),
            tech_stack=data.get('tech_stack', []),
            raw_text=data.get('raw_text', ''),
            source=data.get('source', 'unknown'),
            source_url=data.get('source_url', data.get('url', '')),
            scraped_at=datetime.fromisoformat(data.get('scraped_at', data.get('posted_date'))),
            comment_id=data.get('comment_id'),
            url=data.get('url'),
            posted_date=posted_date,
            hidden_score=data.get('hidden_score')
        )

