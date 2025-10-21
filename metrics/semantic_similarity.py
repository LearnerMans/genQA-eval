"""
Semantic similarity calculation utilities.

This module provides functions for calculating semantic similarity between
text embeddings using cosine similarity.
"""

import numpy as np
from typing import List


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Cosine similarity measures the cosine of the angle between two vectors,
    providing a metric of similarity that ranges from -1 to 1 (typically 0 to 1
    for text embeddings). A value of 1 indicates identical direction, 0 indicates
    orthogonality, and -1 indicates opposite direction.
    
    Formula: cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
    
    Args:
        vec1: First embedding vector as a list of floats
        vec2: Second embedding vector as a list of floats
        
    Returns:
        Cosine similarity score, typically between 0.0 and 1.0 for text embeddings
        
    Raises:
        ValueError: If vectors have different dimensions or are empty
    """
    # Handle empty vectors
    if not vec1 or not vec2:
        raise ValueError("Vectors cannot be empty")
    
    # Check dimension match
    if len(vec1) != len(vec2):
        raise ValueError(
            f"Vector dimensions must match: vec1 has {len(vec1)} dimensions, "
            f"vec2 has {len(vec2)} dimensions"
        )
    
    # Convert to numpy arrays for efficient computation
    arr1 = np.array(vec1, dtype=np.float64)
    arr2 = np.array(vec2, dtype=np.float64)
    
    # Calculate magnitudes (L2 norms)
    magnitude1 = np.linalg.norm(arr1)
    magnitude2 = np.linalg.norm(arr2)
    
    # Handle zero vectors
    if magnitude1 == 0.0 or magnitude2 == 0.0:
        raise ValueError("Cannot calculate cosine similarity for zero vectors")
    
    # Calculate dot product
    dot_product = np.dot(arr1, arr2)
    
    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)
    
    # Clamp to [-1, 1] to handle floating point precision issues
    similarity = np.clip(similarity, -1.0, 1.0)
    
    return float(similarity)
