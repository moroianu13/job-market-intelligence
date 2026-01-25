"""Job labeling module.

Applies role classification to normalized job data.
Supports both rule-based and ML-based classification.
"""
import argparse
import logging
import sys
from pathlib import Path
import pandas as pd

from preprocessing.role_labels import assign_roles
from processing.normalize_all_adzuna import load_all_raw
from processing.skill_extraction import extract_skills
from processing.fingerprints import add_fingerprints
from processing.salary_validation import flag_salary_quality, export_salary_debug_report


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


OUT_DIR = Path("data/curated")


def label_jobs(df: pd.DataFrame, use_ml: bool = False, model_dir: Path = None) -> pd.DataFrame:
    """Apply role labels to job DataFrame.
    
    Args:
        df: DataFrame with job data including 'title' and 'description' columns
        use_ml: If True, use ML classifier; otherwise use rule-based system
        model_dir: Directory containing trained ML model (required if use_ml=True)
        
    Returns:
        DataFrame with added 'roles' column containing list of assigned roles
    """
    df = df.copy()
    logger.info(f"Labeling {len(df)} jobs...")
    
    if use_ml:
        if model_dir is None:
            raise ValueError("model_dir must be provided when use_ml=True")
        
        logger.info(f"Using ML classifier from {model_dir}")
        from ml.role_classifier import RolePredictor
        
        predictor = RolePredictor(model_dir)
        df = predictor.predict_batch(df)
    else:
        logger.info("Using rule-based classifier")
        df["roles"] = df.apply(
            lambda r: assign_roles(r["title"], r["description"]), axis=1
        )
    
    logger.info("Role labeling completed")
    
    logger.info("Extracting skills...")
    df["skills"] = df.apply(lambda r: extract_skills(r["title"], r["description"]), axis=1)
    logger.info("Skill extraction completed")
    
    logger.info("Adding job fingerprints...")
    df = add_fingerprints(df)
    logger.info("Fingerprinting completed")
    
    logger.info("Validating salary data...")
    df = flag_salary_quality(df)
    logger.info("Salary validation completed")
    
    return df



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Label job roles using rules or ML')
    parser.add_argument(
        '--ml',
        action='store_true',
        help='Use ML classifier instead of rule-based system'
    )
    parser.add_argument(
        '--model',
        type=Path,
        default=Path('models/role_classifier/2026-01-22'),
        help='Path to trained ML model directory (default: models/role_classifier/2026-01-22)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output file path (default: data/curated/jobs_all_labeled.parquet or jobs_all_labeled_ml.parquet)'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("Starting job labeling pipeline")
        logger.info(f"Classification method: {'ML' if args.ml else 'Rule-based'}")
        
        # Load raw data
        logger.info("Loading raw data...")
        df = load_all_raw()
        logger.info(f"Loaded {len(df)} job records")
        
        # Apply role labels
        df = label_jobs(df, use_ml=args.ml, model_dir=args.model if args.ml else None)
        
        # Export salary quality report
        logger.info("\nExporting salary quality report...")
        try:
            from datetime import datetime
            run_date = datetime.now().strftime('%Y-%m-%d')
            export_salary_debug_report(df, run_date=run_date)
        except Exception as e:
            logger.warning(f"Failed to export salary debug report: {e}")
        
        # Count role distribution
        role_counts = df["roles"].explode().value_counts()
        logger.info(f"\nRole distribution:\n{role_counts}")

        # Save curated data
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Use different output file for ML vs rule-based
        if args.output:
            out_path = args.output
        else:
            filename = "jobs_all_labeled_ml.parquet" if args.ml else "jobs_all_labeled.parquet"
            out_path = OUT_DIR / filename
        
        df.to_parquet(out_path, index=False)
        
        logger.info(f"\nSaved labeled data to: {out_path}")
        logger.info(f"Total records: {len(df)}")
        logger.info(f"\nSample data:")
        logger.info(f"\n{df[['title', 'roles', 'country', 'salary_min', 'salary_max']].head()}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
