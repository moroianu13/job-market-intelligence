"""Tests for ML role classifier."""
import pytest
import pandas as pd
from pathlib import Path
from ml.role_classifier import RolePredictor


@pytest.fixture
def sample_jobs():
    """Sample job data for testing."""
    return pd.DataFrame({
        'title': [
            'Senior Data Scientist',
            'Machine Learning Engineer - AI/ML',
            'Data Engineer - AWS',
            'Junior Data Analyst',
            'DevOps Engineer',
            'Software Developer',
            'Cybersecurity Specialist',
            'Product Manager'
        ],
        'description': [
            'Build ML models with Python, scikit-learn, and TensorFlow',
            'Deploy deep learning models, MLOps, Kubernetes',
            'Build ETL pipelines with Spark, AWS Glue, Airflow',
            'Create dashboards with Tableau, SQL queries',
            'Automate infrastructure with Terraform, Docker, Kubernetes',
            'Full-stack development with React and Node.js',
            'Network security, penetration testing, threat detection',
            'Define product roadmap, work with stakeholders'
        ]
    })


def test_predictor_initialization():
    """Test that predictor can be initialized with trained model."""
    model_dir = Path('models/role_classifier/2026-01-22')
    
    if not model_dir.exists():
        pytest.skip(f"Model not found at {model_dir}")
    
    predictor = RolePredictor(model_dir)
    assert predictor.model is not None
    assert predictor.vectorizer is not None


def test_predictor_single_label():
    """Test prediction for single job."""
    model_dir = Path('models/role_classifier/2026-01-22')
    
    if not model_dir.exists():
        pytest.skip(f"Model not found at {model_dir}")
    
    predictor = RolePredictor(model_dir)
    
    # Test data scientist
    roles = predictor.predict_roles(
        title="Senior Data Scientist",
        description="Build ML models with Python, scikit-learn"
    )
    assert 'data_scientist' in roles
    
    # Test data engineer
    roles = predictor.predict_roles(
        title="Data Engineer",
        description="Build ETL pipelines with Spark and Airflow"
    )
    assert 'data_engineer' in roles


def test_predictor_batch(sample_jobs):
    """Test batch prediction."""
    model_dir = Path('models/role_classifier/2026-01-22')
    
    if not model_dir.exists():
        pytest.skip(f"Model not found at {model_dir}")
    
    predictor = RolePredictor(model_dir)
    df_result = predictor.predict_batch(sample_jobs)
    
    # Check that roles column was added
    assert 'roles' in df_result.columns
    
    # Check that all jobs have at least one role
    assert all(len(roles) > 0 for roles in df_result['roles'])
    
    # Check expected roles for specific jobs
    assert 'data_scientist' in df_result.iloc[0]['roles']
    assert 'machine_learning_engineer' in df_result.iloc[1]['roles']
    assert 'data_engineer' in df_result.iloc[2]['roles']
    assert 'data_analyst' in df_result.iloc[3]['roles']


def test_predictor_multi_label():
    """Test that predictor can assign multiple labels."""
    model_dir = Path('models/role_classifier/2026-01-22')
    
    if not model_dir.exists():
        pytest.skip(f"Model not found at {model_dir}")
    
    predictor = RolePredictor(model_dir)
    
    # Job that should get multiple labels
    roles = predictor.predict_roles(
        title="Data Scientist / ML Engineer",
        description="Build and deploy ML models, deep learning, MLOps, Python, TensorFlow"
    )
    
    # Should have at least one role, possibly multiple
    assert len(roles) >= 1
    
    # Likely to contain data_scientist or machine_learning_engineer
    assert ('data_scientist' in roles) or ('machine_learning_engineer' in roles)


def test_predictor_threshold():
    """Test that threshold parameter affects predictions."""
    model_dir = Path('models/role_classifier/2026-01-22')
    
    if not model_dir.exists():
        pytest.skip(f"Model not found at {model_dir}")
    
    predictor = RolePredictor(model_dir)
    
    title = "Data Scientist"
    description = "Machine learning, Python, statistics"
    
    # Lower threshold should give more labels
    roles_low = predictor.predict_roles(title, description, threshold=0.3)
    roles_high = predictor.predict_roles(title, description, threshold=0.7)
    
    # Either high threshold gives fewer labels, or they're the same
    assert len(roles_high) <= len(roles_low)


def test_predictor_empty_input():
    """Test predictor with empty input."""
    model_dir = Path('models/role_classifier/2026-01-22')
    
    if not model_dir.exists():
        pytest.skip(f"Model not found at {model_dir}")
    
    predictor = RolePredictor(model_dir)
    
    roles = predictor.predict_roles(title="", description="")
    
    # Should return at least 'other'
    assert len(roles) > 0
    assert 'other' in roles


def test_role_categories_match():
    """Test that role categories match across modules."""
    from ml.role_classifier.train_classifier import ROLE_CATEGORIES as TRAIN_CATEGORIES
    from ml.role_classifier.predict_classifier import ROLE_CATEGORIES as PREDICT_CATEGORIES
    from preprocessing.role_labels import ROLE_KEYWORDS
    
    # Categories should match between train and predict
    assert TRAIN_CATEGORIES == PREDICT_CATEGORIES
    
    # All categories should have keywords defined (except 'other')
    for category in TRAIN_CATEGORIES:
        if category != 'other':
            assert category in ROLE_KEYWORDS
