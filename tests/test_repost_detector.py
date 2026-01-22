"""Tests for ghost job detection functionality."""
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

import pandas as pd
import pytest

from analysis.repost_detector import (
    compute_repost_metrics,
    flag_ghost_jobs,
)


class TestComputeRepostMetrics:
    """Tests for repost metrics computation."""
    
    def test_basic_repost_metrics(self):
        """Should compute basic metrics correctly."""
        # Create synthetic history with multiple dates
        history = pd.DataFrame([
            {
                'job_fingerprint': 'fp1',
                'run_date': '2026-01-01',
                'country': 'de',
                'roles': 'data_scientist',
                'title': 'Data Scientist',
                'company': 'Tech Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/job1'
            },
            {
                'job_fingerprint': 'fp1',
                'run_date': '2026-01-10',
                'country': 'de',
                'roles': 'data_scientist',
                'title': 'Data Scientist',
                'company': 'Tech Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/job1'
            },
            {
                'job_fingerprint': 'fp1',
                'run_date': '2026-02-01',
                'country': 'de',
                'roles': 'data_scientist',
                'title': 'Data Scientist',
                'company': 'Tech Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/job1'
            },
        ])
        
        result = compute_repost_metrics(history)
        
        assert len(result) == 1
        assert result.iloc[0]['job_fingerprint'] == 'fp1'
        assert result.iloc[0]['first_seen'] == '2026-01-01'
        assert result.iloc[0]['last_seen'] == '2026-02-01'
        assert result.iloc[0]['days_seen'] == 3
        assert result.iloc[0]['repost_count'] == 3
        assert result.iloc[0]['active_span_days'] == 31
    
    def test_multiple_jobs(self):
        """Should handle multiple unique jobs."""
        history = pd.DataFrame([
            {
                'job_fingerprint': 'fp1',
                'run_date': '2026-01-01',
                'country': 'de',
                'roles': 'data_scientist',
                'title': 'Data Scientist',
                'company': 'Tech Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/job1'
            },
            {
                'job_fingerprint': 'fp2',
                'run_date': '2026-01-01',
                'country': 'gb',
                'roles': 'data_engineer',
                'title': 'Data Engineer',
                'company': 'Other Corp',
                'location': 'London',
                'redirect_url': 'https://example.com/job2'
            },
        ])
        
        result = compute_repost_metrics(history)
        
        assert len(result) == 2
        assert set(result['job_fingerprint']) == {'fp1', 'fp2'}
    
    def test_single_occurrence(self):
        """Should handle jobs seen only once."""
        history = pd.DataFrame([
            {
                'job_fingerprint': 'fp1',
                'run_date': '2026-01-01',
                'country': 'de',
                'roles': 'data_scientist',
                'title': 'Data Scientist',
                'company': 'Tech Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/job1'
            },
        ])
        
        result = compute_repost_metrics(history)
        
        assert len(result) == 1
        assert result.iloc[0]['days_seen'] == 1
        assert result.iloc[0]['repost_count'] == 1
        assert result.iloc[0]['active_span_days'] == 0


