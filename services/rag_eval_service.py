"""
RAG Answer Generation and Evaluation Service.

This service handles the complete pipeline:
1. Retrieve relevant contexts from vector database
2. Generate answer using LLM
3. Calculate lexical metrics (BLEU, ROUGE, etc.)
4. Calculate LLM-judged metrics (answer relevance, context relevance, groundedness)
5. Store all results in the database
6. Generate comprehensive evaluation reports
"""

import asyncio
import inspect
import json
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
import uuid
from datetime import datetime
from statistics import mean

from db.db import DB
from vectorDb.db import VectorDb
from llm.openai_llm import OpenAILLM
from llm.openai_embeddings import OpenAIEmbeddings
from metrics.text_metrics import score_texts
from metrics.rag_evaluator import (
    evaluate_rag,
    score_to_numeric,
    calculate_overall_score,
    format_evaluation_report
)

logger = logging.getLogger(__name__)


class RAGEvalService:
    """Service for RAG answer generation and comprehensive evaluation."""

    async def _emit_progress(
        self,
        callback: Optional[Callable[[Dict[str, Any]], Awaitable[None] | None]],
        event: Dict[str, Any]
    ) -> None:
        """Safely invoke a progress callback if provided."""
        if not callback:
            return

        try:
            result = callback(event)
            if inspect.isawaitable(result):
                await result
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Progress callback raised an error: %s", exc)

    def __init__(
        self,
        db: DB,
        vector_db: VectorDb,
        llm: Optional[OpenAILLM] = None,
        embeddings: Optional[OpenAIEmbeddings] = None
    ):
        """
        Initialize the RAG evaluation service.

        Args:
            db: Database instance
            vector_db: Vector database instance
            llm: LLM instance (defaults to OpenAI GPT-4o)
            embeddings: Embeddings instance (defaults to OpenAI text-embedding-3-large)
        """
        self.db = db
        self.vector_db = vector_db
        self.llm = llm or OpenAILLM(model_name='openai_4o')
        self.embeddings = embeddings or OpenAIEmbeddings(model_name='openai_text_embedding_large_3')

    async def retrieve_contexts(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant contexts from vector database.

        Args:
            query: User's question
            collection_name: Name of the vector collection
            top_k: Number of contexts to retrieve

        Returns:
            List of retrieved context dictionaries with content and metadata
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(query)

            # Search for similar contexts
            results = self.vector_db.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=top_k
            )

            # Extract content from metadata
            contexts = []
            for result in results:
                # Assuming metadata contains 'content' field
                content = result['metadata'].get('content', '')
                if content:
                    contexts.append({
                        'content': content,
                        'chunk_id': result['id'],
                        'distance': result['distance'],
                        'metadata': result['metadata']
                    })

            return contexts

        except Exception as e:
            logger.error(f"Error retrieving contexts: {e}")
            raise

    async def generate_answer(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        prompt_template: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate answer using LLM and retrieved contexts.

        Args:
            query: User's question
            contexts: List of retrieved context dictionaries
            prompt_template: Optional custom prompt template
            temperature: LLM temperature (default 0.0)

        Returns:
            Generated answer string
        """
        try:
            # Default prompt template
            if not prompt_template:
                prompt_template = """You are a helpful assistant. Answer the user's question based on the provided contexts.

Retrieved Contexts:
{contexts}

Question: {query}

Provide a clear, accurate answer based on the contexts above."""

            # Format contexts
            contexts_text = "\n\n".join([
                f"Context {i+1}: {ctx['content']}"
                for i, ctx in enumerate(contexts)
            ])

            # Format prompt (support legacy {contexts} and UI-promoted {chunks})
            template_values = {
                "contexts": contexts_text,
                "chunks": contexts_text,
                "query": query,
                "question": query
            }
            normalized_template = (
                prompt_template
                .replace("{{chunks}}", "{chunks}")
                .replace("{{contexts}}", "{contexts}")
                .replace("{{query}}", "{query}")
                .replace("{{question}}", "{question}")
            )

            try:
                prompt = normalized_template.format(**template_values)
            except KeyError as missing_key:
                available = ", ".join(sorted(template_values.keys()))
                logger.error(
                    "Error generating answer: prompt template missing key '%s'. Available placeholders: %s",
                    missing_key, available
                )
                raise KeyError(
                    f"Prompt template missing {{{missing_key}}}. Available placeholders: {available}"
                ) from missing_key

            # Generate answer
            messages = [
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided contexts."},
                {"role": "user", "content": prompt}
            ]

            answer = await self.llm.generate(messages, temperature=temperature)
            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise

    def calculate_lexical_metrics(
        self,
        generated_answer: str,
        reference_answer: str
    ) -> Dict[str, float]:
        """
        Calculate all lexical metrics.

        Args:
            generated_answer: LLM-generated answer
            reference_answer: Ground truth reference answer

        Returns:
            Dictionary with all lexical metric scores
        """
        try:
            results = score_texts(
                candidate=generated_answer,
                references=reference_answer,
                max_n=4,
                smooth=True
            )

            return {
                'bleu': results['BLEU'],
                'rouge_l': results['ROUGE_L'],
                'rouge_l_precision': results['ROUGE_L_precision'],
                'rouge_l_recall': results['ROUGE_L_recall'],
                'squad_em': results['SQuAD_EM'],
                'squad_token_f1': results['SQuAD_token_F1'],
                'content_f1': results['ContentF1'],
                'lexical_aggregate': results['Aggregate']
            }

        except Exception as e:
            logger.error(f"Error calculating lexical metrics: {e}")
            raise

    async def calculate_llm_judged_metrics(
        self,
        query: str,
        contexts: List[str],
        answer: str,
        model: str = "gpt-5"
    ) -> Dict[str, Any]:
        """
        Calculate LLM-judged metrics using GPT-5 and capture reasoning.

        Args:
            query: User's question
            contexts: List of context strings
            answer: Generated answer
            model: Model to use for evaluation (default gpt-5)

        Returns:
            Dictionary containing numeric scores and reasoning details
        """
        try:
            # Run evaluation synchronously (evaluate_rag is not async)
            evaluation = await asyncio.to_thread(
                evaluate_rag,
                query=query,
                contexts=contexts,
                answer=answer,
                model=model
            )

            scores = {
                'answer_relevance': score_to_numeric(evaluation.answer_relevance.score),
                'context_relevance': score_to_numeric(evaluation.context_relevance.score),
                'groundedness': score_to_numeric(evaluation.groundedness.score),
                'llm_judged_overall': evaluation.overall_score
            }

            reasoning = {
                'answer_relevance': evaluation.answer_relevance.explanation,
                'context_relevance': evaluation.context_relevance.explanation,
                'groundedness': evaluation.groundedness.explanation,
                'context_relevance_per_context': evaluation.context_relevance.per_context_scores or [],
                'groundedness_supported_claims': evaluation.groundedness.supported_claims,
                'groundedness_total_claims': evaluation.groundedness.total_claims
            }

            return {
                'scores': scores,
                'reasoning': reasoning
            }

        except Exception as e:
            logger.error(f"Error calculating LLM-judged metrics: {e}")
            raise

    def save_evaluation_to_db(
        self,
        test_run_id: str,
        qa_pair_id: str,
        generated_answer: str,
        lexical_metrics: Dict[str, float],
        llm_judged_metrics: Dict[str, float],
        llm_judged_reasoning: Optional[Dict[str, Any]] = None,
        chunk_ids: Optional[List[str]] = None
    ) -> str:
        """
        Save evaluation results to database.

        Args:
            test_run_id: ID of the test run
            qa_pair_id: ID of the QA pair
            generated_answer: The generated answer text
            lexical_metrics: Dictionary of lexical metric scores
            llm_judged_metrics: Dictionary of LLM-judged metric scores
            llm_judged_reasoning: Optional dictionary containing reasoning details
            chunk_ids: Optional list of chunk IDs used for retrieval

        Returns:
            ID of the created evaluation record
        """
        try:
            # Overwrite semantics: ensure only one eval per (test_run_id, qa_pair_id)
            # 1) Delete existing eval(s) for this pair (will cascade delete eval_chunks)
            self.db.execute(
                "DELETE FROM evals WHERE test_run_id = ? AND qa_pair_id = ?",
                (test_run_id, qa_pair_id)
            )

            reasoning = llm_judged_reasoning or {}
            context_per_context = reasoning.get('context_relevance_per_context')
            if context_per_context is not None:
                try:
                    context_per_context_payload = json.dumps(context_per_context)
                except (TypeError, ValueError):
                    logger.warning("Failed to serialize per-context scores; defaulting to empty list")
                    context_per_context_payload = json.dumps([])
            else:
                context_per_context_payload = None

            # 2) Insert fresh row
            eval_id = str(uuid.uuid4())
            self.db.execute(
                """
                INSERT INTO evals (
                    id, test_run_id, qa_pair_id,
                    bleu, rouge_l, rouge_l_precision, rouge_l_recall,
                    squad_em, squad_token_f1, content_f1, lexical_aggregate,
                    answer_relevance, context_relevance, groundedness, llm_judged_overall,
                    answer, answer_relevance_reasoning, context_relevance_reasoning,
                    groundedness_reasoning, context_relevance_per_context,
                    groundedness_supported_claims, groundedness_total_claims
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eval_id,
                    test_run_id,
                    qa_pair_id,
                    lexical_metrics['bleu'],
                    lexical_metrics['rouge_l'],
                    lexical_metrics['rouge_l_precision'],
                    lexical_metrics['rouge_l_recall'],
                    lexical_metrics['squad_em'],
                    lexical_metrics['squad_token_f1'],
                    lexical_metrics['content_f1'],
                    lexical_metrics['lexical_aggregate'],
                    llm_judged_metrics['answer_relevance'],
                    llm_judged_metrics['context_relevance'],
                    llm_judged_metrics['groundedness'],
                    llm_judged_metrics['llm_judged_overall'],
                    generated_answer,
                    reasoning.get('answer_relevance'),
                    reasoning.get('context_relevance'),
                    reasoning.get('groundedness'),
                    context_per_context_payload,
                    reasoning.get('groundedness_supported_claims'),
                    reasoning.get('groundedness_total_claims')
                )
            )

            # 3) Link chunks for this new eval
            if chunk_ids:
                for chunk_id in chunk_ids:
                    self.db.execute(
                        "INSERT INTO eval_chunks (eval_id, chunk_id) VALUES (?, ?)",
                        (eval_id, chunk_id)
                    )

            logger.info(f"Saved evaluation {eval_id} for test run {test_run_id}")
            return eval_id

        except Exception as e:
            logger.error(f"Error saving evaluation to database: {e}")
            raise

    async def generate_and_evaluate(
        self,
        test_run_id: str,
        qa_pair_id: str,
        query: str,
        reference_answer: str,
        collection_name: str,
        top_k: int = 10,
        prompt_template: Optional[str] = None,
        temperature: float = 0.7,
        eval_model: str = "gpt-5",
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None] | None]] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Generate answer and evaluate with all metrics.

        Args:
            test_run_id: ID of the test run
            qa_pair_id: ID of the QA pair
            query: User's question
            reference_answer: Ground truth answer
            collection_name: Vector collection name
            top_k: Number of contexts to retrieve
            prompt_template: Optional custom prompt template
            temperature: LLM generation temperature
            eval_model: Model to use for LLM-judged evaluation (default gpt-5)
            progress_callback: Optional callable invoked with progress events

        Returns:
            Dictionary containing all results:
            - eval_id: ID of the evaluation record
            - generated_answer: Generated answer text
            - contexts: Retrieved contexts
            - lexical_metrics: All lexical metric scores
            - llm_judged_metrics: All LLM-judged metric scores
        """
        try:
            await self._emit_progress(progress_callback, {
                "stage": "started",
                "status": "running",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id
            })

            logger.info(f"Starting evaluation for QA pair {qa_pair_id}")

            # Step 1: Retrieve contexts
            logger.info("Retrieving contexts...")
            context_results = await self.retrieve_contexts(
                query=query,
                collection_name=collection_name,
                top_k=top_k
            )

            await self._emit_progress(progress_callback, {
                "stage": "contexts_retrieved",
                "status": "running",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id,
                "data": {
                    "context_count": len(context_results)
                }
            })

            if not context_results:
                await self._emit_progress(progress_callback, {
                    "stage": "contexts_retrieved",
                    "status": "failed",
                    "test_run_id": test_run_id,
                    "qa_pair_id": qa_pair_id,
                    "error": f"No contexts found in collection '{collection_name}'"
                })
                raise ValueError(f"No contexts found in collection '{collection_name}'")

            # Step 2: Generate answer
            logger.info("Generating answer...")
            generated_answer = await self.generate_answer(
                query=query,
                contexts=context_results,
                prompt_template=prompt_template,
                temperature=temperature
            )

            await self._emit_progress(progress_callback, {
                "stage": "answer_generated",
                "status": "running",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id
            })

            # Step 3: Calculate lexical metrics
            logger.info("Calculating lexical metrics...")
            lexical_metrics = self.calculate_lexical_metrics(
                generated_answer=generated_answer,
                reference_answer=reference_answer
            )

            await self._emit_progress(progress_callback, {
                "stage": "lexical_metrics_calculated",
                "status": "running",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id,
                "data": lexical_metrics
            })

            # Step 4: Calculate LLM-judged metrics
            logger.info("Calculating LLM-judged metrics...")
            context_texts = [ctx['content'] for ctx in context_results]
            llm_judged_result = await self.calculate_llm_judged_metrics(
                query=query,
                contexts=context_texts,
                answer=generated_answer,
                model=eval_model
            )
            llm_judged_metrics = llm_judged_result['scores']
            llm_judged_reasoning = llm_judged_result['reasoning']

            await self._emit_progress(progress_callback, {
                "stage": "llm_metrics_calculated",
                "status": "running",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id,
                "data": llm_judged_metrics
            })

            # Step 5: Save to database
            logger.info("Saving results to database...")
            chunk_ids = [ctx['chunk_id'] for ctx in context_results]
            eval_id = self.save_evaluation_to_db(
                test_run_id=test_run_id,
                qa_pair_id=qa_pair_id,
                generated_answer=generated_answer,
                lexical_metrics=lexical_metrics,
                llm_judged_metrics=llm_judged_metrics,
                llm_judged_reasoning=llm_judged_reasoning,
                chunk_ids=chunk_ids
            )

            logger.info(f"Evaluation complete! Eval ID: {eval_id}")

            await self._emit_progress(progress_callback, {
                "stage": "saved",
                "status": "completed",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id,
                "data": {
                    "eval_id": eval_id
                }
            })

            return {
                'eval_id': eval_id,
                'generated_answer': generated_answer,
                'contexts': context_results,
                'lexical_metrics': lexical_metrics,
                'llm_judged_metrics': llm_judged_metrics,
                'llm_judged_reasoning': llm_judged_reasoning
            }

        except Exception as e:
            logger.error(f"Error in generate_and_evaluate: {e}")
            await self._emit_progress(progress_callback, {
                "stage": "failed",
                "status": "failed",
                "test_run_id": test_run_id,
                "qa_pair_id": qa_pair_id,
                "error": str(e)
            })
            raise

    async def batch_evaluate(
        self,
        test_run_id: str,
        qa_pairs: List[Dict[str, Any]],
        collection_name: str,
        top_k: int = 10,
        prompt_template: Optional[str] = None,
        temperature: float = 0.7,
        eval_model: str = "gpt-5"
    ) -> List[Dict[str, Any]]:
        """
        Batch evaluation for multiple QA pairs.

        Args:
            test_run_id: ID of the test run
            qa_pairs: List of QA pair dictionaries with 'id', 'question', 'answer' keys
            collection_name: Vector collection name
            top_k: Number of contexts to retrieve
            prompt_template: Optional custom prompt template
            temperature: LLM generation temperature
            eval_model: Model to use for LLM-judged evaluation (default gpt-5)

        Returns:
            List of evaluation result dictionaries
        """
        results = []

        for i, qa_pair in enumerate(qa_pairs, 1):
            try:
                logger.info(f"Processing QA pair {i}/{len(qa_pairs)}: {qa_pair['id']}")

                result = await self.generate_and_evaluate(
                    test_run_id=test_run_id,
                    qa_pair_id=qa_pair['id'],
                    query=qa_pair['question'],
                    reference_answer=qa_pair['answer'],
                    collection_name=collection_name,
                    top_k=top_k,
                    prompt_template=prompt_template,
                    temperature=temperature,
                    eval_model=eval_model
                )

                results.append({
                    'qa_pair_id': qa_pair['id'],
                    'status': 'success',
                    'result': result
                })

            except Exception as e:
                logger.error(f"Error processing QA pair {qa_pair['id']}: {e}")
                results.append({
                    'qa_pair_id': qa_pair['id'],
                    'status': 'failed',
                    'error': str(e)
                })

        return results
