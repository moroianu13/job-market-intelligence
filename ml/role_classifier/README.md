# ML Role Classifier

Machine learning-based job role classification system that replaces the rule-based classifier with a trained multi-label text classification model.

## Overview

The ML role classifier uses TF-IDF text vectorization and Logistic Regression to predict job roles from job titles and descriptions. It's trained on the same data initially labeled by the rule-based system but learns to generalize patterns beyond simple keyword matching.

## Performance Metrics

**Training Performance (Test Set):**
- F1 Score (micro): **0.916**
- F1 Score (macro): **0.834**
- Hamming Loss: **0.024**
- Agreement with rule-based: **90.5%**

**Per-Class F1 Scores:**
- data_scientist: 0.97
- data_engineer: 0.94
- machine_learning_engineer: 0.92
- data_analyst: 0.86
- cybersecurity_specialist: 0.80
- devops_engineer: 0.77
- software_engineer: 0.77
- other: 0.64

## Key Features

- **Multi-label classification**: Jobs can have multiple roles simultaneously
- **Text-based learning**: Learns from title and description text patterns
- **Feature importance**: Provides interpretable features for each role
- **Fast inference**: Batch prediction on 2486 jobs in <1 second
- **Drop-in replacement**: Can be used instead of rule-based system with a single flag

## Architecture

### Training Pipeline (`train_classifier.py`)
1. Load labeled jobs from `jobs_all_labeled.parquet`
2. Combine title + description into single text field
3. Convert multi-label roles to binary matrix (8 classes)
4. Split into train/test (80/20)
5. Vectorize text with TF-IDF (max 5000 features, 1-2 grams)
6. Train MultiOutputClassifier with LogisticRegression
7. Evaluate and save model + vectorizer

### Prediction Pipeline (`predict_classifier.py`)
1. Load trained model and vectorizer
2. Preprocess input text (title + description)
3. Transform with fitted TF-IDF vectorizer
4. Predict probabilities for each role
5. Apply threshold (default 0.5) for multi-label output
6. Return role list (minimum 'other' if no predictions)

## Usage

### Train a New Model

```bash
python ml/role_classifier/train_classifier.py \
    --data data/curated/jobs_all_labeled.parquet \
    --out models/role_classifier/2026-01-22 \
    --test-size 0.2 \
    --random-seed 42
```

### Use in Pipeline

**With ML classifier:**
```bash
python processing/label_all_jobs.py --ml --model models/role_classifier/2026-01-22
```

**With rule-based classifier (default):**
```bash
python processing/label_all_jobs.py
```

### Programmatic Usage

```python
from ml.role_classifier import RolePredictor

# Load model
predictor = RolePredictor('models/role_classifier/2026-01-22')

# Predict single job
roles = predictor.predict_roles(
    title="Senior Data Scientist",
    description="Build ML models with Python, TensorFlow..."
)
# Returns: ['data_scientist', 'machine_learning_engineer']

# Batch prediction
import pandas as pd
df = pd.read_parquet('data/normalized/jobs.parquet')
df_labeled = predictor.predict_batch(df, threshold=0.5)
```

### Compare Classifiers

```bash
python ml/role_classifier/compare_classifiers.py
```

## Model Details

**Vectorizer:** TfidfVectorizer
- max_features: 5000
- ngram_range: (1, 2)
- min_df: 2
- max_df: 0.9
- stop_words: 'english'

**Base Estimator:** LogisticRegression
- max_iter: 500
- C: 1.0
- class_weight: 'balanced'
- multi_class: handled by MultiOutputClassifier

**Multi-label Strategy:** MultiOutputClassifier
- One binary classifier per role
- Independent predictions
- Threshold-based final decision

## Key Insights

### Comparison with Rule-Based System

The ML classifier shows several improvements:

1. **More Multi-label Predictions** (17.1% vs 13.4%)
   - Better captures jobs with overlapping responsibilities
   - Example: "Data Scientist/Engineer" → multiple roles

2. **Better Generalization**
   - Learns patterns beyond exact keywords
   - Example: "Analytics Solution Architect" → data_engineer + data_analyst

3. **Reduced 'Other' Category** (initially)
   - More confident in specialized roles
   - +42% in 'other' due to boundary cases learning

4. **Key Transitions:**
   - Added 'other': 76 jobs (32.3% of changes)
   - Added 'machine_learning_engineer': 40 jobs (17.0%)
   - Added 'devops_engineer': 28 jobs (11.9%)

### Top Features Per Role

**Data Scientist:**
`data scientist`, `scientist`, `data science`, `science`

**Data Engineer:**
`data engineer`, `engineer`, `data engineering`, `databricks`, `azure`

**Machine Learning Engineer:**
`learning engineer`, `machine learning`, `ai`, `ml engineer`, `mlops`

**Data Analyst:**
`analyst`, `data analyst`, `business intelligence`, `bi`, `analytics`

**DevOps Engineer:**
`devops`, `platform engineer`, `cloud`, `azure devops`

## Files

- `train_classifier.py` - Training script
- `predict_classifier.py` - Inference script and RolePredictor class
- `compare_classifiers.py` - Comparison tool
- `__init__.py` - Module interface
- `README.md` - This file

## Model Artifacts

Saved to `models/role_classifier/YYYY-MM-DD/`:
- `role_classifier.joblib` - Trained MultiOutputClassifier
- `vectorizer.joblib` - Fitted TfidfVectorizer
- `metadata.txt` - Model configuration

## Future Improvements

1. **Active Learning**: Flag uncertain predictions for human review
2. **Advanced Models**: Try XGBoost, Random Forest, or neural networks
3. **Contextual Embeddings**: Use BERT/sentence transformers
4. **Hierarchical Classification**: Model role relationships
5. **Confidence Scores**: Return probabilities with predictions
6. **Online Learning**: Update model with new labeled data
7. **Cross-validation**: More robust evaluation with k-fold CV
8. **Hyperparameter Tuning**: Grid search for optimal parameters

## Notes

- The model is trained on rule-based labels, so it learns those patterns
- 90.5% agreement indicates the model successfully learns the rules
- Disagreements often show where ML generalizes better
- 'Other' category remains challenging (F1: 0.64) due to diversity
- Multi-label threshold (0.5) can be tuned per use case