class TestFlagGhostJobs:
    """Tests for ghost job flagging."""
    
    def test_ghost_job_detection(self):
        """Should flag jobs meeting ghost criteria."""
        repost_df = pd.DataFrame([
            {
                'job_fingerprint': 'ghost1',
                'days_seen': 5,
                'active_span_days': 60,
                'repost_count': 5
            },
            {
                'job_fingerprint': 'real1',
                'days_seen': 1,
                'active_span_days': 0,
                'repost_count': 1
            },
            {
                'job_fingerprint': 'real2',
                'days_seen': 2,
                'active_span_days': 7,
                'repost_count': 2
            },
        ])
        
        result = flag_ghost_jobs(repost_df, min_days_seen=3, min_active_span_days=30)
        
        assert 'ghost_job' in result.columns
        assert result[result['job_fingerprint'] == 'ghost1']['ghost_job'].iloc[0] == True
        assert result[result['job_fingerprint'] == 'real1']['ghost_job'].iloc[0] == False
        assert result[result['job_fingerprint'] == 'real2']['ghost_job'].iloc[0] == False
    
    def test_threshold_boundaries(self):
        """Should respect threshold boundaries exactly."""
        repost_df = pd.DataFrame([
            {
                'job_fingerprint': 'edge1',
                'days_seen': 3,  # Exactly at threshold
                'active_span_days': 30,  # Exactly at threshold
                'repost_count': 3
            },
            {
                'job_fingerprint': 'edge2',
                'days_seen': 2,  # Below threshold
                'active_span_days': 30,
                'repost_count': 2
            },
            {
                'job_fingerprint': 'edge3',
                'days_seen': 3,
                'active_span_days': 29,  # Below threshold
                'repost_count': 3
            },
        ])
        
        result = flag_ghost_jobs(repost_df, min_days_seen=3, min_active_span_days=30)
        
        # edge1 should be flagged (meets both thresholds)
        assert result[result['job_fingerprint'] == 'edge1']['ghost_job'].iloc[0] == True
        # edge2 should not be flagged (days_seen below threshold)
        assert result[result['job_fingerprint'] == 'edge2']['ghost_job'].iloc[0] == False
        # edge3 should not be flagged (active_span below threshold)
        assert result[result['job_fingerprint'] == 'edge3']['ghost_job'].iloc[0] == False
    
    def test_custom_thresholds(self):
        """Should support custom threshold values."""
        repost_df = pd.DataFrame([
            {
                'job_fingerprint': 'job1',
                'days_seen': 5,
                'active_span_days': 60,
                'repost_count': 5
            },
        ])
        
        # Strict thresholds - should flag
        result1 = flag_ghost_jobs(repost_df, min_days_seen=3, min_active_span_days=30)
        assert result1['ghost_job'].iloc[0] == True
        
        # Very strict thresholds - should not flag
        result2 = flag_ghost_jobs(repost_df, min_days_seen=10, min_active_span_days=90)
        assert result2['ghost_job'].iloc[0] == False
    
    def test_empty_dataframe(self):
        """Should handle empty DataFrame gracefully."""
        repost_df = pd.DataFrame(columns=[
            'job_fingerprint', 'days_seen', 'active_span_days', 'repost_count'
        ])
        
        result = flag_ghost_jobs(repost_df)
        
        assert 'ghost_job' in result.columns
        assert len(result) == 0


class TestEndToEndGhostDetection:
    """Integration tests for complete ghost detection workflow."""
    
    def test_full_workflow(self):
        """Should detect ghost jobs from raw history."""
        # Simulate 3 months of data collection
        history = []
        
        # Ghost job: appears frequently over long period
        for i in range(10):
            date = (datetime(2026, 1, 1) + timedelta(days=i*10)).strftime('%Y-%m-%d')
            history.append({
                'job_fingerprint': 'ghost_job',
                'run_date': date,
                'country': 'de',
                'roles': 'data_scientist',
                'title': 'Data Scientist',
                'company': 'Ghost Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/ghost'
            })
        
        # Real job: appears briefly
        for i in range(2):
            date = (datetime(2026, 1, 1) + timedelta(days=i*3)).strftime('%Y-%m-%d')
            history.append({
                'job_fingerprint': 'real_job',
                'run_date': date,
                'country': 'gb',
                'roles': 'data_engineer',
                'title': 'Data Engineer',
                'company': 'Real Corp',
                'location': 'London',
                'redirect_url': 'https://example.com/real'
            })
        
        history_df = pd.DataFrame(history)
        
        # Compute metrics
        metrics = compute_repost_metrics(history_df)
        
        # Flag ghost jobs
        result = flag_ghost_jobs(metrics, min_days_seen=3, min_active_span_days=30)
        
        # Verify results
        ghost_jobs = result[result['ghost_job'] == True]
        real_jobs = result[result['ghost_job'] == False]
        
        assert len(ghost_jobs) == 1
        assert ghost_jobs.iloc[0]['job_fingerprint'] == 'ghost_job'
        assert ghost_jobs.iloc[0]['days_seen'] == 10
        assert ghost_jobs.iloc[0]['active_span_days'] >= 90
        
        assert len(real_jobs) == 1
        assert real_jobs.iloc[0]['job_fingerprint'] == 'real_job'
        assert real_jobs.iloc[0]['days_seen'] == 2
