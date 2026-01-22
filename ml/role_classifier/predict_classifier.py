#!/usr/bin/env python3
"""
Use trained ML role classifier to predict roles for new jobs.

This module provides functions to load the trained model and apply it
to job postings, replacing the rule-based classification system.

Usage:
    # As a module
    from ml.role_classifier.predict_classifier import RolePredictor
    predictor = RolePredictor('models/role_classifier/')
    roles = predictor.predict_roles(title="Data Scientist", description="...")
    
    # As a CLI tool
    python ml/role_classifier/predict_classifier.py --model models/role_classifier/ --input data/normalized/jobs.parquet --output data/curated/jobs_ml_labeled.parquet
"""
import argparse
import logging
from pathlib import Path
from typing import List, Union

import joblib
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Role categories (must match train_classifier.py)
ROLE_CATEGORIES = [
    'data_scientist',
    'data_engineer',
    'machine_learning_engineer',
    'data_analyst',
    'cybersecurity_specialist',
    'devops_engineer',
    'software_engineer',
    'other'
]


class RolePredictor:
    """
    ML-based role predictor that loads a trained model and vectorizer.
    """
    
    def __init__(self, model_dir: Union[str, Path]):
        """
        Initialize predictor by loading trained model and vectorizer.
        
        Args:
            model_dir: Directory containing role_classifier.joblib and vectorizer.joblib
        """
        model_dir = Path(model_dir)
        
        model_path = model_dir / 'role_classifier.joblib'
        vectorizer_path = model_dir / 'vectorizer.joblib'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        if not vectorizer_path.exists():
            raise FileNotFoundError(f"Vectorizer not found at {vectorizer_path}")
        
        logger.info(f"Loading model from {model_dir}")
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)
        
        # Initialize binarizer for converting predictions back to labels
        self.mlb = MultiLabelBinarizer(classes=ROLE_CATEGORIES)
        self.mlb.fit([[role] for role in ROLE_CATEGORIES])
        
        logger.info("Model loaded successfully")
    
    def predict_roles(self, title: str, description: str, threshold: float = 0.5) -> List[str]:
        """
        Predict role labels for a single job posting.
        
        Args:
            title: Job title
            description: Job description text
            threshold: Probability threshold for multi-label classification (default: 0.5)
            
        Returns:
            List of predicted role labels (e.g., ['data_scientist', 'machine_learning_engineer'])
        """
        # Combine title and description
        text = f"{title or ''} {description or ''}"
        
        # Vectorize
        X = self.vectorizer.transform([text])
        
        # Predict probabilities
        if hasattr(self.model, 'predict_proba'):
            # Get probabilities for each class
            proba_list = []
            for estimator in self.model.estimators_:
                proba = estimator.predict_proba(X)[0]
                # Take probability of positive class (index 1)
                proba_list.append(proba[1] if len(proba) > 1 else 0.0)
            
            # Apply threshold
            y_pred = [1 if p >= threshold else 0 for p in proba_list]
        else:
            # Fallback to binary prediction
            y_pred = self.model.predict(X)[0]
        
        # Convert binary predictions to role labels
        roles = [role for role, pred in zip(ROLE_CATEGORIES, y_pred) if pred == 1]
        
        # Ensure at least 'other' if no roles predicted
        if not roles:
            roles = ['other']
        
        return roles
    
    def predict_batch(self, df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        """
        Predict role labels for a batch of jobs in a DataFrame.
        
        Args:
            df: DataFrame with 'title' and 'description' columns
            threshold: Probability threshold for multi-label classification
            
        Returns:
            DataFrame with added 'roles' column containing predicted labels
        """
        logger.info(f"Predicting roles for {len(df)} jobs...")
        
        # Prepare text
        text_series = (df['title'].fillna('') + ' ' + df['description'].fillna(''))
        
        # Vectorize
        X = self.vectorizer.transform(text_series)
        
        # Predict
        if hasattr(self.model, 'predict_proba'):
            # Get probabilities for each class
            proba_matrix = []
            for estimator in self.model.estimators_:
                proba = estimator.predict_proba(X)
                # Take probability of positive class (index 1)
                proba_col = [p[1] if len(p) > 1 else 0.0 for p in proba]
                proba_matrix.append(proba_col)
            
            # Convert to array and apply threshold
            import numpy as np
            proba_matrix = np.array(proba_matrix).T  # Shape: (n_samples, n_classes)
            y_pred = (proba_matrix >= threshold).astype(int)
        else:
            y_pred = self.model.predict(X)
        
        # Convert predictions to role lists
        roles_list = []
        for pred_row in y_pred:
            roles = [role for role, pred in zip(ROLE_CATEGORIES, pred_row) if pred == 1]
            # Ensure at least 'other' if no roles predicted
            if not roles:
                roles = ['other']
            roles_list.append(roles)
        
        # Add to DataFrame
        df_result = df.copy()
        df_result['roles'] = roles_list
        
        logger.info("Prediction completed")
        
        # Log role distribution
        all_roles = [role for roles in roles_list for role in roles]
        from collections import Counter
        role_counts = Counter(all_roles)
        logger.info("\nPredicted role distribution:")
        for role in ROLE_CATEGORIES:
            count = role_counts.get(role, 0)
            pct = 100 * count / len(df)
            logger.info(f"  {role}: {count} ({pct:.1f}%)")
        
        return df_result


def main():
    """CLI interface for batch prediction."""
    parser = argparse.ArgumentParser(description='Predict roles using trained ML classifier')
    parser.add_argument(
        '--model',
        type=Path,
        required=True,
        help='Directory containing trained model files'
    )
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input parquet file with jobs to classify'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output parquet file with predicted roles'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Probability threshold for classification (default: 0.5)'
    )
    
    args = parser.parse_args()
    
    # Load model
    predictor = RolePredictor(args.model)
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    df = pd.read_parquet(args.input)
    
    # Predict
    df_result = predictor.predict_batch(df, threshold=args.threshold)
    
    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df_result.to_parquet(args.output, index=False)
    logger.info(f"Saved predictions to {args.output}")


if __name__ == '__main__':
    main()
