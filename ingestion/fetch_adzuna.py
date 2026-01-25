"""Adzuna API data ingestion module.

This module fetches job postings from the Adzuna API and saves them as JSON files.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env from project root


class EnvVarMaskFilter(logging.Filter):
    """Mask sensitive environment variable values in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for key, val in os.environ.items():
            if key.startswith("ADZUNA_") and val:
                message = message.replace(val, "***")
        record.msg = message
        record.args = ()
        return True


# Configure logging with masking filter
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/fetch_adzuna.log')
    ]
)

logger = logging.getLogger(__name__)
_mask_filter = EnvVarMaskFilter()
logger.addFilter(_mask_filter)
for handler in logger.handlers:
    handler.addFilter(_mask_filter)
# Ensure root handlers also mask secrets (covers downstream modules)
for handler in logging.getLogger().handlers:
    handler.addFilter(_mask_filter)


@dataclass(frozen=True)
class FetchConfig:
    """Configuration for Adzuna API data fetching.
    
    Attributes:
        countries: Tuple of country codes to fetch data from
        queries: Job search queries to execute
        results_per_page: Number of results per API page
        pages_per_query: Number of pages to fetch per query
        sleep_seconds: Delay between API requests to avoid rate limiting
        request_timeout: HTTP request timeout in seconds
    """
    countries: tuple[str, ...] = ("de", "pl", "gb", "at", "nl", "be", "fr", "es", "it")
    queries: tuple[str, ...] = ("data scientist", "data engineer", "machine learning engineer")
    results_per_page: int = 50
    pages_per_query: int = 2
    sleep_seconds: float = 2.0
    request_timeout: int = 30


def utc_date_str() -> str:
    """Get current UTC date as string in YYYY-MM-DD format.
    
    Returns:
        Current date in YYYY-MM-DD format
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def require_env(name: str) -> str:
    """Get required environment variable or raise error.
    
    Args:
        name: Name of the environment variable
        
    Returns:
        Value of the environment variable
        
    Raises:
        RuntimeError: If environment variable is not set
    """
    val = os.getenv(name)
    if not val:
        logger.error(f"Missing environment variable: {name}")
        raise RuntimeError(f"Missing environment variable: {name}. Put it in your .env file.")
    return val


def fetch_search_page(
    *,
    app_id: str,
    app_key: str,
    country: str,
    query: str,
    page: int,
    results_per_page: int,
    timeout: int = 30,
) -> Optional[dict[str, Any]]:
    """Fetch a single page of job search results from Adzuna API.
    
    Args:
        app_id: Adzuna API application ID
        app_key: Adzuna API application key
        country: Country code (e.g., 'de', 'gb', 'pl')
        query: Job search query string
        page: Page number to fetch
        results_per_page: Number of results per page
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing API response, or None if country unsupported
        
    Raises:
        RuntimeError: If API request fails
        requests.RequestException: If network error occurs
    """
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": results_per_page,
    }

    try:
        resp = requests.get(url, params=params, timeout=timeout)
        
        if resp.status_code != 200:
            try:
                err = resp.json()
            except Exception:
                err = {"raw": resp.text[:500]}
                
            if isinstance(err, dict) and err.get("exception") == "UNSUPPORTED_COUNTRY":
                logger.warning(f"Skipping unsupported country: {country}")
                return None
                
            path = resp.request.path_url if resp.request else f"/jobs/{country}/search/{page}"
            logger.error(
                "API request failed: status=%s, path=%s", resp.status_code, path
            )
            raise RuntimeError(
                f"Request failed: {resp.status_code}\nPath: {path}\nBody: {resp.text[:500]}"
            )
        
        return resp.json()
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching {country}/{query} page {page}: {e}")
        raise


def save_json(payload: dict[str, Any], path: Path) -> None:
    """Save JSON data to file.
    
    Args:
        payload: Dictionary to save as JSON
        path: File path where JSON will be saved
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except IOError as e:
        logger.error(f"Failed to save JSON to {path}: {e}")
        raise


