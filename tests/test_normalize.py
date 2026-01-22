"""Unit tests for data normalization."""
import json
import pytest
from pathlib import Path
from processing.normalize_all_adzuna import normalize_file


class TestNormalizeFile:
    """Test cases for normalize_file function."""
    
    def test_normalize_single_job(self, tmp_path):
        """Test normalization of a single job posting."""
        # Create test JSON file
        test_data = {
            "results": [
                {
                    "id": "123",
                    "title": "Data Scientist",
                    "description": "Test job",
                    "created": "2026-01-22T10:00:00Z",
                    "redirect_url": "https://example.com/job",
                    "company": {"display_name": "TestCorp"},
                    "category": {"label": "IT Jobs"},
                    "location": {"display_name": "Berlin"},
                    "salary_min": 50000,
                    "salary_max": 70000
                }
            ]
        }
        
        # Create proper directory structure
        test_file = tmp_path / "2026-01-22" / "de" / "data_scientist" / "page_1.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(test_data))
        
        # Normalize
        rows = normalize_file(test_file)
        
        # Assertions
        assert len(rows) == 1
        assert rows[0]["job_id"] == "123"
        assert rows[0]["title"] == "Data Scientist"
        assert rows[0]["run_date"] == "2026-01-22"
        assert rows[0]["country"] == "de"
        assert rows[0]["query"] == "data_scientist"
    
    def test_normalize_multiple_jobs(self, tmp_path):
        """Test normalization with multiple jobs."""
        test_data = {
            "results": [
                {"id": "1", "title": "Job 1", "description": "Desc 1"},
                {"id": "2", "title": "Job 2", "description": "Desc 2"},
                {"id": "3", "title": "Job 3", "description": "Desc 3"}
            ]
        }
        
        test_file = tmp_path / "2026-01-22" / "gb" / "data_engineer" / "page_1.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(test_data))
        
        rows = normalize_file(test_file)
        assert len(rows) == 3
    
    def test_normalize_empty_results(self, tmp_path):
        """Test handling of empty results."""
        test_data = {"results": []}
        
        test_file = tmp_path / "2026-01-22" / "pl" / "ml_engineer" / "page_1.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(test_data))
        
        rows = normalize_file(test_file)
        assert len(rows) == 0
    
    def test_normalize_missing_fields(self, tmp_path):
        """Test handling of missing optional fields."""
        test_data = {
            "results": [
                {
                    "id": "123",
                    "title": "Test Job",
                    # Missing description, company, etc.
                }
            ]
        }
        
        test_file = tmp_path / "2026-01-22" / "at" / "query" / "page_1.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(test_data))
        
        rows = normalize_file(test_file)
        assert len(rows) == 1
        assert rows[0]["description"] == ""
        assert rows[0]["company"] is None
