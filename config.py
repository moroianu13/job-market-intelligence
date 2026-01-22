"""Centralized configuration for the job market intelligence project."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Root directories
PROJECT_ROOT = Path(__file__).parent
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_ROOT / "raw" / "adzuna"
CURATED_DATA_DIR = DATA_ROOT / "curated"
SNAPSHOTS_DIR = CURATED_DATA_DIR / "snapshots"
MOCK_DATA_DIR = DATA_ROOT / "raw" / "mock"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
GHOST_JOBS_DIR = REPORTS_DIR / "ghost_jobs"

# API Credentials
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


@dataclass(frozen=True)
class AdzunaConfig:
    """Configuration for Adzuna API data collection."""
    
    countries: Tuple[str, ...] = (
        "de",  # Germany
        "pl",  # Poland
        "gb",  # United Kingdom
        "at",  # Austria
        "nl",  # Netherlands
        "be",  # Belgium
        "fr",  # France
        "es",  # Spain
        "it",  # Italy
    )
    
    queries: Tuple[str, ...] = (
        "data scientist",
        "data engineer",
        "machine learning engineer",
    )
    
    results_per_page: int = 50
    pages_per_query: int = 2
    sleep_seconds: float = 2.0
    request_timeout: int = 30


# Export defaults for easy access
DEFAULT_COUNTRIES = AdzunaConfig.countries
DEFAULT_QUERIES = AdzunaConfig.queries
DEFAULT_PAGES_PER_QUERY = AdzunaConfig.pages_per_query


@dataclass(frozen=True)
class RoleConfig:
    """Configuration for role classification."""
    
    roles: Tuple[str, ...] = (
        "data_scientist",
        "data_engineer",
        "machine_learning_engineer",
        "data_analyst",
        "cybersecurity_specialist",
        "devops_engineer",
        "software_engineer",
        "other",
    )


# Helper functions
def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        RAW_DATA_DIR,
        CURATED_DATA_DIR,
        MOCK_DATA_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        REPORTS_DIR / "eda",
        REPORTS_DIR / "demo",
        MODELS_DIR / "role_classifier",
        MODELS_DIR / "salary",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_latest_model_dir(model_type: str) -> Path:
    """Get the latest model directory for a given model type."""
    base_dir = MODELS_DIR / model_type
    if not base_dir.exists():
        raise FileNotFoundError(f"No models found in {base_dir}")
    
    model_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    if not model_dirs:
        raise FileNotFoundError(f"No model directories found in {base_dir}")
    
    return sorted(model_dirs)[-1]


def validate_api_credentials() -> bool:
    """Check if Adzuna API credentials are configured."""
    return bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)
    
    default_role: str = "other"


# Create directories if they don't exist
CURATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
