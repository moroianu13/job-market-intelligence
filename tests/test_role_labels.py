"""Unit tests for role classification."""
import pytest
from preprocessing.role_labels import assign_roles, ROLES


class TestAssignRoles:
    """Test cases for assign_roles function."""
    
    def test_data_scientist_role(self):
        """Test data scientist classification."""
        roles = assign_roles("Senior Data Scientist", "Build ML models with Python")
        assert "data_scientist" in roles
    
    def test_data_engineer_role(self):
        """Test data engineer classification."""
        roles = assign_roles("Data Engineer", "Build ETL pipelines with Spark")
        assert "data_engineer" in roles
    
    def test_ml_engineer_role(self):
        """Test ML engineer classification."""
        roles = assign_roles("ML Engineer", "Deploy machine learning models")
        assert "machine_learning_engineer" in roles
    
    def test_data_analyst_role(self):
        """Test data analyst classification."""
        roles = assign_roles("Data Analyst", "Create dashboards and reports")
        assert "data_analyst" in roles
    
    def test_cybersecurity_role(self):
        """Test cybersecurity classification."""
        roles = assign_roles("Security Engineer", "Protect infrastructure from threats")
        assert "cybersecurity_specialist" in roles
    
    def test_devops_role(self):
        """Test DevOps classification."""
        roles = assign_roles("DevOps Engineer", "Manage CI/CD pipelines")
        assert "devops_engineer" in roles
    
    def test_software_engineer_role(self):
        """Test software engineer classification."""
        roles = assign_roles("Full Stack Developer", "Build web applications")
        assert "software_engineer" in roles
    
    def test_other_role(self):
        """Test fallback to 'other' for unmatched jobs."""
        roles = assign_roles("Project Manager", "Manage projects and teams")
        assert roles == ["other"]
    
    def test_empty_title(self):
        """Test handling of empty title."""
        roles = assign_roles("", "Some description")
        assert roles == ["other"]
    
    def test_case_insensitive(self):
        """Test that matching is case-insensitive."""
        roles = assign_roles("DATA SCIENTIST", "MACHINE LEARNING")
        assert "data_scientist" in roles
    
    def test_multiple_roles(self):
        """Test job matching multiple role categories."""
        roles = assign_roles(
            "Data Scientist / ML Engineer",
            "Build and deploy machine learning models"
        )
        assert "data_scientist" in roles
        assert "machine_learning_engineer" in roles
    
    def test_returns_list(self):
        """Test that function always returns a list."""
        roles = assign_roles("Random Job", "Random description")
        assert isinstance(roles, list)
        assert len(roles) >= 1
