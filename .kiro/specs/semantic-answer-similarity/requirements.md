# Requirements Document

## Introduction

This feature adds semantic similarity comparison between reference answers (from QA pairs) and LLM-generated answers in the RAG evaluation system. The comparison uses the existing embedding model configured in each test to calculate cosine similarity, providing a lightweight metric that works on laptops without requiring additional large models. This metric will be stored in the database alongside existing evaluation metrics.

## Glossary

- **RAG System**: Retrieval-Augmented Generation system that answers questions using retrieved context
- **QA Pair**: Question-Answer pair containing a reference question and expected answer
- **LLM-Generated Answer**: Answer produced by the language model during evaluation
- **Reference Answer**: Ground truth answer from the QA pair
- **Embedding Model**: Neural network model that converts text into vector representations. it can be found in the test config 
- **Cosine Similarity**: Metric measuring similarity between two vectors (range: -1 to 1, typically 0 to 1 for text)
- **Test Configuration**: Settings for a test including chunk size, embedding model, and generative model
- **Evaluation Record**: Database record storing all metrics for a single QA pair evaluation

## Requirements

### Requirement 1

**User Story:** As a RAG system evaluator, I want to measure semantic similarity between reference answers and generated answers, so that I can assess answer accuracy beyond lexical overlap.

#### Acceptance Criteria

1. WHEN the RAG Evaluation Service generates an answer, THE System SHALL calculate semantic similarity between the generated answer and reference answer using the test's configured embedding model
2. THE System SHALL compute cosine similarity between the two answer embeddings and store the result as a decimal value between 0 and 1
3. THE System SHALL store the semantic similarity score in the evaluation record in the database
4. THE System SHALL use the same embedding model specified in the test configuration for consistency with the retrieval pipeline
5. THE System SHALL calculate semantic similarity without requiring additional large language models beyond the configured embedding model

### Requirement 2

**User Story:** As a developer, I want the semantic similarity metric stored in the database, so that I can retrieve and analyze it alongside other evaluation metrics.

#### Acceptance Criteria

1. THE System SHALL add a new column named "semantic_similarity" to the evals table with REAL data type
2. THE System SHALL execute database migration to add the semantic_similarity column to existing databases without data loss
3. WHEN saving an evaluation record, THE System SHALL store the semantic similarity score in the semantic_similarity column
4. WHEN retrieving evaluation records, THE System SHALL include the semantic_similarity value in the returned data
5. THE System SHALL allow NULL values for semantic_similarity to support backward compatibility with existing evaluation records

### Requirement 3

**User Story:** As a system administrator, I want the database schema to be automatically migrated, so that existing installations can adopt the new feature without manual intervention.

#### Acceptance Criteria

1. WHEN the database connection is initialized, THE System SHALL check if the semantic_similarity column exists in the evals table
2. IF the semantic_similarity column does not exist, THEN THE System SHALL execute an ALTER TABLE statement to add the column
3. THE System SHALL handle migration errors gracefully and log appropriate error messages
4. THE System SHALL maintain all existing data in the evals table during migration
5. THE System SHALL complete the migration within the existing database initialization transaction

### Requirement 4

**User Story:** As a RAG system evaluator, I want semantic similarity calculated efficiently, so that evaluation performance remains acceptable on laptop hardware.

#### Acceptance Criteria

1. THE System SHALL reuse the existing embedding service instance to avoid redundant model loading
2. THE System SHALL calculate embeddings for both reference and generated answers in a single batch operation when possible
3. THE System SHALL compute cosine similarity using efficient vector operations
4. THE System SHALL complete semantic similarity calculation within 2 seconds per QA pair on typical laptop hardware
5. THE System SHALL not require GPU acceleration for semantic similarity calculation
