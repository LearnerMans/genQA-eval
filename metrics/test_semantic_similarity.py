"""
Unit tests for semantic similarity calculations.
"""

import pytest
import numpy as np
from metrics.semantic_similarity import cosine_similarity


class TestCosineSimilarity:
    """Test cases for cosine_similarity function."""
    
    def test_identical_vectors(self):
        """Test that identical vectors have similarity of 1.0."""
        vec = [1.0, 2.0, 3.0, 4.0]
        similarity = cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, abs=1e-6)
    
    def test_identical_normalized_vectors(self):
        """Test identical unit vectors have similarity of 1.0."""
        vec = [0.6, 0.8]  # Unit vector
        similarity = cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, abs=1e-6)
    
    def test_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity of 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0, abs=1e-6)
    
    def test_opposite_vectors(self):
        """Test that opposite vectors have similarity of -1.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0, abs=1e-6)
    
    def test_similar_vectors(self):
        """Test vectors with similar direction have high similarity."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.1, 2.1, 2.9]
        similarity = cosine_similarity(vec1, vec2)
        assert similarity > 0.99
    
    def test_empty_vector_first(self):
        """Test that empty first vector raises ValueError."""
        vec1 = []
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="Vectors cannot be empty"):
            cosine_similarity(vec1, vec2)
    
    def test_empty_vector_second(self):
        """Test that empty second vector raises ValueError."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = []
        with pytest.raises(ValueError, match="Vectors cannot be empty"):
            cosine_similarity(vec1, vec2)
    
    def test_both_empty_vectors(self):
        """Test that both empty vectors raise ValueError."""
        vec1 = []
        vec2 = []
        with pytest.raises(ValueError, match="Vectors cannot be empty"):
            cosine_similarity(vec1, vec2)
    
    def test_zero_vector_first(self):
        """Test that zero first vector raises ValueError."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="Cannot calculate cosine similarity for zero vectors"):
            cosine_similarity(vec1, vec2)
    
    def test_zero_vector_second(self):
        """Test that zero second vector raises ValueError."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        with pytest.raises(ValueError, match="Cannot calculate cosine similarity for zero vectors"):
            cosine_similarity(vec1, vec2)
    
    def test_both_zero_vectors(self):
        """Test that both zero vectors raise ValueError."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0]
        with pytest.raises(ValueError, match="Cannot calculate cosine similarity for zero vectors"):
            cosine_similarity(vec1, vec2)
    
    def test_dimension_mismatch_smaller_first(self):
        """Test that dimension mismatch raises ValueError when first vector is smaller."""
        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="Vector dimensions must match"):
            cosine_similarity(vec1, vec2)
    
    def test_dimension_mismatch_larger_first(self):
        """Test that dimension mismatch raises ValueError when first vector is larger."""
        vec1 = [1.0, 2.0, 3.0, 4.0]
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="Vector dimensions must match"):
            cosine_similarity(vec1, vec2)
    
    def test_high_dimensional_vectors(self):
        """Test cosine similarity with high-dimensional vectors (like embeddings)."""
        # Simulate embedding-like vectors (1536 dimensions)
        np.random.seed(42)
        vec1 = np.random.randn(1536).tolist()
        vec2 = np.random.randn(1536).tolist()
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Random vectors should have low similarity
        assert -1.0 <= similarity <= 1.0
        assert abs(similarity) < 0.2  # Typically very small for random vectors
    
    def test_normalized_embeddings(self):
        """Test with normalized vectors (like OpenAI embeddings)."""
        # Create unit vectors
        vec1 = [0.6, 0.8]
        vec2 = [0.8, 0.6]
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Should be positive and less than 1
        assert 0.0 < similarity < 1.0
        assert similarity == pytest.approx(0.96, abs=0.01)
