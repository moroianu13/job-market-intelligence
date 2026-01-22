#!/usr/bin/env python3
"""
Showcase Demo Script

Generates a demo report with dataset statistics, role distribution,
top skills, salary coverage, and random job examples comparing
rule-based vs ML classification.
"""
import argparse
import logging
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd

from config import CURATED_DATA_DIR, REPORTS_DIR, LOG_FORMAT, LOG_LEVEL

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def load_datasets(rules_path: Path, ml_path: Path = None) -> tuple:
    """Load rule-based and optionally ML-based labeled datasets."""
    logger.info(f"Loading rule-based data from {rules_path}")
    df_rules = pd.read_parquet(rules_path)
    
    df_ml = None
    if ml_path and ml_path.exists():
        logger.info(f"Loading ML-based data from {ml_path}")
        df_ml = pd.read_parquet(ml_path)
    
    return df_rules, df_ml


def get_dataset_stats(df: pd.DataFrame) -> Dict:
    """Calculate dataset statistics."""
    stats = {
        'total_jobs': len(df),
        'countries': df['country'].nunique(),
        'companies': df['company'].nunique(),
        'date_range': f"{df['run_date'].min()} to {df['run_date'].max()}",
        'jobs_with_salary': df['salary_min'].notna().sum(),
        'salary_coverage_pct': 100 * df['salary_min'].notna().sum() / len(df),
        'jobs_with_skills': df['skills'].apply(lambda x: isinstance(x, (list, tuple)) and len(x) > 0).sum(),
        'skills_coverage_pct': 100 * df['skills'].apply(lambda x: isinstance(x, (list, tuple)) and len(x) > 0).sum() / len(df),
    }
    return stats


def get_role_distribution(df: pd.DataFrame) -> Dict:
    """Get role distribution statistics."""
    role_counts = df['roles'].explode().value_counts().to_dict()
    total_roles = sum(role_counts.values())
    
    role_dist = {}
    for role, count in role_counts.items():
        role_dist[role] = {
            'count': count,
            'percentage': 100 * count / total_roles
        }
    
    return role_dist


def get_top_skills(df: pd.DataFrame, top_n: int = 15) -> List[tuple]:
    """Get top N skills across all jobs."""
    all_skills = []
    for skills in df['skills']:
        if isinstance(skills, (list, tuple)) and len(skills) > 0:
            all_skills.extend(skills)
    
    skill_counts = Counter(all_skills)
    return skill_counts.most_common(top_n)


def get_random_job_examples(
    df_rules: pd.DataFrame,
    df_ml: pd.DataFrame = None,
    n: int = 10
) -> List[Dict]:
    """Get random job examples with classification results."""
    sample_indices = random.sample(range(len(df_rules)), min(n, len(df_rules)))
    
    examples = []
    for idx in sample_indices:
        job_rules = df_rules.iloc[idx]
        
        example = {
            'title': job_rules['title'],
            'country': job_rules['country'].upper(),
            'company': job_rules['company'] if pd.notna(job_rules['company']) else 'N/A',
            'roles_rule_based': list(job_rules['roles']) if isinstance(job_rules['roles'], (list, tuple)) else [],
            'skills': list(job_rules['skills']) if isinstance(job_rules['skills'], (list, tuple)) and len(job_rules['skills']) > 0 else ['No skills detected'],
            'salary': None
        }
        
        # Add salary if available
        if pd.notna(job_rules['salary_min']) and pd.notna(job_rules['salary_max']):
            salary_mid = (job_rules['salary_min'] + job_rules['salary_max']) / 2
            example['salary'] = f"€{salary_mid:,.0f}"
        
        # Add ML classification if available
        if df_ml is not None:
            job_ml = df_ml.iloc[idx]
            example['roles_ml_based'] = list(job_ml['roles']) if isinstance(job_ml['roles'], (list, tuple)) else []
        
        examples.append(example)
    
    return examples


