"""Salary data quality validation and flagging.

Performs sanity checks on salary data including:
- Outlier detection using IQR method per country
- Low sample size flagging
- Missing data detection
- Annual EUR conversion (where possible)
- Debug export for outliers

Author: Job Market Intelligence Team
"""
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Salary validation thresholds
MIN_SAMPLE_SIZE = 10  # Minimum samples per country for robust statistics
MIN_REASONABLE_SALARY = 10_000  # €10k/year (likely missing data or hourly rate)
MAX_REASONABLE_SALARY = 500_000  # €500k/year (likely B2B/contractor rate or data error)
B2B_THRESHOLD = 250_000  # Above this is likely B2B/contractor daily rate
IQR_MULTIPLIER = 3.0  # Outlier detection: Q1 - 3*IQR or Q3 + 3*IQR


def detect_outliers_iqr(series: pd.Series, multiplier: float = IQR_MULTIPLIER) -> pd.Series:
    """
    Detect outliers using Interquartile Range (IQR) method.
    
    Args:
        series: Pandas Series with numeric values
        multiplier: IQR multiplier for outlier bounds (default: 3.0)
        
    Returns:
        Boolean Series indicating outliers (True = outlier)
    """
    if len(series) < 4:
        # Not enough data for IQR
        return pd.Series([False] * len(series), index=series.index)
    
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    return (series < lower_bound) | (series > upper_bound)


def estimate_annual_salary(row: pd.Series) -> tuple[float, float, str]:
    """
    Estimate annual salary in EUR from min/max salary fields.
    
    Handles common issues:
    - Missing salary data
    - Hourly rates (< €50/hour → assume full-time)
    - Daily rates (< €1000/day → assume contractor)
    - Unreasonable values
    
    Args:
        row: DataFrame row with salary_min, salary_max columns
        
    Returns:
        Tuple of (annual_min, annual_max, note)
    """
    sal_min = row.get('salary_min')
    sal_max = row.get('salary_max')
    
    # Missing data
    if pd.isna(sal_min) or pd.isna(sal_max):
        return np.nan, np.nan, "missing"
    
    sal_min = float(sal_min)
    sal_max = float(sal_max)
    
    # Detect hourly rate (likely < €50/hour)
    if sal_max < 50:
        # Assume full-time: 40h/week * 52 weeks = 2080 hours/year
        sal_min = sal_min * 2080
        sal_max = sal_max * 2080
        note = "converted_hourly"
    
    # Detect daily rate (likely €200-€1000/day)
    elif 200 <= sal_max <= 1000:
        # Assume 220 working days/year
        sal_min = sal_min * 220
        sal_max = sal_max * 220
        note = "converted_daily"
    
    # Detect monthly rate (likely €2000-€15000/month)
    elif 2000 <= sal_max <= 15000:
        sal_min = sal_min * 12
        sal_max = sal_max * 12
        note = "converted_monthly"
    
    # Already annual or unclear
    else:
        note = "ok"
    
    return sal_min, sal_max, note


