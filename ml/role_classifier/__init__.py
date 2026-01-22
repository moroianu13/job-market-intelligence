"""
ML Role Classifier module.

This module provides machine learning-based role classification
to replace the rule-based system in preprocessing/role_labels.py.
"""
from .predict_classifier import RolePredictor

__all__ = ['RolePredictor']
