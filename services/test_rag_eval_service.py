"""
Unit tests for RAG Eval Service.

Tests the complete pipeline:
1. Context retrieval
2. Answer generation
3. Lexical metric calculation
4. LLM-judged metric calculation
5. Database storage
"""

import json
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import tempfile
import os
from typing import List, Dict, Any

from services.rag_eval_service import RAGEvalService
from db.db import DB
from vectorDb.db import VectorDb
from metrics.rag_evaluator import (
    ContextRelevance,
    Groundedness,
    AnswerRelevance,
    RAGEvaluation,
    Score
)


class TestRAGEvalService(unittest.IsolatedAsyncioTestCase):
    """Test cases for RAGEvalService."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db = DB(self.db_path)

        # Mock vector database
        self.vector_db_mock = Mock(spec=VectorDb)

        # Mock LLM components
        self.llm_mock = Mock()
        self.llm_mock.generate = AsyncMock()
        self.embeddings_mock = Mock()
        self.embeddings_mock.embed_text = AsyncMock()

        # Create service instance
        self.service = RAGEvalService(
            db=self.db,
            vector_db=self.vector_db_mock,
            llm=self.llm_mock,
            embeddings=self.embeddings_mock
        )

        # Mock retrieved contexts
        self.mock_contexts = [
            {
                'content': 'Context 1 about healthy eating',
                'chunk_id': 'chunk_1',
                'distance': 0.1,
                'metadata': {'source': 'doc1'}
            },
            {
                'content': 'Context 2 about exercise benefits',
                'chunk_id': 'chunk_2',
                'distance': 0.2,
                'metadata': {'source': 'doc2'}
            }
        ]

        # Mock generated answer
        self.mock_answer = "Regular exercise improves cardiovascular health and mental well-being."

        # Mock metrics
        self.mock_lexical_metrics = {
            'bleu': 0.8,
            'rouge_l': 0.75,
            'rouge_l_precision': 0.78,
            'rouge_l_recall': 0.72,
            'squad_em': 0.0,
            'squad_token_f1': 0.85,
            'content_f1': 0.82,
            'lexical_aggregate': 0.77
        }

        self.mock_llm_judged_metrics = {
            'answer_relevance': 2.5,
            'context_relevance': 2.8,
            'groundedness': 3.0,
            'llm_judged_overall': 2.77
        }

        self.mock_llm_judged_reasoning = {
            'answer_relevance': 'Answer fully covers query.',
            'context_relevance': 'Retrieved contexts align with the question.',
            'groundedness': 'All claims supported.',
            'context_relevance_per_context': [3.0, 2.5],
            'groundedness_supported_claims': 4,
            'groundedness_total_claims': 4
        }

    async def asyncTearDown(self):
        """Clean up test fixtures."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    async def test_retrieve_contexts(self):
        """Test context retrieval from vector database."""
        # Setup mocks
        self.embeddings_mock.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.vector_db_mock.search_similar.return_value = self.mock_contexts

        # Execute
        result = await self.service.retrieve_contexts(
            query="What are the benefits of exercise?",
            collection_name="test_collection",
            top_k=2
        )

        # Assert
        self.embeddings_mock.embed_text.assert_called_once_with("What are the benefits of exercise?")
        self.vector_db_mock.search_similar.assert_called_once_with(
            collection_name="test_collection",
            query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            top_k=2
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['content'], 'Context 1 about healthy eating')
        self.assertEqual(result[0]['chunk_id'], 'chunk_1')
        self.assertEqual(result[1]['chunk_id'], 'chunk_2')

    async def test_generate_answer(self):
        """Test answer generation with LLM."""
        # Setup mocks
        self.llm_mock.generate.return_value = self.mock_answer

        # Execute
        result = await self.service.generate_answer(
            query="What are exercise benefits?",
            contexts=self.mock_contexts
        )

        # Assert
        self.assertEqual(result, self.mock_answer)

        # Check that generate was called with correct messages
        self.llm_mock.generate.assert_called_once()
        call_args = self.llm_mock.generate.call_args[0][0]  # First positional argument

        # Verify system message
        self.assertIn("You are a helpful assistant", call_args[0]['content'])

        # Verify user message contains contexts and query
        user_content = call_args[1]['content']
        self.assertIn("Retrieved Contexts:", user_content)
        self.assertIn("Context 1: Context 1 about healthy eating", user_content)
        self.assertIn("Context 2: Context 2 about exercise benefits", user_content)
        self.assertIn("Question: What are exercise benefits?", user_content)

    async def test_generate_answer_with_custom_prompt(self):
        """Test answer generation with custom prompt template."""
        # Setup mocks
        self.llm_mock.generate.return_value = self.mock_answer

        custom_template = "Custom: {query} using {contexts}"
        expected_prompt = f"Custom: What are exercise benefits? using Context 1: Context 1 about healthy eating\n\nContext 2: Context 2 about exercise benefits"

        # Execute
        result = await self.service.generate_answer(
            query="What are exercise benefits?",
            contexts=self.mock_contexts,
            prompt_template=custom_template
        )

        # Assert
        self.assertEqual(result, self.mock_answer)

        # Check that custom template was used
        user_content = self.llm_mock.generate.call_args[0][0][1]['content']
        self.assertEqual(user_content, expected_prompt)

    async def test_calculate_lexical_metrics(self):
        """Test lexical metric calculation."""
        with patch('services.rag_eval_service.score_texts', return_value=self.mock_lexical_metrics):
            # Execute
            result = self.service.calculate_lexical_metrics(
                generated_answer=self.mock_answer,
                reference_answer="Exercise benefits include improved cardiovascular health."
            )

            # Assert
            self.assertEqual(result, self.mock_lexical_metrics)
            self.assertIsInstance(result, dict)
            self.assertIn('bleu', result)
            self.assertIn('rouge_l', result)

    async def test_calculate_llm_judged_metrics(self):
        """Test LLM-judged metric calculation."""
        mock_evaluation = RAGEvaluation(
            context_relevance=ContextRelevance(
                explanation="Contexts closely match the query.",
                score=Score.EXCELLENT,
                per_context_scores=[3.0, 2.5]
            ),
            groundedness=Groundedness(
                explanation="All claims grounded in evidence.",
                score=Score.EXCELLENT,
                supported_claims=5,
                total_claims=5
            ),
            answer_relevance=AnswerRelevance(
                explanation="Answer addresses all aspects.",
                score=Score.GOOD
            ),
            overall_score=2.67
        )

        with patch('services.rag_eval_service.evaluate_rag', return_value=mock_evaluation):
            # Execute
            result = await self.service.calculate_llm_judged_metrics(
                query="What are exercise benefits?",
                contexts=["Context 1", "Context 2"],
                answer=self.mock_answer,
                model="gpt-4o"
            )

            # Assert
            expected_scores = {
                'answer_relevance': 2.0,
                'context_relevance': 3.0,
                'groundedness': 3.0,
                'llm_judged_overall': 2.67
            }
            self.assertEqual(result['scores'], expected_scores)
            self.assertEqual(result['reasoning']['answer_relevance'], "Answer addresses all aspects.")
            self.assertEqual(result['reasoning']['context_relevance'], "Contexts closely match the query.")
            self.assertEqual(result['reasoning']['groundedness'], "All claims grounded in evidence.")
            self.assertEqual(result['reasoning']['context_relevance_per_context'], [3.0, 2.5])
            self.assertEqual(result['reasoning']['groundedness_supported_claims'], 5)
            self.assertEqual(result['reasoning']['groundedness_total_claims'], 5)

    def test_save_evaluation_to_db(self):
        """Test saving evaluation results to database."""
        eval_id = self.service.save_evaluation_to_db(
            test_run_id="test_run_123",
            qa_pair_id="qa_123",
            generated_answer=self.mock_answer,
            lexical_metrics=self.mock_lexical_metrics,
            llm_judged_metrics=self.mock_llm_judged_metrics,
            llm_judged_reasoning=self.mock_llm_judged_reasoning,
            chunk_ids=["chunk_1", "chunk_2"]
        )

        # Verify evaluation was saved
        self.assertIsInstance(eval_id, str)
        self.assertTrue(len(eval_id) > 0)

        # Query the database to verify
        cur = self.db.execute(
            "SELECT * FROM evals WHERE id = ?",
            (eval_id,)
        )
        row = cur.fetchone()

        # Check that all fields were saved correctly
        self.assertIsNotNone(row)
        self.assertEqual(row[0], eval_id)  # id
        self.assertEqual(row[1], "test_run_123")  # test_run_id
        self.assertEqual(row[2], "qa_123")  # qa_pair_id
        self.assertEqual(row[3], 0.8)  # bleu
        self.assertEqual(row[14], 2.77)  # llm_judged_overall
        self.assertEqual(row[15], self.mock_answer)  # answer
        self.assertEqual(row[16], self.mock_llm_judged_reasoning['answer_relevance'])
        self.assertEqual(row[17], self.mock_llm_judged_reasoning['context_relevance'])
        self.assertEqual(row[18], self.mock_llm_judged_reasoning['groundedness'])
        self.assertEqual(
            json.loads(row[19]),
            self.mock_llm_judged_reasoning['context_relevance_per_context']
        )
        self.assertEqual(row[20], self.mock_llm_judged_reasoning['groundedness_supported_claims'])
        self.assertEqual(row[21], self.mock_llm_judged_reasoning['groundedness_total_claims'])

    async def test_generate_and_evaluate(self):
        """Test the complete pipeline: generate and evaluate."""
        self.embeddings_mock.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.vector_db_mock.search_similar.return_value = self.mock_contexts
        self.llm_mock.generate.return_value = self.mock_answer

        with patch('services.rag_eval_service.score_texts', return_value=self.mock_lexical_metrics):
            mock_evaluation = RAGEvaluation(
                context_relevance=ContextRelevance(
                    explanation="Strongly relevant contexts.",
                    score=Score.EXCELLENT,
                    per_context_scores=[3.0, 2.5]
                ),
                groundedness=Groundedness(
                    explanation="Claims are grounded.",
                    score=Score.EXCELLENT,
                    supported_claims=4,
                    total_claims=4
                ),
                answer_relevance=AnswerRelevance(
                    explanation="Answer covers the query.",
                    score=Score.GOOD
                ),
                overall_score=2.67
            )

            with patch('services.rag_eval_service.evaluate_rag', return_value=mock_evaluation):
                result = await self.service.generate_and_evaluate(
                    test_run_id="test_run_123",
                    qa_pair_id="qa_123",
                    query="What are the benefits of exercise?",
                    reference_answer="Exercise improves health.",
                    collection_name="test_collection",
                    top_k=2
                )

                self.assertIn('eval_id', result)
                self.assertEqual(result['generated_answer'], self.mock_answer)
                self.assertEqual(result['lexical_metrics'], self.mock_lexical_metrics)
                self.assertIn('llm_judged_metrics', result)
                self.assertIn('llm_judged_reasoning', result)
                self.assertIn('contexts', result)
                self.assertEqual(result['llm_judged_metrics']['answer_relevance'], 2.0)
                self.assertEqual(result['llm_judged_reasoning']['answer_relevance'], "Answer covers the query.")

    async def test_batch_evaluate(self):
        """Test batch evaluation of multiple QA pairs."""
        # Setup mocks
        self.embeddings_mock.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.vector_db_mock.search_similar.return_value = self.mock_contexts
        self.llm_mock.generate.return_value = self.mock_answer

        qa_pairs = [
            {"id": "qa_1", "question": "Question 1?", "answer": "Answer 1"},
            {"id": "qa_2", "question": "Question 2?", "answer": "Answer 2"}
        ]

        with patch('services.rag_eval_service.score_texts', return_value=self.mock_lexical_metrics):
            mock_evaluation = RAGEvaluation(
                context_relevance=ContextRelevance(
                    explanation="Contexts relevant.",
                    score=Score.EXCELLENT,
                    per_context_scores=[3.0]
                ),
                groundedness=Groundedness(
                    explanation="Grounded claims.",
                    score=Score.EXCELLENT,
                    supported_claims=2,
                    total_claims=2
                ),
                answer_relevance=AnswerRelevance(
                    explanation="Answers the question.",
                    score=Score.GOOD
                ),
                overall_score=2.67
            )

            with patch('services.rag_eval_service.evaluate_rag', return_value=mock_evaluation):
                results = await self.service.batch_evaluate(
                    test_run_id="test_run_batch",
                    qa_pairs=qa_pairs,
                    collection_name="test_collection",
                    top_k=2
                )

                self.assertEqual(len(results), 2)
                for result in results:
                    self.assertEqual(result['status'], 'success')
                    self.assertIn('result', result)
                    self.assertEqual(result['result']['generated_answer'], self.mock_answer)
                    self.assertIn('llm_judged_reasoning', result['result'])

    async def test_retrieve_contexts_empty_results(self):
        """Test context retrieval when no contexts are found."""
        # Setup mocks
        self.embeddings_mock.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.vector_db_mock.search_similar.return_value = []  # Empty results

        # Execute
        result = await self.service.retrieve_contexts(
            query="What are the benefits of exercise?",
            collection_name="test_collection",
            top_k=10
        )

        # Assert
        self.assertEqual(len(result), 0)

    async def test_generate_and_evaluate_no_contexts_error(self):
        """Test that generate_and_evaluate raises error when no contexts found."""
        # Setup mocks to return empty contexts
        self.embeddings_mock.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.vector_db_mock.search_similar.return_value = []

        # Execute and assert raises error
        with self.assertRaises(ValueError):
            await self.service.generate_and_evaluate(
                test_run_id="test_run_123",
                qa_pair_id="qa_123",
                query="What are the benefits of exercise?",
                reference_answer="Exercise improves health.",
                collection_name="test_collection",
                top_k=10
            )


if __name__ == '__main__':
    # Run with asyncio support
    asyncio.run(unittest.main())
