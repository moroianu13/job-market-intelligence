"""Job fingerprinting for tracking reposts and ghost jobs.

This module provides deterministic fingerprinting of job postings
to identify the same job across multiple scraping runs, even when
job IDs change or jobs are reposted.

Fingerprint strategy:
- Normalized title (lowercase, whitespace normalized)
- Normalized company name
- Normalized location
- Redirect URL domain (not full URL to handle tracking params)

This approach balances:
- Stability: Same job = same fingerprint
- Sensitivity: Different jobs = different fingerprints
- Robustness: Minor text changes don't break tracking
"""
import hashlib
import re
from typing import Optional
from urllib.parse import urlparse

import pandas as pd


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for fingerprinting.
    
    Converts to lowercase, removes extra whitespace, and strips leading/trailing space.
    This makes fingerprints robust to minor formatting changes.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text, or empty string if input is None/empty
    """
    if not text or pd.isna(text):
        return ""
    
    # Convert to lowercase
    text = str(text).lower()
    
    # Normalize whitespace (multiple spaces/tabs/newlines -> single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_domain(url: Optional[str]) -> str:
    """Extract domain from URL.
    
    Extracts the network location (domain) from a URL, ignoring
    query parameters, fragments, and paths. This makes fingerprints
    robust to tracking parameters and URL variations.
    
    Args:
        url: Full URL string
        
    Returns:
        Domain (netloc) or empty string if invalid/empty URL
        
    Examples:
        >>> extract_domain("https://example.com/jobs/123?ref=abc")
        'example.com'
        >>> extract_domain("http://jobs.example.com/apply")
        'jobs.example.com'
    """
    if not url or pd.isna(url):
        return ""
    
    try:
        parsed = urlparse(str(url))
        return parsed.netloc.lower()
    except Exception:
        return ""


def make_fingerprint(row: pd.Series) -> str:
    """Create deterministic fingerprint for a job posting.
    
    Combines normalized title, company, location, and URL domain
    into a SHA1 hash. This provides a stable identifier that:
    - Survives reposts (same job = same fingerprint)
    - Handles minor text variations
    - Is deterministic and reproducible
    
    Args:
        row: pandas Series with columns: title, company, location, redirect_url
        
    Returns:
        40-character SHA1 hex digest
        
    Note:
        If any required field is missing, it's treated as empty string.
        This ensures fingerprints can still be generated for incomplete data.
    """
    # Extract and normalize components
    title = normalize_text(row.get("title"))
    company = normalize_text(row.get("company"))
    location = normalize_text(row.get("location"))
    url_domain = extract_domain(row.get("redirect_url"))
    
    # Combine into fingerprint string
    # Format: title|company|location|domain
    # Using | as separator (unlikely in normalized text)
    fingerprint_str = f"{title}|{company}|{location}|{url_domain}"
    
    # Hash for consistent length and privacy
    fingerprint_hash = hashlib.sha1(fingerprint_str.encode('utf-8')).hexdigest()
    
    return fingerprint_hash


def add_fingerprints(df: pd.DataFrame) -> pd.DataFrame:
    """Add job_fingerprint column to DataFrame.
    
    Applies make_fingerprint to each row and adds result as new column.
    
    Args:
        df: DataFrame with job data (must have: title, company, location, redirect_url)
        
    Returns:
        DataFrame with added 'job_fingerprint' column
    """
    df = df.copy()
    df['job_fingerprint'] = df.apply(make_fingerprint, axis=1)
    return df
