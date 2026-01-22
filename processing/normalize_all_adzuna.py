"""Data normalization module for Adzuna job postings.

Converts raw JSON files from Adzuna API into structured DataFrames.
"""
import logging
from pathlib import Path
import json
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


RAW_ROOT = Path("data/raw/adzuna")


def normalize_file(json_path: Path) -> list[dict]:
    """Normalize a single JSON file from Adzuna API.
    
    Args:
        json_path: Path to JSON file containing Adzuna API response
        
    Returns:
        List of dictionaries with normalized job data
        
    Raises:
        json.JSONDecodeError: If JSON file is malformed
        IOError: If file cannot be read
    """
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read {json_path}: {e}")
        raise

    rows = []
    for job in payload.get("results", []):
        rows.append(
            {
                "job_id": job.get("id"),
                "title": job.get("title", "") or "",
                "description": job.get("description", "") or "",
                "created": job.get("created"),
                "redirect_url": job.get("redirect_url"),
                "company": (job.get("company") or {}).get("display_name"),
                "category": (job.get("category") or {}).get("label"),
                "location": (job.get("location") or {}).get("display_name"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "run_date": json_path.parts[-4],  # YYYY-MM-DD
                "country": json_path.parts[-3],   # de / ro / gb
                "query": json_path.parts[-2],     # data_scientist, etc
                "source_file": str(json_path),
            }
        )
    return rows


def load_all_raw() -> pd.DataFrame:
    """Load and normalize all raw Adzuna JSON files.
    
    Searches for all page_*.json files under RAW_ROOT and normalizes them
    into a single DataFrame.
    
    Returns:
        DataFrame with all normalized job postings
        
    Raises:
        FileNotFoundError: If RAW_ROOT directory doesn't exist
    """
    if not RAW_ROOT.exists():
        logger.error(f"Raw data directory not found: {RAW_ROOT}")
        raise FileNotFoundError(f"Directory {RAW_ROOT} does not exist")
    
    rows = []
    file_count = 0
    
    for json_file in RAW_ROOT.rglob("page_*.json"):
        try:
            rows.extend(normalize_file(json_file))
            file_count += 1
        except Exception as e:
            logger.warning(f"Skipping file {json_file}: {e}")
            continue
    
    logger.info(f"Loaded {file_count} files with {len(rows)} job records")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    logger.info("Loading raw data...")
    df = load_all_raw()
    logger.info(f"Loaded {len(df)} rows")
    logger.info(f"\nFirst few rows:\n{df.head()}")
