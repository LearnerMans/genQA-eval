# Implementation Plan

- [x] 1. Implement cosine similarity calculation utility





  - Create `metrics/semantic_similarity.py` module with cosine_similarity function
  - Implement efficient vector operations using numpy
  - Handle edge cases (empty vectors, dimension mismatches, zero vectors)
  - _Requirements: 1.2, 1.5, 4.3_

- [x] 1.1 Write unit tests for cosine similarity


  - Test identical vectors (similarity = 1.0)
  - Test orthogonal vectors (similarity = 0.0)
  - Test empty and zero vectors
  - Test dimension mismatch error handling
  - _Requirements: 1.2, 4.3_

- [x] 2. Add database migration for semantic_similarity column





  - Modify `db/db.py` to add semantic_similarity column to evals table
  - Add migration logic in the existing migration section
  - Use ALTER TABLE to add REAL column allowing NULL values
  - Handle migration errors gracefully with logging
  - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Enhance RAGEvalService with semantic similarity calculation









  - Add `calculate_semantic_similarity` method to `services/rag_eval_service.py`
  - Implement batch embedding for reference and generated answers
  - Calculate cosine similarity using the new utility function
  - Handle errors gracefully and return None on failure
  - _Requirements: 1.1, 1.2, 1.4, 4.1, 4.2, 4.3_
 

- [x] 4. Integrate semantic similarity into evaluation pipeline







  - Modify `generate_and_evaluate` method in RAGEvalService
  - Add semantic similarity calculation step after answer generation
  - Retrieve embedding model from test configuration
  - Include semantic similarity in returned metrics dictionary
  - Add error handling with logging
  - _Requirements: 1.1, 1.3, 1.4, 4.1, 4.4_

- [x] 5. Update database save operation for semantic similarity





  - Modify `save_evaluation_to_db` method in RAGEvalService
  - Add semantic_similarity parameter to method signature
  - Update INSERT statement to include semantic_similarity column
  - Update values tuple to include semantic_similarity value
  - _Requirements: 2.3, 2.5_

- [x] 6. Update evaluation repository to return semantic similarity





  - Modify `get_by_test_run_id` in `repos/eval_repo.py` to include semantic_similarity
  - Modify `get_full_by_run_and_qa` to include semantic_similarity in SELECT
  - Add semantic_similarity to returned dictionaries
  - _Requirements: 2.4, 2.5_

- [x] 7. Add integration tests for semantic similarity feature






  - Test end-to-end evaluation with semantic similarity calculation
  - Test database migration adds column successfully
  - Test retrieval includes semantic_similarity in results
  - Test backward compatibility with NULL values
  - Test error handling when embedding fails
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.4, 3.4_