def flag_salary_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add salary quality flags to DataFrame.
    
    Adds columns:
    - salary_flag: Quality flag (ok, missing, low_sample, outlier, possible_b2b, unknown_period)
    - salary_note: Additional context (e.g., "converted_hourly")
    
    Args:
        df: DataFrame with salary_min, salary_max, country columns
        
    Returns:
        DataFrame with added salary_flag and salary_note columns
    """
    df = df.copy()
    
    # Initialize new columns
    df['salary_flag'] = 'unknown'
    df['salary_note'] = ''
    
    # Step 1: Flag missing salaries
    missing_mask = df['salary_min'].isna() | df['salary_max'].isna()
    df.loc[missing_mask, 'salary_flag'] = 'missing'
    logger.info(f"Missing salary data: {missing_mask.sum():,} records")
    
    # Step 2: Calculate midpoint for valid salaries
    valid_mask = ~missing_mask
    df.loc[valid_mask, 'salary_mid'] = (df.loc[valid_mask, 'salary_min'] + df.loc[valid_mask, 'salary_max']) / 2
    
    # Step 3: Flag unreasonable values (before IQR)
    if valid_mask.any():
        # Extremely low (likely hourly/daily rates not converted)
        low_mask = valid_mask & (df['salary_max'] < MIN_REASONABLE_SALARY)
        df.loc[low_mask, 'salary_flag'] = 'unknown_period'
        df.loc[low_mask, 'salary_note'] = f'max < €{MIN_REASONABLE_SALARY:,}'
        logger.info(f"Unknown period/low values: {low_mask.sum():,} records")
        
        # Extremely high (likely B2B rates)
        b2b_mask = valid_mask & (df['salary_min'] > B2B_THRESHOLD)
        df.loc[b2b_mask, 'salary_flag'] = 'possible_b2b'
        df.loc[b2b_mask, 'salary_note'] = f'min > €{B2B_THRESHOLD:,}'
        logger.info(f"Possible B2B/contractor rates: {b2b_mask.sum():,} records")
    
    # Step 4: Per-country outlier detection
    outliers_by_country = []
    
    for country in df['country'].unique():
        country_mask = (df['country'] == country) & valid_mask & (df['salary_flag'] == 'unknown')
        country_salaries = df.loc[country_mask, 'salary_mid']
        
        if len(country_salaries) < MIN_SAMPLE_SIZE:
            # Not enough samples for robust stats
            df.loc[country_mask, 'salary_flag'] = 'low_sample'
            df.loc[country_mask, 'salary_note'] = f'n={len(country_salaries)}'
            logger.debug(f"{country.upper()}: Low sample size (n={len(country_salaries)})")
            continue
        
        # Detect outliers using IQR
        is_outlier = detect_outliers_iqr(country_salaries)
        outlier_indices = country_salaries[is_outlier].index
        
        if len(outlier_indices) > 0:
            df.loc[outlier_indices, 'salary_flag'] = 'outlier'
            
            # Add percentile info to note
            for idx in outlier_indices:
                salary = df.loc[idx, 'salary_mid']
                percentile = (country_salaries < salary).sum() / len(country_salaries) * 100
                df.loc[idx, 'salary_note'] = f'p{percentile:.0f} in {country.upper()}'
            
            outliers_by_country.append({
                'country': country,
                'total': len(country_salaries),
                'outliers': len(outlier_indices),
                'pct': 100 * len(outlier_indices) / len(country_salaries)
            })
            
            logger.info(f"{country.upper()}: {len(outlier_indices)} outliers out of {len(country_salaries)} ({100*len(outlier_indices)/len(country_salaries):.1f}%)")
    
    # Step 5: Mark remaining valid salaries as OK
    ok_mask = valid_mask & (df['salary_flag'] == 'unknown')
    df.loc[ok_mask, 'salary_flag'] = 'ok'
    logger.info(f"Clean salary data: {ok_mask.sum():,} records")
    
    # Summary statistics
    flag_counts = df['salary_flag'].value_counts()
    logger.info("\nSalary Flag Summary:")
    for flag, count in flag_counts.items():
        pct = 100 * count / len(df)
        logger.info(f"  {flag:>15}: {count:>6,} ({pct:>5.1f}%)")
    
    return df


def export_salary_debug_report(df: pd.DataFrame, run_date: str = None) -> Path:
    """
    Export salary outliers and flagged data for manual review.
    
    Creates CSV report with:
    - All records with salary_flag != 'ok'
    - Sorted by country, then salary_flag
    
    Args:
        df: DataFrame with salary validation flags
        run_date: Optional run date (YYYY-MM-DD), defaults to today
        
    Returns:
        Path to exported CSV file
    """
    if run_date is None:
        run_date = datetime.now().strftime('%Y-%m-%d')
    
    # Create output directory
    output_dir = Path(f"reports/data_quality/{run_date}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter to flagged records
    flagged = df[df['salary_flag'] != 'ok'].copy()
    
    if len(flagged) == 0:
        logger.info("No salary issues found - skipping debug report")
        return None
    
    # Select relevant columns
    export_cols = [
        'country', 'salary_flag', 'salary_note',
        'salary_min', 'salary_max', 'salary_mid',
        'title', 'company', 'job_id'
    ]
    
    # Only include columns that exist
    export_cols = [col for col in export_cols if col in flagged.columns]
    
    flagged_export = flagged[export_cols].sort_values(['country', 'salary_flag'])
    
    # Export
    output_path = output_dir / 'salary_outliers.csv'
    flagged_export.to_csv(output_path, index=False)
    
    logger.info(f"\n✓ Exported {len(flagged):,} flagged records to:")
    logger.info(f"  {output_path}")
    
    # Summary by country and flag
    summary = flagged.groupby(['country', 'salary_flag']).size().reset_index(name='count')
    summary_path = output_dir / 'salary_summary.csv'
    summary.to_csv(summary_path, index=False)
    logger.info(f"  {summary_path}")
    
    return output_path


def get_clean_salary_data(df: pd.DataFrame, 
                          min_country_samples: int = MIN_SAMPLE_SIZE) -> pd.DataFrame:
    """
    Filter DataFrame to only clean salary records.
    
    Returns records where:
    - salary_flag == 'ok'
    - Country has >= min_country_samples clean records
    
    Args:
        df: DataFrame with salary_flag column
        min_country_samples: Minimum records per country (default: 10)
        
    Returns:
        Filtered DataFrame with clean salary data
    """
    if 'salary_flag' not in df.columns:
        logger.warning("salary_flag column not found - returning all records")
        return df
    
    # Filter to OK records
    clean = df[df['salary_flag'] == 'ok'].copy()
    
    # Count by country
    country_counts = clean['country'].value_counts()
    valid_countries = country_counts[country_counts >= min_country_samples].index
    
    # Filter to countries with enough samples
    clean = clean[clean['country'].isin(valid_countries)]
    
    excluded_countries = len(country_counts) - len(valid_countries)
    excluded_records = len(df[df['salary_flag'] == 'ok']) - len(clean)
    
    logger.info(f"\nClean salary filter:")
    logger.info(f"  Valid countries: {len(valid_countries)} (excluded {excluded_countries} with n < {min_country_samples})")
    logger.info(f"  Valid records: {len(clean):,} (excluded {excluded_records:,})")
    
    return clean


if __name__ == '__main__':
    """
    Test salary validation on sample data.
    """
    logger.info("Testing salary validation module...")
    
    # Create sample data
    test_data = pd.DataFrame({
        'country': ['de', 'de', 'de', 'de', 'de', 'pl', 'pl', 'pl', 'gb', 'gb'],
        'salary_min': [50000, 60000, 55000, 150000, np.nan, 30000, 35000, 200000, 40000, 45000],
        'salary_max': [70000, 80000, 75000, 180000, np.nan, 40000, 45000, 250000, 50000, 55000],
        'title': ['Data Scientist'] * 10,
        'company': ['Test Corp'] * 10,
        'job_id': range(1, 11)
    })
    
    logger.info(f"\nOriginal data:\n{test_data}")
    
    # Apply validation
    test_data = flag_salary_quality(test_data)
    
    logger.info(f"\nFlagged data:\n{test_data[['country', 'salary_min', 'salary_max', 'salary_flag', 'salary_note']]}")
    
    # Export debug report
    export_salary_debug_report(test_data, run_date='test')
    
    # Get clean data
    clean = get_clean_salary_data(test_data)
    logger.info(f"\nClean data ({len(clean)} records):\n{clean[['country', 'salary_min', 'salary_max']]}")
