"""Data loader with GitHub Releases fallback for Streamlit app."""
import streamlit as st
from pathlib import Path
import requests

DATA_FILE = "data/curated/jobs_all_labeled_ml.parquet"
GITHUB_RELEASE_URL = "https://github.com/moroianu13/job-market-intelligence/releases/download/latest/jobs_all_labeled_ml.parquet"
LOCAL_CACHE = "/tmp/jobs_all_labeled_ml.parquet"


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data_from_github():
    """Download data from GitHub Releases if local file doesn't exist."""
    
    # Try local file first (for development)
    if Path(DATA_FILE).exists():
        return DATA_FILE
    
    # Try cached file
    if Path(LOCAL_CACHE).exists():
        return LOCAL_CACHE
    
    # Download from GitHub Releases
    try:
        response = requests.get(GITHUB_RELEASE_URL, timeout=30)
        response.raise_for_status()
        
        with open(LOCAL_CACHE, 'wb') as f:
            f.write(response.content)
        
        return LOCAL_CACHE
    
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.info("Run locally: `python -m processing.label_all_jobs --ml`")
        return None


def get_data_file():
    """Get path to data file, downloading from GitHub Releases if needed."""
    return load_data_from_github()
