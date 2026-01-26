#!/usr/bin/env python3
"""
One-Command Pipeline Runner for Job Market Intelligence.

Orchestrates the entire data pipeline with fine-grained control over steps.
Supports idempotent execution with --force flag to rerun completed steps.
"""
import argparse
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import (
    PROJECT_ROOT, CURATED_DATA_DIR, SNAPSHOTS_DIR, MODELS_DIR, REPORTS_DIR,
    DEFAULT_COUNTRIES, DEFAULT_QUERIES, DEFAULT_PAGES_PER_QUERY,
    LOG_FORMAT, LOG_LEVEL, ensure_directories, validate_api_credentials
)

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates pipeline steps with idempotent execution."""
    
    def __init__(self, args):
        """Initialize pipeline runner with CLI arguments."""
        self.args = args
        self.run_date = args.run_date or datetime.now().strftime('%Y-%m-%d')
        self.completed_steps = []
        self.skipped_steps = []
        self.failed_steps = []
        
        # Ensure directories exist
        ensure_directories()
    
    def run_command(self, cmd: List[str], step_name: str) -> bool:
        """
        Run a command and track success/failure.
        
        Args:
            cmd: Command list to execute
            step_name: Name of the step for logging
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"▶ STEP: {step_name}")
        logger.info(f"{'='*60}")
        logger.info(f"Command: {' '.join(cmd)}\n")
        
        try:
            result = subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
            self.completed_steps.append(step_name)
            logger.info(f"✅ {step_name} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.failed_steps.append(step_name)
            logger.error(f"❌ {step_name} failed with code {e.returncode}")
            return False
    
    def should_run_step(self, output_path: Path, step_name: str) -> bool:
        """
        Check if a step should run based on output existence and --force flag.
        
        Args:
            output_path: Path to check for existence
            step_name: Name of the step
            
        Returns:
            True if step should run, False if should skip
        """
        if self.args.force:
            return True
        
        if output_path.exists():
            logger.info(f"⏭️  Skipping {step_name} (output exists: {output_path})")
            logger.info(f"   Use --force to rerun")
            self.skipped_steps.append(step_name)
            return False
        
        return True
    
    def step_fetch(self) -> bool:
        """Fetch data from Adzuna API."""
        if not validate_api_credentials():
            logger.error("❌ Adzuna API credentials not configured!")
            logger.error("   Please set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env file")
            return False
        
        # Check if data already exists for this run_date
        output_dir = PROJECT_ROOT / 'data' / 'raw' / 'adzuna' / self.run_date
        if not self.should_run_step(output_dir, "fetch"):
            return True
        
        cmd = [sys.executable, '-m', 'ingestion.fetch_adzuna']
        
        # Add optional arguments
        if self.args.countries:
            cmd.extend(['--countries'] + self.args.countries.split(','))
        if self.args.queries:
            cmd.extend(['--queries'] + self.args.queries.split(','))
        if self.args.pages:
            cmd.extend(['--pages', str(self.args.pages)])
        
        return self.run_command(cmd, "fetch")
    
    def step_label(self) -> bool:
        """Normalize and label jobs with roles and skills."""
        output_file = 'jobs_all_labeled_ml.parquet' if self.args.ml else 'jobs_all_labeled.parquet'
        output_path = CURATED_DATA_DIR / output_file
        
        if not self.should_run_step(output_path, "label"):
            return True
        
        cmd = [sys.executable, '-m', 'processing.label_all_jobs']
        
        if self.args.ml:
            cmd.append('--ml')
            # Try to use latest model if not specified
            try:
                from config import get_latest_model_dir
                latest_model = get_latest_model_dir('role_classifier')
                cmd.extend(['--model', str(latest_model)])
                logger.info(f"Using ML model: {latest_model}")
            except FileNotFoundError:
                logger.warning("No trained ML model found, will use default")
        
        success = self.run_command(cmd, "label")
        
        # Save snapshot after successful labeling
        if success and output_path.exists():
            self._save_snapshot(output_path)
        
        return success
    
    def _save_snapshot(self, curated_path: Path):
        """Save dated snapshot of curated data for historical tracking.
        
        Args:
            curated_path: Path to the current curated data file
        """
        import shutil
        
        # Create snapshot directory for this run_date
        snapshot_dir = SNAPSHOTS_DIR / self.run_date
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = snapshot_dir / curated_path.name
        
        try:
            shutil.copy2(curated_path, snapshot_path)
            logger.info(f"📸 Snapshot saved: {snapshot_path}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to save snapshot: {e}")
    
    def step_ghost_detection(self) -> bool:
        """Detect ghost jobs from historical snapshots."""
        # Check if we have snapshots
        if not SNAPSHOTS_DIR.exists() or not list(SNAPSHOTS_DIR.glob("*/*.parquet")):
            logger.warning("⚠️  No snapshots found, skipping ghost detection")
            logger.warning(f"   Snapshots directory: {SNAPSHOTS_DIR}")
            self.skipped_steps.append("ghost-detection")
            return True
        
        cmd = [
            sys.executable, '-m', 'analysis.repost_detector',
            '--run-date', self.run_date
        ]
        
        return self.run_command(cmd, "ghost-detection")
    
    def step_eda(self) -> bool:
        """Generate EDA report with visualizations."""
        output_dir = REPORTS_DIR / 'eda' / self.run_date
        output_file = output_dir / 'EDA_REPORT.md'
        
        if not self.should_run_step(output_file, "eda"):
            return True
        
        cmd = [
            sys.executable, '-m', 'analysis.eda_report',
            '--out', str(output_dir)
        ]
        
        return self.run_command(cmd, "eda")
    
    def step_insights(self) -> bool:
        """Generate market insights report."""
        # Check if market_insights.py exists
        insights_script = PROJECT_ROOT / 'analysis' / 'market_insights.py'
        if not insights_script.exists():
            logger.warning("⚠️  market_insights.py not found, skipping insights step")
            self.skipped_steps.append("insights")
            return True
        
        output_dir = REPORTS_DIR / 'insights' / self.run_date
        output_file = output_dir / 'INSIGHTS.md'
        
        if not self.should_run_step(output_file, "insights"):
            return True
        
        cmd = [
            sys.executable, '-m', 'analysis.market_insights',
            '--out', str(output_dir)
        ]
        
        return self.run_command(cmd, "insights")
    
    def step_salary(self) -> bool:
        """Train salary prediction model."""
        output_dir = MODELS_DIR / 'salary' / self.run_date
        output_file = output_dir / 'salary_model.joblib'
        
        if not self.should_run_step(output_file, "salary"):
            return True
        
        cmd = [
            sys.executable, '-m', 'analysis.salary_model',
            '--out', str(output_dir)
        ]
        
        return self.run_command(cmd, "salary")
    
    def step_train_role_model(self) -> bool:
        """Train ML role classifier."""
        output_dir = MODELS_DIR / 'role_classifier' / self.run_date
        output_file = output_dir / 'role_classifier.joblib'
        
        if not self.should_run_step(output_file, "train-role-model"):
            return True
        
        # Check if labeled data exists
        data_file = CURATED_DATA_DIR / 'jobs_all_labeled.parquet'
        if not data_file.exists():
            logger.error(f"❌ Labeled data not found: {data_file}")
            logger.error("   Run --label step first")
            return False
        
        cmd = [
            sys.executable, '-m', 'ml.role_classifier.train_classifier',
            '--data', str(data_file),
            '--out', str(output_dir)
        ]
        
        return self.run_command(cmd, "train-role-model")
    
    def run_pipeline(self):
        """Execute requested pipeline steps."""
        logger.info("="*60)
        logger.info("JOB MARKET INTELLIGENCE PIPELINE")
        logger.info("="*60)
        logger.info(f"Run Date: {self.run_date}")
        logger.info(f"Force Mode: {self.args.force}")
        logger.info(f"ML Mode: {self.args.ml}")
        logger.info("="*60)
        
        # Determine which steps to run
        steps = []
        
        if self.args.all:
            steps = ['fetch', 'label', 'eda', 'insights', 'salary', 'train_role_model']
            if self.args.ghost_detection:
                steps.append('ghost_detection')
        else:
            if self.args.fetch:
                steps.append('fetch')
            if self.args.label:
                steps.append('label')
            if self.args.eda:
                steps.append('eda')
            if self.args.insights:
                steps.append('insights')
            if self.args.salary:
                steps.append('salary')
            if self.args.train_role_model:
                steps.append('train_role_model')
            if self.args.ghost_detection:
                steps.append('ghost_detection')
        
        if not steps:
            logger.error("❌ No steps specified! Use --all or specific step flags.")
            logger.error("   Run with --help for usage information")
            sys.exit(1)
        
        logger.info(f"Steps to execute: {', '.join(steps)}")
        logger.info("="*60 + "\n")
        
        # Execute steps
        for step in steps:
            method = getattr(self, f'step_{step}')
            success = method()
            
            if not success and not self.args.continue_on_error:
                logger.error(f"\n❌ Pipeline stopped due to failure in step: {step}")
                self.print_summary()
                sys.exit(1)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print pipeline execution summary."""
        logger.info("\n" + "="*60)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*60)
        
        logger.info(f"\n✅ Completed Steps ({len(self.completed_steps)}):")
        for step in self.completed_steps:
            logger.info(f"   • {step}")
        
        if self.skipped_steps:
            logger.info(f"\n⏭️  Skipped Steps ({len(self.skipped_steps)}):")
            for step in self.skipped_steps:
                logger.info(f"   • {step}")
        
        if self.failed_steps:
            logger.info(f"\n❌ Failed Steps ({len(self.failed_steps)}):")
            for step in self.failed_steps:
                logger.info(f"   • {step}")
        
        # Output locations
        logger.info(f"\n📁 Output Locations:")
        logger.info(f"   • Raw Data: data/raw/adzuna/{self.run_date}/")
        logger.info(f"   • Curated Data: data/curated/")
        logger.info(f"   • Models: models/")
        logger.info(f"   • Reports: reports/")
        
        # Quick access paths
        logger.info(f"\n🔗 Quick Access:")
        
        curated_file = 'jobs_all_labeled_ml.parquet' if self.args.ml else 'jobs_all_labeled.parquet'
        curated_path = CURATED_DATA_DIR / curated_file
        if curated_path.exists():
            logger.info(f"   • Labeled Data: {curated_path}")
        
        eda_report = REPORTS_DIR / 'eda' / self.run_date / 'EDA_REPORT.md'
        if eda_report.exists():
            logger.info(f"   • EDA Report: {eda_report}")
        
        salary_model = MODELS_DIR / 'salary' / self.run_date / 'salary_model.joblib'
        if salary_model.exists():
            logger.info(f"   • Salary Model: {salary_model}")
        
        role_model = MODELS_DIR / 'role_classifier' / self.run_date / 'role_classifier.joblib'
        if role_model.exists():
            logger.info(f"   • Role Classifier: {role_model}")
        
        logger.info("\n" + "="*60)
        
        if not self.failed_steps:
            logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        else:
            logger.info("⚠️  PIPELINE COMPLETED WITH FAILURES")
        
        logger.info("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Job Market Intelligence Pipeline Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python orchestration/run_pipeline.py --all
  
  # Run with ghost job detection
  python orchestration/run_pipeline.py --all --ghost-detection
  
  # Run specific steps
  python orchestration/run_pipeline.py --fetch --label --eda
  
  # Use ML classifier
  python orchestration/run_pipeline.py --label --ml
  
  # Force rerun all steps
  python orchestration/run_pipeline.py --all --force
  
  # Custom data collection
  python orchestration/run_pipeline.py --fetch --countries de,gb,fr --pages 5
        """
    )
    
    # Pipeline steps
    parser.add_argument('--all', action='store_true', help='Run all pipeline steps')
    parser.add_argument('--fetch', action='store_true', help='Fetch data from Adzuna API')
    parser.add_argument('--label', action='store_true', help='Normalize and label jobs')
    parser.add_argument('--eda', action='store_true', help='Generate EDA report')
    parser.add_argument('--insights', action='store_true', help='Generate market insights')
    parser.add_argument('--salary', action='store_true', help='Train salary prediction model')
    parser.add_argument('--train-role-model', action='store_true', help='Train ML role classifier')
    parser.add_argument('--ghost-detection', action='store_true', help='Detect ghost jobs from historical snapshots')
    
    # Configuration
    parser.add_argument('--ml', action='store_true', help='Use ML classifier for role labeling')
    parser.add_argument('--run-date', type=str, help='Run date (YYYY-MM-DD), default: today')
    parser.add_argument('--force', action='store_true', help='Force rerun even if outputs exist')
    parser.add_argument('--continue-on-error', action='store_true', help='Continue pipeline on step failure')
    
    # Data collection options
    parser.add_argument('--countries', type=str, help='Comma-separated country codes (e.g., de,gb,fr)')
    parser.add_argument('--queries', type=str, help='Comma-separated search queries')
    parser.add_argument('--pages', type=int, help='Number of pages per query')
    
    args = parser.parse_args()
    
    # Run pipeline
    runner = PipelineRunner(args)
    runner.run_pipeline()


if __name__ == '__main__':
    main()