def main() -> None:
    """Main function to fetch job data from Adzuna API.
    
    Fetches job postings for configured countries and queries,
    saving results to dated directories.
    """
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("Starting Adzuna data fetch")
    
    try:
        app_id = require_env("ADZUNA_APP_ID")
        app_key = require_env("ADZUNA_APP_KEY")
    except RuntimeError as e:
        logger.error("Failed to load API credentials")
        sys.exit(1)

    cfg = FetchConfig()
    run_date = utc_date_str()

    raw_root = Path("data/raw/adzuna") / run_date
    logger.info(f"Output directory: {raw_root}")

    total_files = 0
    total_jobs = 0
    failed_requests = 0
    
    for country in cfg.countries:
        for query in cfg.queries:
            safe_query = query.lower().replace(" ", "_")
            for page in range(1, cfg.pages_per_query + 1):
                logger.info(f"Fetching: country={country}, query='{query}', page={page}")
                
                try:
                    payload = fetch_search_page(
                        app_id=app_id,
                        app_key=app_key,
                        country=country,
                        query=query,
                        page=page,
                        results_per_page=cfg.results_per_page,
                        timeout=cfg.request_timeout,
                    )
                    
                    if not payload or not payload.get("results"):
                        logger.warning(f"No results for {country}/{query} page {page}")
                        continue

                    out_path = raw_root / country / safe_query / f"page_{page}.json"
                    save_json(payload, out_path)
                    
                    results_count = len(payload.get('results', []))
                    total_files += 1
                    total_jobs += results_count

                    logger.info(f"Saved {out_path} ({results_count} jobs)")
                    time.sleep(cfg.sleep_seconds)
                    
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Failed to fetch {country}/{query} page {page}: {e}")
                    continue

    logger.info(f"\n{'='*60}")
    logger.info(f"Fetch completed successfully")
    logger.info(f"Files saved: {total_files}")
    logger.info(f"Total jobs collected: {total_jobs}")
    logger.info(f"Failed requests: {failed_requests}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch job postings from Adzuna API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch with default settings
  python ingestion/fetch_adzuna.py
  
  # Fetch with custom pages
  python ingestion/fetch_adzuna.py --pages 5
  
  # Fetch specific countries only
  python ingestion/fetch_adzuna.py --countries de gb pl
        """
    )
    
    parser.add_argument(
        "--pages",
        type=int,
        help=f"Number of pages to fetch per query (default: {FetchConfig.pages_per_query})"
    )
    
    parser.add_argument(
        "--countries",
        nargs="+",
        help=f"Country codes to fetch (default: {' '.join(FetchConfig.countries)})"
    )
    
    parser.add_argument(
        "--queries",
        nargs="+",
        help='Search queries (default: "data scientist" "data engineer" "machine learning engineer")'
    )
    
    parser.add_argument(
        "--results-per-page",
        type=int,
        help=f"Results per page (default: {FetchConfig.results_per_page})"
    )
    
    parser.add_argument(
        "--sleep",
        type=float,
        help=f"Seconds to sleep between requests (default: {FetchConfig.sleep_seconds})"
    )
    
    args = parser.parse_args()
    
    # Override config with CLI arguments if provided
    if any([args.pages, args.countries, args.queries, args.results_per_page, args.sleep]):
        from dataclasses import replace
        config = FetchConfig()
        config = replace(
            config,
            pages_per_query=args.pages or config.pages_per_query,
            countries=tuple(args.countries) if args.countries else config.countries,
            queries=tuple(args.queries) if args.queries else config.queries,
            results_per_page=args.results_per_page or config.results_per_page,
            sleep_seconds=args.sleep if args.sleep is not None else config.sleep_seconds,
        )
        # Update global config
        globals()['FetchConfig'] = lambda: config
    
    main()
