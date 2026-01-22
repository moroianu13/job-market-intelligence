"""Tests for job fingerprinting functionality."""
import pandas as pd
import pytest

from processing.fingerprints import (
    normalize_text,
    extract_domain,
    make_fingerprint,
    add_fingerprints
)


class TestNormalizeText:
    """Tests for text normalization."""
    
    def test_lowercase_conversion(self):
        """Text should be converted to lowercase."""
        assert normalize_text("DATA SCIENTIST") == "data scientist"
        assert normalize_text("Senior Engineer") == "senior engineer"
    
    def test_whitespace_normalization(self):
        """Multiple whitespace should be normalized to single space."""
        assert normalize_text("Data    Scientist") == "data scientist"
        assert normalize_text("Data\nScientist") == "data scientist"
        assert normalize_text("Data\t\tScientist") == "data scientist"
    
    def test_leading_trailing_whitespace(self):
        """Leading and trailing whitespace should be stripped."""
        assert normalize_text("  Data Scientist  ") == "data scientist"
        assert normalize_text("\nData Scientist\n") == "data scientist"
    
    def test_empty_input(self):
        """Empty or None input should return empty string."""
        assert normalize_text(None) == ""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""
    
    def test_idempotency(self):
        """Normalizing twice should give same result."""
        text = "  Data   SCIENTIST  "
        normalized = normalize_text(text)
        assert normalize_text(normalized) == normalized


class TestExtractDomain:
    """Tests for domain extraction from URLs."""
    
    def test_simple_url(self):
        """Should extract domain from simple URL."""
        assert extract_domain("https://example.com/jobs/123") == "example.com"
        assert extract_domain("http://jobs.example.com/apply") == "jobs.example.com"
    
    def test_url_with_query_params(self):
        """Should ignore query parameters."""
        url = "https://example.com/jobs/123?ref=abc&source=linkedin"
        assert extract_domain(url) == "example.com"
    
    def test_url_with_fragment(self):
        """Should ignore URL fragments."""
        url = "https://example.com/jobs/123#apply"
        assert extract_domain(url) == "example.com"
    
    def test_case_normalization(self):
        """Domain should be lowercase."""
        assert extract_domain("https://EXAMPLE.COM/jobs") == "example.com"
        assert extract_domain("https://Example.Com/jobs") == "example.com"
    
    def test_empty_input(self):
        """Empty or None input should return empty string."""
        assert extract_domain(None) == ""
        assert extract_domain("") == ""
    
    def test_invalid_url(self):
        """Invalid URLs should return empty string."""
        assert extract_domain("not a url") == ""


class TestMakeFingerprint:
    """Tests for fingerprint generation."""
    
    def test_fingerprint_stability(self):
        """Same input should always produce same fingerprint."""
        row = pd.Series({
            'title': 'Data Scientist',
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        fp1 = make_fingerprint(row)
        fp2 = make_fingerprint(row)
        
        assert fp1 == fp2
        assert len(fp1) == 40  # SHA1 hex digest length
    
    def test_fingerprint_case_insensitivity(self):
        """Case variations should produce same fingerprint."""
        row1 = pd.Series({
            'title': 'Data Scientist',
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        row2 = pd.Series({
            'title': 'DATA SCIENTIST',
            'company': 'TECH CORP',
            'location': 'BERLIN',
            'redirect_url': 'https://EXAMPLE.COM/jobs/123'
        })
        
        assert make_fingerprint(row1) == make_fingerprint(row2)
    
    def test_fingerprint_whitespace_insensitivity(self):
        """Whitespace variations should produce same fingerprint."""
        row1 = pd.Series({
            'title': 'Data Scientist',
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        row2 = pd.Series({
            'title': '  Data   Scientist  ',
            'company': 'Tech  Corp',
            'location': '  Berlin  ',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        assert make_fingerprint(row1) == make_fingerprint(row2)
    
    def test_fingerprint_url_param_insensitivity(self):
        """URL query parameters should not affect fingerprint."""
        row1 = pd.Series({
            'title': 'Data Scientist',
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        row2 = pd.Series({
            'title': 'Data Scientist',
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123?ref=abc&utm_source=linkedin'
        })
        
        assert make_fingerprint(row1) == make_fingerprint(row2)
    
    def test_fingerprint_sensitivity(self):
        """Different jobs should produce different fingerprints."""
        row1 = pd.Series({
            'title': 'Data Scientist',
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        row2 = pd.Series({
            'title': 'Data Engineer',  # Different title
            'company': 'Tech Corp',
            'location': 'Berlin',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        assert make_fingerprint(row1) != make_fingerprint(row2)
    
    def test_missing_fields(self):
        """Should handle missing fields gracefully."""
        row = pd.Series({
            'title': 'Data Scientist',
            'company': None,
            'location': '',
            'redirect_url': 'https://example.com/jobs/123'
        })
        
        fp = make_fingerprint(row)
        assert len(fp) == 40


class TestAddFingerprints:
    """Tests for batch fingerprint addition."""
    
    def test_add_fingerprints_to_dataframe(self):
        """Should add job_fingerprint column to DataFrame."""
        df = pd.DataFrame([
            {
                'title': 'Data Scientist',
                'company': 'Tech Corp',
                'location': 'Berlin',
                'redirect_url': 'https://example.com/jobs/123'
            },
            {
                'title': 'Data Engineer',
                'company': 'Tech Corp',
                'location': 'Munich',
                'redirect_url': 'https://example.com/jobs/456'
            }
        ])
        
        result = add_fingerprints(df)
        
        assert 'job_fingerprint' in result.columns
        assert len(result) == 2
        assert all(len(fp) == 40 for fp in result['job_fingerprint'])
        assert result['job_fingerprint'][0] != result['job_fingerprint'][1]
    
    def test_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=['title', 'company', 'location', 'redirect_url'])
        result = add_fingerprints(df)
        
        assert 'job_fingerprint' in result.columns
        assert len(result) == 0