def generate_markdown_report(
    stats: Dict,
    role_dist: Dict,
    top_skills: List[tuple],
    examples: List[Dict],
    output_path: Path,
    has_ml: bool = False
):
    """Generate markdown demo report."""
    logger.info(f"Generating demo report at {output_path}")
    
    lines = [
        "# Job Market Intelligence - Demo Report",
        f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n---\n",
        "## 📊 Dataset Statistics\n",
        f"- **Total Jobs**: {stats['total_jobs']:,}",
        f"- **Countries Covered**: {stats['countries']}",
        f"- **Unique Companies**: {stats['companies']:,}",
        f"- **Date Range**: {stats['date_range']}",
        f"- **Jobs with Salary Data**: {stats['jobs_with_salary']:,} ({stats['salary_coverage_pct']:.1f}%)",
        f"- **Jobs with Skills Data**: {stats['jobs_with_skills']:,} ({stats['skills_coverage_pct']:.1f}%)",
        "\n---\n",
        "## 🎯 Role Distribution\n",
    ]
    
    # Sort roles by count
    sorted_roles = sorted(role_dist.items(), key=lambda x: x[1]['count'], reverse=True)
    for role, info in sorted_roles:
        role_name = role.replace('_', ' ').title()
        lines.append(f"- **{role_name}**: {info['count']:,} jobs ({info['percentage']:.1f}%)")
    
    lines.extend([
        "\n---\n",
        f"## 🔧 Top {len(top_skills)} Skills\n",
    ])
    
    for skill, count in top_skills:
        lines.append(f"{count:4d} | {skill}")
    
    lines.extend([
        "\n---\n",
        "## 💼 Random Job Examples\n",
    ])
    
    for i, example in enumerate(examples, 1):
        lines.append(f"\n### Example {i}: {example['title']}\n")
        lines.append(f"**Country**: {example['country']}  ")
        lines.append(f"**Company**: {example['company']}  ")
        
        # Roles
        roles_rule = ", ".join([r.replace('_', ' ').title() for r in example['roles_rule_based']])
        lines.append(f"**Roles (Rule-based)**: {roles_rule}  ")
        
        if has_ml and 'roles_ml_based' in example:
            roles_ml = ", ".join([r.replace('_', ' ').title() for r in example['roles_ml_based']])
            lines.append(f"**Roles (ML-based)**: {roles_ml}  ")
            
            # Highlight differences
            set_rule = set(example['roles_rule_based'])
            set_ml = set(example['roles_ml_based'])
            if set_rule != set_ml:
                added = set_ml - set_rule
                removed = set_rule - set_ml
                if added:
                    lines.append(f"  ↳ *ML added*: {', '.join([r.replace('_', ' ').title() for r in added])}  ")
                if removed:
                    lines.append(f"  ↳ *ML removed*: {', '.join([r.replace('_', ' ').title() for r in removed])}  ")
        
        # Skills (limit to first 10)
        skills_str = ", ".join(example['skills'][:10])
        if len(example['skills']) > 10:
            skills_str += f", ... (+{len(example['skills']) - 10} more)"
        lines.append(f"**Skills**: {skills_str}  ")
        
        # Salary
        if example['salary']:
            lines.append(f"**Salary**: {example['salary']}  ")
    
    lines.extend([
        "\n---\n",
        "\n## 🚀 Quick Start\n",
        "\n**View full dataset**:",
        "```python",
        "import pandas as pd",
        "df = pd.read_parquet('data/curated/jobs_all_labeled.parquet')",
        "df.head()",
        "```",
        "\n**Explore with Streamlit**:",
        "```bash",
        "streamlit run app/streamlit_app.py",
        "```",
        "\n**Run full pipeline**:",
        "```bash",
        "python orchestration/run_pipeline.py --all",
        "```",
        "\n---\n",
        "\n*Generated by Job Market Intelligence Demo*\n",
    ])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Report saved to {output_path}")


def print_console_summary(stats: Dict, role_dist: Dict, top_skills: List[tuple]):
    """Print summary to console."""
    print("\n" + "="*60)
    print("JOB MARKET INTELLIGENCE - DEMO SHOWCASE")
    print("="*60)
    
    print("\n📊 DATASET STATS")
    print(f"  Total Jobs: {stats['total_jobs']:,}")
    print(f"  Countries: {stats['countries']}")
    print(f"  Salary Coverage: {stats['salary_coverage_pct']:.1f}%")
    print(f"  Skills Coverage: {stats['skills_coverage_pct']:.1f}%")
    
    print("\n🎯 TOP ROLES")
    sorted_roles = sorted(role_dist.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    for role, info in sorted_roles:
        role_name = role.replace('_', ' ').title()
        print(f"  {role_name}: {info['count']:,} ({info['percentage']:.1f}%)")
    
    print(f"\n🔧 TOP {min(10, len(top_skills))} SKILLS")
    for skill, count in top_skills[:10]:
        print(f"  {skill}: {count}")
    
    print("\n" + "="*60 + "\n")


def main():
    """Main demo pipeline."""
    parser = argparse.ArgumentParser(description='Generate demo report and showcase')
    parser.add_argument(
        '--data-rules',
        type=Path,
        default=CURATED_DATA_DIR / 'jobs_all_labeled.parquet',
        help='Path to rule-based labeled data'
    )
    parser.add_argument(
        '--data-ml',
        type=Path,
        default=CURATED_DATA_DIR / 'jobs_all_labeled_ml.parquet',
        help='Path to ML-based labeled data (optional)'
    )
    parser.add_argument(
        '--examples',
        type=int,
        default=10,
        help='Number of random job examples to include'
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=None,
        help='Output directory (default: reports/demo/<run_date>)'
    )
    
    args = parser.parse_args()
    
    # Setup output directory
    if args.out is None:
        run_date = datetime.now().strftime('%Y-%m-%d')
        output_dir = REPORTS_DIR / 'demo' / run_date
    else:
        output_dir = args.out
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df_rules, df_ml = load_datasets(args.data_rules, args.data_ml)
    has_ml = df_ml is not None
    
    # Calculate statistics
    logger.info("Calculating dataset statistics...")
    stats = get_dataset_stats(df_rules)
    role_dist = get_role_distribution(df_rules)
    top_skills = get_top_skills(df_rules, top_n=15)
    
    # Get random examples
    logger.info(f"Selecting {args.examples} random job examples...")
    examples = get_random_job_examples(df_rules, df_ml, n=args.examples)
    
    # Generate report
    report_path = output_dir / 'DEMO.md'
    generate_markdown_report(stats, role_dist, top_skills, examples, report_path, has_ml)
    
    # Print console summary
    print_console_summary(stats, role_dist, top_skills)
    
    logger.info("="*60)
    logger.info("Demo Report Complete!")
    logger.info("="*60)
    logger.info(f"Report location: {report_path}")
    logger.info(f"Random examples: {len(examples)} jobs")
    if has_ml:
        logger.info("ML comparison: Included")


if __name__ == '__main__':
    main()
