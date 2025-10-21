"""
Integration tests for semantic similarity feature.

Tests the complete semantic similarity pipeline:
1. Database migration adds semantic_similarity column
2. End-to-end evaluation with semantic similarity calculation
3. Database storage and retrieval of semantic similarity
4. Backward compatibility with NULL values
5. Error handling when embedding fails
"""

import unittest
import tempfile
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from db.db import DB
from vectorDb.db import VectorDb
from services.rag_eval_service import RAGEvalService
from llm.openai_embeddings import OpenAIEmbeddings
from llm.openai_llm import OpenAILLM
from repos.eval_repo import EvalRepo


def get_mock_lexical_metrics():
    """Helper function to get mock lexical metrics matching score_texts output format."""
    return {
        'BLEU': 0.75,
        'BLEU_by_n': [0.8, 0.75, 0.7, 0.65],
        'BLEU_BP': 1.0,
        'ROUGE_L': 0.80,
        'ROUGE_L_precision': 0.82,
        'ROUGE_L_recall': 0.78,
        'ROUGE_L_lcs': 10,
        'SQuAD_EM': 0.0,
        'SQuAD_token_F1': 0.85,
        'ContentF1': 0.83,
        'ContentF1_precision': 0.85,
        'ContentF1_recall': 0.81,
        'Aggregate': 0.79,
        'Aggregate_weights': {'BLEU': 0.3, 'ROUGE_L': 0.4, 'ContentF1': 0.2, 'EM': 0.1}
    }


class TestSemanticSimilarityIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for semantic similarity feature."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db = DB(self.db_path)
        
        # Create eval repository
        self.eval_repo = EvalRepo(self.db)
        
        # Mock vector database
        self.vector_db_mock = Mock(spec=VectorDb)
        
        # Mock LLM and embeddings
        self.llm_mock = Mock(spec=OpenAILLM)
        self.llm_mock.generate = AsyncMock()
        
        self.embeddings_mock = Mock(spec=OpenAIEmbeddings)
        self.embeddings_mock.embed_text = AsyncMock()
        self.embeddings_mock.embed_texts = AsyncMock()
        
        # Create service instance
        self.service = RAGEvalService(
            db=self.db,
            vector_db=self.vector_db_mock,
            llm=self.llm_mock,
            embeddings=self.embeddings_mock
        )
        
        # Test data
        self.test_run_id = "test_run_integration_001"
        self.qa_pair_id = "qa_integration_001"
        self.query = "What are the benefits of regular exercise?"
        self.reference_answer = "Regular exercise improves cardiovascular health and mental well-being."
        self.generated_answer = "Exercise benefits include better heart health and improved mood."
        
        # Create required foreign key records
        # Create project
        project_id = "project_integration_001"
        self.db.execute(
            "INSERT INTO projects (id, name) VALUES (?, ?)",
            (project_id, "Integration Test Project")
        )
        
        # Create test
        test_id = "test_integration_001"
        self.db.execute(
            "INSERT INTO tests (id, project_id, name) VALUES (?, ?, ?)",
            (test_id, project_id, "Integration Test")
        )
        
        # Create config
        config_id = "config_integration_001"
        self.db.execute(
            "INSERT INTO config (id, test_id, type, chunk_size, overlap) VALUES (?, ?, ?, ?, ?)",
            (config_id, test_id, "semantic", 500, 50)
        )
        
        # Create test run
        self.db.execute(
            "INSERT INTO test_runs (id, test_id, config_id) VALUES (?, ?, ?)",
            (self.test_run_id, test_id, config_id)
        )
        
        # Create QA pair
        import hashlib
        qa_hash = hashlib.md5(f"{self.query}{self.reference_answer}".encode()).hexdigest()
        self.db.execute(
            "INSERT INTO question_answer_pairs (id, project_id, hash, question, answer) VALUES (?, ?, ?, ?, ?)",
            (self.qa_pair_id, project_id, qa_hash, self.query, self.reference_answer)
        )
        
        # Create dummy sources and chunks for FK constraints
        source_id = "source_integration_001"
        self.db.execute(
            "INSERT INTO sources (id, type, path_or_link, test_id) VALUES (?, ?, ?, ?)",
            (source_id, "file", "/test/path", test_id)
        )
        
        self.db.execute(
            "INSERT INTO chunks (id, type, source_id, content, chunk_index) VALUES (?, ?, ?, ?, ?)",
            ("chunk_1", "file", source_id, "Exercise improves heart health", 0)
        )
        
        self.db.execute(
            "INSERT INTO chunks (id, type, source_id, content, chunk_index) VALUES (?, ?, ?, ?, ?)",
            ("chunk_2", "file", source_id, "Physical activity boosts mental health", 1)
        )
        
        # Mock contexts - format expected by vector_db.search_similar
        self.mock_vector_results = [
            {
                'id': 'chunk_1',
                'distance': 0.1,
                'metadata': {
                    'content': 'Exercise improves heart health',
                    'source': 'doc1'
                }
            },
            {
                'id': 'chunk_2',
                'distance': 0.2,
                'metadata': {
                    'content': 'Physical activity boosts mental health',
                    'source': 'doc2'
                }
            }
        ]
        
        # Mock embeddings (1536-dimensional vectors)
        self.ref_embedding = [0.1] * 1536
        self.gen_embedding = [0.09] * 1536

    async def asyncTearDown(self):
        """Clean up test fixtures."""
        self.db.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_migration_adds_semantic_similarity_column(self):
        """Test that database migration successfully adds semantic_similarity column."""
        # Query table schema
        cur = self.db.execute("PRAGMA table_info('evals')")
        columns = {row[1]: row[2] for row in cur.fetchall()}
        
        # Verify semantic_similarity column exists
        self.assertIn('semantic_similarity', columns)
        self.assertEqual(columns['semantic_similarity'], 'REAL')


    async def test_end_to_end_evaluation_with_semantic_similarity(self):
        """Test complete evaluation pipeline includes semantic similarity calculation."""
        # Setup mocks - need to return awaitable for async methods
        async def mock_embed_text(text):
            return [0.1] * 1536
        
        self.embeddings_mock.embed_text = mock_embed_text
        self.vector_db_mock.search_similar.return_value = self.mock_vector_results
        self.llm_mock.generate.return_value = self.generated_answer
        
        # Mock embed_texts for semantic similarity calculation
        self.embeddings_mock.embed_texts.return_value = [
            self.ref_embedding,
            self.gen_embedding
        ]
        
        # Mock lexical metrics
        mock_lexical_metrics = get_mock_lexical_metrics()
        
        # Mock LLM-judged evaluation
        from metrics.rag_evaluator import (
            RAGEvaluation, ContextRelevance, Groundedness, AnswerRelevance, Score
        )
        
        mock_evaluation = RAGEvaluation(
            context_relevance=ContextRelevance(
                explanation="Contexts are relevant",
                score=Score.EXCELLENT,
                per_context_scores=[3.0, 2.5]
            ),
            groundedness=Groundedness(
                explanation="Answer is grounded",
                score=Score.EXCELLENT,
                supported_claims=3,
                total_claims=3
            ),
            answer_relevance=AnswerRelevance(
                explanation="Answer is relevant",
                score=Score.GOOD
            ),
            overall_score=2.67
        )
        
        with patch('services.rag_eval_service.score_texts', return_value=mock_lexical_metrics):
            with patch('services.rag_eval_service.evaluate_rag', return_value=mock_evaluation):
                # Execute evaluation
                result = await self.service.generate_and_evaluate(
                    test_run_id=self.test_run_id,
                    qa_pair_id=self.qa_pair_id,
                    query=self.query,
                    reference_answer=self.reference_answer,
                    collection_name="test_collection",
                    top_k=2,
                    embedding_model=self.embeddings_mock
                )
        
        # Verify semantic similarity was calculated
        self.assertIn('semantic_similarity', result)
        self.assertIsNotNone(result['semantic_similarity'])
        self.assertIsInstance(result['semantic_similarity'], float)
        self.assertGreaterEqual(result['semantic_similarity'], 0.0)
        self.assertLessEqual(result['semantic_similarity'], 1.0)
        
        # Verify embed_texts was called with both answers
        self.embeddings_mock.embed_texts.assert_called_once()
        call_args = self.embeddings_mock.embed_texts.call_args[0][0]
        self.assertEqual(len(call_args), 2)
        self.assertEqual(call_args[0], self.reference_answer)
        self.assertEqual(call_args[1], self.generated_answer)


    async def test_semantic_similarity_stored_in_database(self):
        """Test that semantic similarity is correctly stored in database."""
        # Prepare test data
        lexical_metrics = {
            'bleu': 0.75,
            'rouge_l': 0.80,
            'rouge_l_precision': 0.82,
            'rouge_l_recall': 0.78,
            'squad_em': 0.0,
            'squad_token_f1': 0.85,
            'content_f1': 0.83,
            'lexical_aggregate': 0.79
        }
        
        llm_judged_metrics = {
            'answer_relevance': 2.0,
            'context_relevance': 3.0,
            'groundedness': 3.0,
            'llm_judged_overall': 2.67
        }
        
        llm_judged_reasoning = {
            'answer_relevance': 'Answer is relevant',
            'context_relevance': 'Contexts are relevant',
            'groundedness': 'Answer is grounded',
            'context_relevance_per_context': [3.0, 2.5],
            'groundedness_supported_claims': 3,
            'groundedness_total_claims': 3
        }
        
        semantic_similarity = 0.92
        
        # Save evaluation with semantic similarity
        eval_id = self.service.save_evaluation_to_db(
            test_run_id=self.test_run_id,
            qa_pair_id=self.qa_pair_id,
            generated_answer=self.generated_answer,
            lexical_metrics=lexical_metrics,
            llm_judged_metrics=llm_judged_metrics,
            llm_judged_reasoning=llm_judged_reasoning,
            chunk_ids=None,  # Don't use chunk_ids to avoid FK constraint issues
            semantic_similarity=semantic_similarity
        )
        
        # Retrieve from database
        cur = self.db.execute(
            "SELECT semantic_similarity FROM evals WHERE id = ?",
            (eval_id,)
        )
        row = cur.fetchone()
        
        # Verify semantic similarity was stored
        self.assertIsNotNone(row)
        self.assertEqual(row[0], semantic_similarity)


    async def test_retrieval_includes_semantic_similarity(self):
        """Test that evaluation retrieval includes semantic_similarity in results."""
        # First, save an evaluation with semantic similarity
        lexical_metrics = {
            'bleu': 0.75,
            'rouge_l': 0.80,
            'rouge_l_precision': 0.82,
            'rouge_l_recall': 0.78,
            'squad_em': 0.0,
            'squad_token_f1': 0.85,
            'content_f1': 0.83,
            'lexical_aggregate': 0.79
        }
        
        llm_judged_metrics = {
            'answer_relevance': 2.0,
            'context_relevance': 3.0,
            'groundedness': 3.0,
            'llm_judged_overall': 2.67
        }
        
        llm_judged_reasoning = {
            'answer_relevance': 'Answer is relevant',
            'context_relevance': 'Contexts are relevant',
            'groundedness': 'Answer is grounded',
            'context_relevance_per_context': [3.0, 2.5],
            'groundedness_supported_claims': 3,
            'groundedness_total_claims': 3
        }
        
        semantic_similarity = 0.88
        
        eval_id = self.service.save_evaluation_to_db(
            test_run_id=self.test_run_id,
            qa_pair_id=self.qa_pair_id,
            generated_answer=self.generated_answer,
            lexical_metrics=lexical_metrics,
            llm_judged_metrics=llm_judged_metrics,
            llm_judged_reasoning=llm_judged_reasoning,
            chunk_ids=None,  # Don't use chunk_ids to avoid FK constraint issues
            semantic_similarity=semantic_similarity
        )
        
        # Retrieve using eval_repo
        results = self.eval_repo.get_by_test_run_id(self.test_run_id)
        
        # Verify semantic_similarity is in results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIn('semantic_similarity', result)
        self.assertEqual(result['semantic_similarity'], semantic_similarity)


    async def test_backward_compatibility_with_null_values(self):
        """Test that existing records with NULL semantic_similarity are handled correctly."""
        # Create a separate QA pair for this test
        import hashlib
        qa_pair_id_old = "qa_old_001"
        qa_hash_old = hashlib.md5("Old questionOld answer".encode()).hexdigest()
        
        # Get project_id from test_runs
        cur = self.db.execute("SELECT test_id FROM test_runs WHERE id = ?", (self.test_run_id,))
        test_id = cur.fetchone()[0]
        cur = self.db.execute("SELECT project_id FROM tests WHERE id = ?", (test_id,))
        project_id = cur.fetchone()[0]
        
        self.db.execute(
            "INSERT INTO question_answer_pairs (id, project_id, hash, question, answer) VALUES (?, ?, ?, ?, ?)",
            (qa_pair_id_old, project_id, qa_hash_old, "Old question", "Old answer")
        )
        
        # Save evaluation WITHOUT semantic similarity (simulating old records)
        lexical_metrics = {
            'bleu': 0.70,
            'rouge_l': 0.75,
            'rouge_l_precision': 0.78,
            'rouge_l_recall': 0.72,
            'squad_em': 0.0,
            'squad_token_f1': 0.80,
            'content_f1': 0.78,
            'lexical_aggregate': 0.74
        }
        
        llm_judged_metrics = {
            'answer_relevance': 2.0,
            'context_relevance': 2.5,
            'groundedness': 2.5,
            'llm_judged_overall': 2.33
        }
        
        llm_judged_reasoning = {
            'answer_relevance': 'Relevant',
            'context_relevance': 'Relevant',
            'groundedness': 'Grounded',
            'context_relevance_per_context': [2.5],
            'groundedness_supported_claims': 2,
            'groundedness_total_claims': 2
        }
        
        # Save without semantic_similarity (should be NULL)
        eval_id = self.service.save_evaluation_to_db(
            test_run_id=self.test_run_id,
            qa_pair_id=qa_pair_id_old,
            generated_answer=self.generated_answer,
            lexical_metrics=lexical_metrics,
            llm_judged_metrics=llm_judged_metrics,
            llm_judged_reasoning=llm_judged_reasoning,
            chunk_ids=[],
            semantic_similarity=None  # Explicitly NULL
        )
        
        # Retrieve from database
        cur = self.db.execute(
            "SELECT semantic_similarity FROM evals WHERE id = ?",
            (eval_id,)
        )
        row = cur.fetchone()
        
        # Verify NULL is stored correctly
        self.assertIsNotNone(row)
        self.assertIsNone(row[0])
        
        # Verify retrieval via eval_repo handles NULL gracefully
        results = self.eval_repo.get_by_test_run_id(self.test_run_id)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIn('semantic_similarity', result)
        self.assertIsNone(result['semantic_similarity'])


    async def test_error_handling_when_embedding_fails(self):
        """Test that evaluation continues gracefully when embedding generation fails."""
        # Create a separate QA pair for this test
        import hashlib
        qa_pair_id_error = "qa_error_001"
        qa_hash_error = hashlib.md5(f"{self.query}{self.reference_answer}error".encode()).hexdigest()
        
        # Get project_id from test_runs
        cur = self.db.execute("SELECT test_id FROM test_runs WHERE id = ?", (self.test_run_id,))
        test_id = cur.fetchone()[0]
        cur = self.db.execute("SELECT project_id FROM tests WHERE id = ?", (test_id,))
        project_id = cur.fetchone()[0]
        
        self.db.execute(
            "INSERT INTO question_answer_pairs (id, project_id, hash, question, answer) VALUES (?, ?, ?, ?, ?)",
            (qa_pair_id_error, project_id, qa_hash_error, self.query, self.reference_answer)
        )
        
        # Setup mocks
        async def mock_embed_text(text):
            return [0.1] * 1536
        
        self.embeddings_mock.embed_text = mock_embed_text
        self.vector_db_mock.search_similar.return_value = self.mock_vector_results
        self.llm_mock.generate.return_value = self.generated_answer
        
        # Mock embed_texts to raise an exception
        self.embeddings_mock.embed_texts.side_effect = Exception("Embedding API failure")
        
        # Mock lexical metrics
        mock_lexical_metrics = get_mock_lexical_metrics()
        
        # Mock LLM-judged evaluation
        from metrics.rag_evaluator import (
            RAGEvaluation, ContextRelevance, Groundedness, AnswerRelevance, Score
        )
        
        mock_evaluation = RAGEvaluation(
            context_relevance=ContextRelevance(
                explanation="Contexts are relevant",
                score=Score.EXCELLENT,
                per_context_scores=[3.0, 2.5]
            ),
            groundedness=Groundedness(
                explanation="Answer is grounded",
                score=Score.EXCELLENT,
                supported_claims=3,
                total_claims=3
            ),
            answer_relevance=AnswerRelevance(
                explanation="Answer is relevant",
                score=Score.GOOD
            ),
            overall_score=2.67
        )
        
        with patch('services.rag_eval_service.score_texts', return_value=mock_lexical_metrics):
            with patch('services.rag_eval_service.evaluate_rag', return_value=mock_evaluation):
                # Execute evaluation - should not raise exception
                result = await self.service.generate_and_evaluate(
                    test_run_id=self.test_run_id,
                    qa_pair_id=qa_pair_id_error,
                    query=self.query,
                    reference_answer=self.reference_answer,
                    collection_name="test_collection",
                    top_k=2,
                    embedding_model=self.embeddings_mock
                )
        
        # Verify evaluation completed despite embedding failure
        self.assertIn('eval_id', result)
        self.assertIn('generated_answer', result)
        self.assertIn('lexical_metrics', result)
        self.assertIn('llm_judged_metrics', result)
        
        # Verify semantic_similarity is not included when embedding fails
        # (The service only includes it in the result if it's not None)
        self.assertNotIn('semantic_similarity', result)
        
        # Verify the evaluation was saved with NULL semantic_similarity
        eval_id = result['eval_id']
        cur = self.db.execute(
            "SELECT semantic_similarity FROM evals WHERE id = ?",
            (eval_id,)
        )
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertIsNone(row[0])


    async def test_error_handling_with_empty_answers(self):
        """Test that empty answers are handled gracefully in semantic similarity calculation."""
        # Test with empty reference answer
        result = await self.service.calculate_semantic_similarity(
            reference_answer="",
            generated_answer="Some answer",
            embedding_model=self.embeddings_mock
        )
        
        # Should return 0.0 for empty answers
        self.assertEqual(result, 0.0)
        
        # Test with empty generated answer
        result = await self.service.calculate_semantic_similarity(
            reference_answer="Some reference",
            generated_answer="",
            embedding_model=self.embeddings_mock
        )
        
        self.assertEqual(result, 0.0)
        
        # Test with both empty
        result = await self.service.calculate_semantic_similarity(
            reference_answer="",
            generated_answer="",
            embedding_model=self.embeddings_mock
        )
        
        self.assertEqual(result, 0.0)

    async def test_error_handling_with_dimension_mismatch(self):
        """Test that dimension mismatch in embeddings is handled gracefully."""
        # Mock embed_texts to return embeddings with different dimensions
        self.embeddings_mock.embed_texts.return_value = [
            [0.1] * 1536,  # Reference embedding
            [0.1] * 768    # Generated embedding with different dimension
        ]
        
        # Should return None when dimension mismatch occurs
        result = await self.service.calculate_semantic_similarity(
            reference_answer=self.reference_answer,
            generated_answer=self.generated_answer,
            embedding_model=self.embeddings_mock
        )
        
        self.assertIsNone(result)


if __name__ == '__main__':
    # Run with asyncio support
    unittest.main()
