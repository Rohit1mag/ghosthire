"""Shared location validation utilities for all scrapers"""
import re
from typing import Optional

# Whitelist of valid locations (cities, countries, regions)
VALID_LOCATIONS = {
    # Remote/Work type
    'remote', 'onsite', 'hybrid', 'anywhere',
    
    # US Cities
    'san francisco', 'sf', 'bay area', 'silicon valley', 'palo alto', 'mountain view',
    'new york', 'nyc', 'manhattan', 'brooklyn',
    'seattle', 'austin', 'boston', 'chicago', 'los angeles', 'la',
    'denver', 'portland', 'atlanta', 'miami', 'philadelphia', 'dallas',
    'san diego', 'washington dc', 'dc', 'boulder', 'raleigh', 'durham',
    'minneapolis', 'detroit', 'phoenix', 'tucson', 'nashville', 'memphis',
    'indianapolis', 'columbus', 'cincinnati', 'kansas city', 'omaha',
    'salt lake city', 'las vegas', 'orlando', 'tampa',
    
    # US States (abbreviations)
    'ca', 'ny', 'wa', 'tx', 'ma', 'il', 'co', 'or', 'ga', 'fl', 'pa',
    'nc', 'sc', 'tn', 'mi', 'oh', 'in', 'mo', 'nv', 'az', 'ut',
    
    # Countries
    'usa', 'united states', 'us', 'canada', 'uk', 'united kingdom',
    'germany', 'france', 'spain', 'italy', 'netherlands', 'sweden',
    'norway', 'denmark', 'switzerland', 'australia', 'new zealand',
    'japan', 'singapore', 'india', 'china', 'brazil', 'mexico',
    'poland', 'portugal', 'belgium', 'austria', 'ireland',
    
    # European Cities
    'london', 'berlin', 'paris', 'amsterdam', 'barcelona', 'madrid',
    'stockholm', 'oslo', 'copenhagen', 'zurich', 'dublin', 'edinburgh',
    'vienna', 'lisbon', 'brussels', 'warsaw', 'milan', 'rome',
    'munich', 'hamburg', 'frankfurt', 'lyon', 'toulouse',
    
    # Asian Cities
    'tokyo', 'singapore', 'hong kong', 'bangalore', 'mumbai', 'delhi',
    'sydney', 'melbourne', 'beijing', 'shanghai', 'seoul', 'taipei',
    
    # Regions
    'europe', 'north america', 'south america', 'asia', 'australia',
    'east coast', 'west coast', 'northeast', 'southwest', 'midwest',
}

# Location normalization map
LOCATION_NORMALIZE = {
    'sf': 'san francisco',
    'nyc': 'new york',
    'la': 'los angeles',
    'dc': 'washington dc',
    'bay area': 'san francisco',
    'silicon valley': 'san francisco',
    'united states': 'usa',
    'united kingdom': 'uk',
    'us': 'usa',
}


def is_valid_location(location: str) -> bool:
    """Validate that extracted text is actually a location"""
    if not location or len(location) < 2:
        return False
    
    location_lower = location.lower()
    
    # Reject common non-location words that might match patterns
    invalid_words = [
        'experience', 'years', 'role', 'position', 'job', 'opportunity',
        'company', 'team', 'work', 'working', 'looking', 'seeking',
        'hiring', 'developer', 'engineer', 'software', 'technical',
        'skills', 'requirements', 'qualifications', 'salary', 'compensation',
        'benefits', 'equity', 'stock', 'options', 'package', 'offer',
        'the', 'and', 'or', 'for', 'with', 'from', 'to', 'at', 'in',
        'this', 'that', 'these', 'those', 'a', 'an',
    ]
    
    if location_lower in invalid_words:
        return False
    
    # Reject if it contains common sentence words (unless it's a known multi-word location)
    valid_multi_word = ['san francisco', 'new york', 'los angeles', 'san diego',
                       'salt lake city', 'kansas city', 'las vegas', 'washington dc',
                       'hong kong', 'new zealand', 'south america', 'north america',
                       'silicon valley', 'bay area', 'east coast', 'west coast']
    
    words = location_lower.split()
    if len(words) > 3:
        # Too many words - likely a sentence
        if location_lower not in valid_multi_word:
            return False
    
    # Reject if it's too long (locations are usually short)
    if len(location) > 50:
        return False
    
    # Reject if it contains numbers (locations don't usually have numbers)
    if re.search(r'\d', location):
        return False
    
    # Reject if it contains email-like patterns
    if '@' in location or '.com' in location_lower:
        return False
    
    return True


def normalize_location(location: str) -> str:
    """Normalize a location string"""
    location_lower = location.lower()
    return LOCATION_NORMALIZE.get(location_lower, location_lower)


def validate_and_normalize_location(location: str) -> Optional[str]:
    """Validate and normalize a location, returning None if invalid"""
    if not location:
        return None
    
    location_lower = location.lower()
    
    # Check if it's in our whitelist
    if location_lower in VALID_LOCATIONS:
        normalized = normalize_location(location_lower)
        if is_valid_location(normalized):
            return normalized.title()
    
    # Check if normalized version is valid
    normalized = normalize_location(location_lower)
    if normalized in VALID_LOCATIONS and is_valid_location(normalized):
        return normalized.title()
    
    return None

