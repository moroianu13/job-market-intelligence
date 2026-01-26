"""Data loader with GitHub Releases fallback for Streamlit app."""
import streamlit as st
from pathlib import Path
import requests
import re

# Try both ML and rule-based filenames
DATA_FILES = [
    "data/curated/jobs_all_labeled_ml.parquet",
    "data/curated/jobs_all_labeled.parquet"
]
GITHUB_API_URL = "https://api.github.com/repos/moroianu13/job-market-intelligence/releases"
GITHUB_RELEASE_BASE = "https://github.com/moroianu13/job-market-intelligence/releases/download"
LOCAL_CACHE_DIR = Path("/tmp/job_data")


@st.cache_data(ttl=3600)
def get_available_dates():
    """Get list of available data dates from GitHub Releases."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        releases = response.json()
        
        # Extract dates from tags like "data-2026-01-22"
        dates = []
        for release in releases:
            tag = release.get('tag_name', '')
            if tag.startswith('data-'):
                date = tag.replace('data-', '')
                dates.append(date)
        
        return sorted(dates, reverse=True)  # Most recent first
    except Exception as e:
        st.warning(f"Could not fetch available dates: {e}")
        return ['latest']


@st.cache_data(ttl=3600)
def load_data_from_github(date_tag='latest'):
    """Download data from GitHub Releases for a specific date."""
    
    # Try local files first (for development)
    for data_file in DATA_FILES:
        if Path(data_file).exists():
            return data_file
    
    # Try cached file for this date
    LOCAL_CACHE_DIR.mkdir(exist_ok=True)
    cache_file = LOCAL_CACHE_DIR / f"jobs_{date_tag}.parquet"
    
    if cache_file.exists():
        return str(cache_file)
    
    # Download from GitHub Releases - try both filenames
    filenames = ["jobs_all_labeled_ml.parquet", "jobs_all_labeled.parquet"]
    
    for filename in filenames:
        try:
            if date_tag == 'latest':
                url = f"{GITHUB_RELEASE_BASE}/latest/{filename}"
            else:
                url = f"{GITHUB_RELEASE_BASE}/data-{date_tag}/{filename}"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            
            return str(cache_file)
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                continue  # Try next filename
            raise
    
    # If both failed
    st.error(f"Failed to load data for {date_tag}: File not found in release")
    st.info("Run locally: `python -m processing.label_all_jobs --ml`")
    return None


def get_data_file(selected_date='latest'):
    """Get path to data file for selected date."""
    return load_data_from_github(selected_date)
