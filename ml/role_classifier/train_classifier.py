#!/usr/bin/env python3
"""
Train a machine learning model to classify job roles.

This replaces the rule-based system in preprocessing/role_labels.py with
a trained multi-label classifier that learns from existing labeled data.

Usage:
    python ml/role_classifier/train_classifier.py --data data/curated/jobs_all_labeled.parquet --out models/role_classifier/
"""
import argparse
import logging
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, hamming_loss, f1_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import MultiLabelBinarizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define role categories (must match preprocessing/role_labels.py)
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


def load_and_prepare_data(data_path: Path) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Load labeled data and prepare features and targets.
    
    Args:
        data_path: Path to labeled jobs parquet file
        
    Returns:
        Tuple of (features_df, target_matrix)
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Remove jobs without roles (handle both list and numpy array)
    df = df[df['roles'].apply(lambda x: hasattr(x, '__len__') and len(x) > 0)].copy()
    logger.info(f"Loaded {len(df)} jobs with role labels")
    
    # Prepare features: combine title and description
    df['text'] = df['title'].fillna('') + ' ' + df['description'].fillna('')
    
    # Convert roles from list/array format to binary matrix
    # Convert numpy arrays to lists for MultiLabelBinarizer
    df['roles_list'] = df['roles'].apply(lambda x: list(x) if hasattr(x, '__iter__') else [])
    mlb = MultiLabelBinarizer(classes=ROLE_CATEGORIES)
    y = mlb.fit_transform(df['roles_list'])
    
    # Log role distribution
    role_counts = y.sum(axis=0)
    logger.info("\nRole distribution in dataset:")
    for role, count in zip(ROLE_CATEGORIES, role_counts):
        pct = 100 * count / len(df)
        logger.info(f"  {role}: {int(count)} ({pct:.1f}%)")
    
    # Calculate multi-label statistics
    labels_per_job = y.sum(axis=1)
    logger.info(f"\nMulti-label statistics:")
    logger.info(f"  Jobs with 1 label: {(labels_per_job == 1).sum()} ({100*(labels_per_job == 1).sum()/len(df):.1f}%)")
    logger.info(f"  Jobs with 2+ labels: {(labels_per_job > 1).sum()} ({100*(labels_per_job > 1).sum()/len(df):.1f}%)")
    logger.info(f"  Max labels per job: {labels_per_job.max()}")
    logger.info(f"  Mean labels per job: {labels_per_job.mean():.2f}")
    
    return df[['text', 'title', 'description', 'roles']], y


def train_model(X_train: pd.Series, y_train: np.ndarray, X_test: pd.Series, y_test: np.ndarray) -> Tuple[object, TfidfVectorizer]:
    """
    Train a multi-label text classifier.
    
    Uses TF-IDF vectorization on combined title+description text,
    with a MultiOutputClassifier wrapping Logistic Regression.
    
    Args:
        X_train: Training text data
        y_train: Training labels (binary matrix)
        X_test: Test text data
        y_test: Test labels (binary matrix)
        
    Returns:
        Tuple of (trained_model, fitted_vectorizer)
    """
    logger.info("\n" + "="*60)
    logger.info("Training ML Role Classifier")
    logger.info("="*60)
    
    # Vectorize text features
    logger.info("Vectorizing text with TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
        stop_words='english',
        strip_accents='unicode',
        lowercase=True
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    logger.info(f"Feature matrix shape: {X_train_vec.shape}")
    logger.info(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    
    # Train multi-label classifier
    logger.info("\nTraining multi-label classifier...")
    base_estimator = LogisticRegression(
        max_iter=500,
        C=1.0,
        class_weight='balanced',
        random_state=42
    )
    
    model = MultiOutputClassifier(base_estimator, n_jobs=-1)
    model.fit(X_train_vec, y_train)
    
    logger.info("Training completed")
    
    # Evaluate on test set
    logger.info("\n" + "="*60)
    logger.info("Evaluation Results")
    logger.info("="*60)
    
    y_pred = model.predict(X_test_vec)
    
    # Overall metrics
    hamming = hamming_loss(y_test, y_pred)
    f1_micro = f1_score(y_test, y_pred, average='micro', zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
    f1_samples = f1_score(y_test, y_pred, average='samples', zero_division=0)
    
    logger.info(f"\nOverall Metrics:")
    logger.info(f"  Hamming Loss: {hamming:.4f}")
    logger.info(f"  F1 Score (micro): {f1_micro:.4f}")
    logger.info(f"  F1 Score (macro): {f1_macro:.4f}")
    logger.info(f"  F1 Score (samples): {f1_samples:.4f}")
    
    # Per-class metrics
    logger.info(f"\nPer-Class Performance:")
    logger.info("\n" + classification_report(
        y_test, y_pred, 
        target_names=ROLE_CATEGORIES,
        zero_division=0
    ))
    
    # Feature importance analysis
    logger.info("\n" + "="*60)
    logger.info("Feature Importance Analysis")
    logger.info("="*60)
    
    feature_names = vectorizer.get_feature_names_out()
    
    for i, role in enumerate(ROLE_CATEGORIES):
        if hasattr(model.estimators_[i], 'coef_'):
            coef = model.estimators_[i].coef_[0]
            top_indices = np.argsort(coef)[-10:][::-1]
            top_features = [feature_names[idx] for idx in top_indices]
            logger.info(f"\nTop features for '{role}':")
            logger.info(f"  {', '.join(top_features)}")
    
    return model, vectorizer


def save_model(model: object, vectorizer: TfidfVectorizer, output_dir: Path):
    """
    Save trained model and vectorizer to disk.
    
    Args:
        model: Trained classifier
        vectorizer: Fitted TF-IDF vectorizer
        output_dir: Directory to save model files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / 'role_classifier.joblib'
    vectorizer_path = output_dir / 'vectorizer.joblib'
    
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    
    logger.info(f"\nModel saved to: {model_path}")
    logger.info(f"Vectorizer saved to: {vectorizer_path}")
    
    # Save metadata
    metadata = {
        'role_categories': ROLE_CATEGORIES,
        'num_features': len(vectorizer.vocabulary_),
        'model_type': 'MultiOutputClassifier(LogisticRegression)'
    }
    
    metadata_path = output_dir / 'metadata.txt'
    with open(metadata_path, 'w') as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")
    
    logger.info(f"Metadata saved to: {metadata_path}")


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description='Train ML role classifier')
    parser.add_argument(
        '--data',
        type=Path,
        default=Path('data/curated/jobs_all_labeled.parquet'),
        help='Path to labeled jobs data'
    )
    parser.add_argument(
        '--out',
        type=Path,
        required=True,
        help='Output directory for trained model'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proportion of data for test set (default: 0.2)'
    )
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    # Load and prepare data
    df, y = load_and_prepare_data(args.data)
    
    # Split train/test
    logger.info(f"\nSplitting data (test_size={args.test_size}, random_state={args.random_seed})")
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'],
        y,
        test_size=args.test_size,
        random_state=args.random_seed,
        stratify=y[:, ROLE_CATEGORIES.index('other')]  # Stratify on 'other' to balance
    )
    
    logger.info(f"Training set: {len(X_train)} jobs")
    logger.info(f"Test set: {len(X_test)} jobs")
    
    # Train model
    model, vectorizer = train_model(X_train, y_train, X_test, y_test)
    
    # Save model
    save_model(model, vectorizer, args.out)
    
    logger.info("\n" + "="*60)
    logger.info("Training pipeline completed successfully!")
    logger.info("="*60)


if __name__ == '__main__':
    main()
