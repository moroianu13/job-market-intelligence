"""Data loader with cloud storage fallback for Streamlit app."""
import streamlit as st
from pathlib import Path
from google.cloud import storage
import os

DATA_FILE = "data/curated/jobs_all_labeled_ml.parquet"
GCS_BUCKET = "job-market-data"
GCS_PATH = "latest/jobs_all_labeled_ml.parquet"
LOCAL_CACHE = "/tmp/jobs_all_labeled_ml.parquet"


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data_from_gcs():
    """Download data from GCS if local file doesn't exist."""
    
    # Try local file first (for development)
    if Path(DATA_FILE).exists():
        return DATA_FILE
    
    # Try cached file
    if Path(LOCAL_CACHE).exists():
        return LOCAL_CACHE
    
    # Download from GCS
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(GCS_PATH)
        
        blob.download_to_filename(LOCAL_CACHE)
        return LOCAL_CACHE
    
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.info("Run locally: `python -m processing.label_all_jobs --ml`")
        return None


def get_data_file():
    """Get path to data file, downloading from GCS if needed."""
    return load_data_from_gcs()
