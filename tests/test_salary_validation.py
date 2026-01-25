"""
Unit tests for salary validation module.
"""
import pytest
import pandas as pd
import numpy as np
from processing.salary_validation import (
    detect_outliers_iqr,
    flag_salary_quality,
    get_clean_salary_data,
    MIN_SAMPLE_SIZE
)


def test_detect_outliers_iqr():
    """Test IQR outlier detection."""
    # Normal distribution
    data = pd.Series([10, 12, 15, 18, 20, 22, 25, 28, 30])
    outliers = detect_outliers_iqr(data, multiplier=1.5)
    assert outliers.sum() == 0, "No outliers expected in normal data"
    
    # With outliers
    data_with_outliers = pd.Series([10, 12, 15, 18, 20, 22, 25, 28, 30, 100, 200])
    outliers = detect_outliers_iqr(data_with_outliers, multiplier=1.5)
    assert outliers.sum() > 0, "Should detect outliers"
    
    # Small sample (< 4 values)
    small_data = pd.Series([10, 20, 30])
    outliers = detect_outliers_iqr(small_data)
    assert outliers.sum() == 0, "Should not flag outliers for small samples"


def test_flag_salary_quality_missing():
    """Test flagging of missing salary data."""
    df = pd.DataFrame({
        'country': ['de', 'de', 'de'],
        'salary_min': [50000, np.nan, 60000],
        'salary_max': [70000, 80000, np.nan],
        'title': ['Job A', 'Job B', 'Job C'],
        'company': ['Corp A', 'Corp B', 'Corp C'],
        'job_id': [1, 2, 3]
    })
    
    result = flag_salary_quality(df)
    
    assert 'salary_flag' in result.columns
    assert result.loc[1, 'salary_flag'] == 'missing'
    assert result.loc[2, 'salary_flag'] == 'missing'


def test_flag_salary_quality_low_sample():
    """Test flagging of countries with low sample size."""
    df = pd.DataFrame({
        'country': ['de'] * 15 + ['ro'] * 3,  # DE: 15 samples, RO: 3 samples
        'salary_min': [50000] * 15 + [30000] * 3,
        'salary_max': [70000] * 15 + [40000] * 3,
        'title': ['Job'] * 18,
        'company': ['Corp'] * 18,
        'job_id': range(1, 19)
    })
    
    result = flag_salary_quality(df)
    
    # Romania should be flagged as low_sample
    ro_flags = result[result['country'] == 'ro']['salary_flag'].unique()
    assert 'low_sample' in ro_flags


def test_flag_salary_quality_outliers():
    """Test outlier detection within country."""
    df = pd.DataFrame({
        'country': ['de'] * 20,
        'salary_min': [50000] * 19 + [300000],  # One extreme outlier
        'salary_max': [70000] * 19 + [350000],
        'title': ['Job'] * 20,
        'company': ['Corp'] * 20,
        'job_id': range(1, 21)
    })
    
    result = flag_salary_quality(df)
    
    # Last record should be flagged (either outlier or possible_b2b)
    assert result.iloc[-1]['salary_flag'] in ['outlier', 'possible_b2b']


def test_flag_salary_quality_b2b():
    """Test detection of possible B2B/contractor rates."""
    df = pd.DataFrame({
        'country': ['de', 'de', 'de'],
        'salary_min': [50000, 60000, 300000],  # Third is likely B2B
        'salary_max': [70000, 80000, 350000],
        'title': ['Job A', 'Job B', 'Job C'],
        'company': ['Corp A', 'Corp B', 'Corp C'],
        'job_id': [1, 2, 3]
    })
    
    result = flag_salary_quality(df)
    
    assert result.loc[2, 'salary_flag'] == 'possible_b2b'


def test_get_clean_salary_data():
    """Test filtering to clean salary records."""
    df = pd.DataFrame({
        'country': ['de'] * 15 + ['ro'] * 3 + ['pl'] * 2,
        'salary_min': [50000] * 20,
        'salary_max': [70000] * 20,
        'title': ['Job'] * 20,
        'company': ['Corp'] * 20,
        'job_id': range(1, 21)
    })
    
    # Apply validation
    df = flag_salary_quality(df)
    
    # Manually set some as 'ok' for DE (enough samples)
    df.loc[df['country'] == 'de', 'salary_flag'] = 'ok'
    
    # Get clean data
    clean = get_clean_salary_data(df, min_country_samples=MIN_SAMPLE_SIZE)
    
    # Should only include DE (15 samples >= 10)
    assert set(clean['country'].unique()) == {'de'}
    assert len(clean) == 15


def test_salary_mid_calculation():
    """Test that salary_mid is correctly calculated."""
    df = pd.DataFrame({
        'country': ['de', 'de'],
        'salary_min': [40000, 60000],
        'salary_max': [60000, 80000],
        'title': ['Job A', 'Job B'],
        'company': ['Corp A', 'Corp B'],
        'job_id': [1, 2]
    })
    
    result = flag_salary_quality(df)
    
    assert 'salary_mid' in result.columns
    assert result.loc[0, 'salary_mid'] == 50000
    assert result.loc[1, 'salary_mid'] == 70000


def test_unknown_period():
    """Test detection of unknown time periods (very low salaries)."""
    df = pd.DataFrame({
        'country': ['de', 'de', 'de'],
        'salary_min': [50000, 60000, 5000],  # Third is suspiciously low
        'salary_max': [70000, 80000, 8000],
        'title': ['Job A', 'Job B', 'Job C'],
        'company': ['Corp A', 'Corp B', 'Corp C'],
        'job_id': [1, 2, 3]
    })
    
    result = flag_salary_quality(df)
    
    assert result.loc[2, 'salary_flag'] == 'unknown_period'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
