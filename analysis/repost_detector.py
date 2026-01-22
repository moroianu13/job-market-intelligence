"""Ghost job and repost detection.

Analyzes historical job data snapshots to identify:
- Reposts: Same job appearing across multiple scraping runs
- Ghost jobs: Jobs that remain posted for extended periods

This module loads all historical snapshots, tracks jobs by fingerprint,
and applies heuristics to identify suspicious posting patterns.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config import SNAPSHOTS_DIR, GHOST_JOBS_DIR


logger = logging.getLogger(__name__)


def load_all_snapshots(snapshots_dir: Path = SNAPSHOTS_DIR) -> pd.DataFrame:
    """Load all historical snapshot files into single DataFrame.
    
    Scans for all jobs_all_labeled_ml.parquet files under snapshots/<date>/
    and concatenates them with run_date tracking.
    
    Args:
        snapshots_dir: Root directory containing dated snapshot folders
        
    Returns:
        DataFrame with all historical jobs and 'run_date' column
        
    Raises:
        FileNotFoundError: If no snapshot files found
    """
    snapshots_dir = Path(snapshots_dir)
    
    if not snapshots_dir.exists():
        raise FileNotFoundError(f"Snapshots directory not found: {snapshots_dir}")
    
    # Find all snapshot parquet files
    snapshot_files = list(snapshots_dir.glob("*/jobs_all_labeled_ml.parquet"))
    
    if not snapshot_files:
        raise FileNotFoundError(f"No snapshot files found in {snapshots_dir}")
    
    logger.info(f"Found {len(snapshot_files)} snapshot files")
    
    # Load each snapshot with its run_date
    dfs = []
    for snapshot_file in sorted(snapshot_files):
        # Extract run_date from path (snapshots/YYYY-MM-DD/...)
        run_date = snapshot_file.parent.name
        
        try:
            df = pd.read_parquet(snapshot_file)
            df['run_date'] = run_date
            dfs.append(df)
            logger.info(f"Loaded {len(df)} jobs from {run_date}")
        except Exception as e:
            logger.warning(f"Failed to load {snapshot_file}: {e}")
    
    if not dfs:
        raise ValueError("No valid snapshot files could be loaded")
    
    # Concatenate all snapshots
    history_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total historical jobs: {len(history_df)}")
    
    return history_df


def compute_repost_metrics(history_df: pd.DataFrame) -> pd.DataFrame:
    """Compute repost and persistence metrics for each job fingerprint.
    
    Groups jobs by fingerprint and calculates:
    - first_seen: First date this job appeared
    - last_seen: Last date this job appeared
    - days_seen: Number of distinct dates job was observed
    - repost_count: Total number of times job appeared (across all runs)
    - active_span_days: Days between first and last observation
    - countries_seen: List of unique countries where job appeared
    - roles_seen: List of unique roles assigned to job
    
    Args:
        history_df: DataFrame with columns: job_fingerprint, run_date, country, roles
        
    Returns:
        DataFrame with one row per unique job_fingerprint and computed metrics
    """
    logger.info("Computing repost metrics by job fingerprint...")
    
    # Convert run_date to datetime for calculations
    history_df = history_df.copy()
    history_df['run_date_dt'] = pd.to_datetime(history_df['run_date'])
    
    # Group by fingerprint
    grouped = history_df.groupby('job_fingerprint').agg({
        'run_date': ['min', 'max', 'nunique', 'count'],
        'run_date_dt': ['min', 'max'],
        'country': lambda x: sorted(set(x)),
        'roles': lambda x: sorted(set(str(r) for r in x if pd.notna(r))),
        'title': 'first',
        'company': 'first',
        'location': 'first',
        'redirect_url': 'first'
    })
    
    # Flatten multi-index columns
    grouped.columns = [
        'first_seen', 'last_seen', 'days_seen', 'repost_count',
        'first_seen_dt', 'last_seen_dt',
        'countries_seen', 'roles_seen',
        'title', 'company', 'location', 'redirect_url'
    ]
    
    # Calculate active span in days
    grouped['active_span_days'] = (
        grouped['last_seen_dt'] - grouped['first_seen_dt']
    ).dt.days
    
    # Drop datetime columns (keep string dates)
    grouped = grouped.drop(columns=['first_seen_dt', 'last_seen_dt'])
    
    # Reset index to make job_fingerprint a column
    grouped = grouped.reset_index()
    
    logger.info(f"Computed metrics for {len(grouped)} unique job fingerprints")
    
    return grouped


def flag_ghost_jobs(
    repost_df: pd.DataFrame,
    min_days_seen: int = 3,
    min_active_span_days: int = 30
) -> pd.DataFrame:
    """Flag potential ghost jobs based on persistence heuristics.
    
    Ghost job heuristic:
    - Job appears on >= min_days_seen distinct scraping dates
    - AND active span (last_seen - first_seen) >= min_active_span_days days
    
    Rationale:
    - Real jobs get filled within weeks
    - Ghost jobs stay posted for months to collect resumes
    - Requires multiple observations to avoid false positives
    
    Args:
        repost_df: DataFrame with repost metrics (from compute_repost_metrics)
        min_days_seen: Minimum distinct dates job must appear (default: 3)
        min_active_span_days: Minimum days between first and last seen (default: 30)
        
    Returns:
        DataFrame with added 'ghost_job' boolean column
    """
    df = repost_df.copy()
    
    # Apply ghost job heuristic
    df['ghost_job'] = (
        (df['days_seen'] >= min_days_seen) &
        (df['active_span_days'] >= min_active_span_days)
    )
    
    ghost_count = df['ghost_job'].sum()
    ghost_pct = 100 * ghost_count / len(df) if len(df) > 0 else 0
    
    logger.info(f"Flagged {ghost_count} ghost jobs ({ghost_pct:.1f}%)")
    logger.info(f"Heuristic: days_seen>={min_days_seen} AND active_span>={min_active_span_days} days")
    
    return df


def generate_ghost_job_report(
    ghost_df: pd.DataFrame,
    output_dir: Path,
    run_date: str,
    top_n: int = 100
) -> Tuple[Path, Path]:
    """Generate ghost job detection report.
    
    Creates:
    1. CSV file with all flagged ghost jobs
    2. JSON summary with statistics
    
    Args:
        ghost_df: DataFrame with ghost_job flags and metrics
        output_dir: Base directory for reports (e.g., reports/ghost_jobs)
        run_date: Date string (YYYY-MM-DD) for organizing reports
        top_n: Number of top ghost jobs to include in summary (default: 100)
        
    Returns:
        Tuple of (csv_path, summary_path)
    """
    output_dir = Path(output_dir)
    report_dir = output_dir / run_date
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter to only ghost jobs
    ghosts = ghost_df[ghost_df['ghost_job']].copy()
    
    if len(ghosts) == 0:
        logger.warning("No ghost jobs detected in this analysis")
    
    # Sort by repost_count (descending) then active_span_days (descending)
    ghosts = ghosts.sort_values(
        by=['repost_count', 'active_span_days'],
        ascending=[False, False]
    )
    
    # Save full ghost jobs CSV
    csv_path = report_dir / "ghost_jobs.csv"
    ghosts.to_csv(csv_path, index=False)
    logger.info(f"✅ Ghost jobs CSV saved: {csv_path}")
    
    # Generate summary statistics
    summary = {
        'analysis_date': run_date,
        'total_unique_jobs': len(ghost_df),
        'ghost_jobs_count': len(ghosts),
        'ghost_jobs_pct': round(100 * len(ghosts) / len(ghost_df), 2) if len(ghost_df) > 0 else 0,
        'metrics': {
            'avg_days_seen': round(ghosts['days_seen'].mean(), 2) if len(ghosts) > 0 else 0,
            'avg_active_span_days': round(ghosts['active_span_days'].mean(), 2) if len(ghosts) > 0 else 0,
            'avg_repost_count': round(ghosts['repost_count'].mean(), 2) if len(ghosts) > 0 else 0,
            'max_active_span_days': int(ghosts['active_span_days'].max()) if len(ghosts) > 0 else 0,
            'max_repost_count': int(ghosts['repost_count'].max()) if len(ghosts) > 0 else 0,
        },
        'top_ghost_jobs': []
    }
    
    # Add top N ghost jobs to summary
    for _, row in ghosts.head(top_n).iterrows():
        summary['top_ghost_jobs'].append({
            'job_fingerprint': row['job_fingerprint'],
            'title': row['title'],
            'company': row['company'],
            'location': row['location'],
            'first_seen': row['first_seen'],
            'last_seen': row['last_seen'],
            'days_seen': int(row['days_seen']),
            'repost_count': int(row['repost_count']),
            'active_span_days': int(row['active_span_days']),
            'countries_seen': row['countries_seen'],
            'roles_seen': row['roles_seen']
        })
    
    # Save summary JSON
    summary_path = report_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"✅ Summary JSON saved: {summary_path}")
    
    return csv_path, summary_path


def detect_ghost_jobs(
    run_date: str,
    snapshots_dir: Path = SNAPSHOTS_DIR,
    output_dir: Path = GHOST_JOBS_DIR,
    min_days_seen: int = 3,
    min_active_span_days: int = 30
) -> Tuple[Path, Path]:
    """End-to-end ghost job detection pipeline.
    
    Main entry point for ghost job analysis:
    1. Load all historical snapshots
    2. Compute repost metrics per job fingerprint
    3. Flag ghost jobs using heuristic
    4. Generate report
    
    Args:
        run_date: Analysis date (YYYY-MM-DD)
        snapshots_dir: Directory containing snapshot folders
        output_dir: Directory for output reports
        min_days_seen: Ghost job threshold (distinct dates)
        min_active_span_days: Ghost job threshold (active span)
        
    Returns:
        Tuple of (csv_path, summary_path)
    """
    logger.info("="*60)
    logger.info("GHOST JOB DETECTION")
    logger.info("="*60)
    logger.info(f"Analysis date: {run_date}")
    logger.info(f"Snapshots dir: {snapshots_dir}")
    logger.info(f"Output dir: {output_dir}")
    logger.info("")
    
    # Load historical data
    history_df = load_all_snapshots(snapshots_dir)
    
    # Compute repost metrics
    repost_df = compute_repost_metrics(history_df)
    
    # Flag ghost jobs
    ghost_df = flag_ghost_jobs(repost_df, min_days_seen, min_active_span_days)
    
    # Generate report
    csv_path, summary_path = generate_ghost_job_report(
        ghost_df, output_dir, run_date
    )
    
    logger.info("")
    logger.info("="*60)
    logger.info("GHOST JOB DETECTION COMPLETE")
    logger.info("="*60)
    
    return csv_path, summary_path


if __name__ == "__main__":
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Detect ghost jobs from historical data')
    parser.add_argument(
        '--run-date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Analysis date (YYYY-MM-DD), default: today'
    )
    parser.add_argument(
        '--min-days-seen',
        type=int,
        default=3,
        help='Minimum distinct dates job must appear (default: 3)'
    )
    parser.add_argument(
        '--min-active-span',
        type=int,
        default=30,
        help='Minimum days between first and last seen (default: 30)'
    )
    
    args = parser.parse_args()
    
    detect_ghost_jobs(
        run_date=args.run_date,
        min_days_seen=args.min_days_seen,
        min_active_span_days=args.min_active_span
    )
