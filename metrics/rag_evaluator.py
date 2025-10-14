"""
RAG Evaluation using LLM-as-a-Judge with GPT-5.

This module implements the RAG Triad framework for evaluating:
1. Context Relevance - Are retrieved contexts relevant to the query?
2. Groundedness - Is the answer faithful to the contexts?
3. Answer Relevance - Does the answer fully address the query?
"""

from openai import OpenAI
import instructor
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Client will be initialized lazily when needed
_client = None


def _get_client():
    """Get or create the instructor client, loading API key from .env file."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Please add it to your .env file:\n"
                "OPENAI_API_KEY=your-api-key-here"
            )
        _client = instructor.from_openai(OpenAI(api_key=api_key))
    return _client


class Score(str, Enum):
    """Score enum mapping to 0-3 scale."""
    EXCELLENT = "excellent"  # 3
    GOOD = "good"            # 2
    AVERAGE = "average"      # 1
    BAD = "bad"              # 0


class ContextRelevance(BaseModel):
    """Evaluation of context relevance to query."""
    explanation: str = Field(..., description="Step-by-step reasoning about context relevance")
    score: Score
    per_context_scores: List[float] = Field(default_factory=list, description="Individual scores for each context")


class Groundedness(BaseModel):
    """Evaluation of answer faithfulness to contexts."""
    explanation: str = Field(..., description="Analysis of factual faithfulness to context")
    score: Score
    supported_claims: int = Field(..., description="Number of verified claims")
    total_claims: int = Field(..., description="Total claims in answer")


class AnswerRelevance(BaseModel):
    """Evaluation of answer quality and completeness."""
    explanation: str = Field(..., description="Analysis of answer quality and completeness")
    score: Score


class RAGEvaluation(BaseModel):
    """Complete RAG evaluation result."""
    context_relevance: ContextRelevance
    groundedness: Groundedness
    answer_relevance: AnswerRelevance
    overall_score: float = Field(..., description="Overall score from 0-3")


def score_to_numeric(score: Score) -> float:
    """Convert Score enum to numeric value."""
    mapping = {
        Score.BAD: 0.0,
        Score.AVERAGE: 1.0,
        Score.GOOD: 2.0,
        Score.EXCELLENT: 3.0
    }
    return mapping[score]


def evaluate_rag(
    query: str,
    contexts: List[str],
    answer: str,
    model: str = "gpt-5",
    temperature: Optional[float] = None
) -> RAGEvaluation:
    """
    Complete RAG evaluation using the RAG Triad framework with GPT-5.

    Args:
        query: The user's query/question
        contexts: List of retrieved context passages
        answer: The generated answer from the RAG system
        model: OpenAI model to use (default: "gpt-5")
        temperature: Temperature for evaluation (default: 0.0 for deterministic)

    Returns:
        RAGEvaluation object with scores and explanations for all dimensions

    Example:
        >>> result = evaluate_rag(
        ...     query="What are the symptoms of type 2 diabetes?",
        ...     contexts=["Type 2 diabetes symptoms include..."],
        ...     answer="Common symptoms include..."
        ... )
        >>> print(f"Overall Score: {result.overall_score}/3.0")
    """

    prompt = f"""Evaluate this RAG system output across three dimensions using the RAG Triad framework.

Query: {query}

Retrieved Contexts:
{chr(10).join(f"{i+1}. {ctx}" for i, ctx in enumerate(contexts))}

Generated Answer: {answer}

Evaluate step-by-step:

1. CONTEXT RELEVANCE (0-3 scale)
Think step by step: Are the retrieved contexts relevant to answering the query?
Score 0 (bad): No relevance
Score 1 (average): Low relevance, slight connection
Score 2 (good): Medium relevance, partial coverage
Score 3 (excellent): High relevance, can answer query
Rate each context individually, then provide overall assessment.

2. GROUNDEDNESS (0-3 scale)
Think step by step: Is the answer faithful to the contexts?
- Extract all factual claims from the answer
- Verify each claim against the contexts
- Count supported vs unsupported claims
Score 0 (bad): Multiple hallucinations or completely unsupported
Score 1 (average): Some unsupported claims
Score 2 (good): Mostly supported with minor unsupported details
Score 3 (excellent): Fully supported by contexts

3. ANSWER RELEVANCE (0-3 scale)
Think step by step: Does the answer fully address the query?
Score 0 (bad): Doesn't address query or refusal
Score 1 (average): Partially addresses query
Score 2 (good): Mostly addresses query with minor gaps
Score 3 (excellent): Completely addresses query

Provide detailed reasoning for each dimension before scoring. Be critical and strict with ratings.
"""

    client = _get_client()
    request_kwargs = {
        "model": model,
        "response_model": RAGEvaluation,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert RAG system evaluator. Provide thorough, critical assessments with detailed reasoning."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    if temperature is not None:
        request_kwargs["temperature"] = temperature

    evaluation = client.chat.completions.create(**request_kwargs)

    return evaluation


def calculate_overall_score(evaluation: RAGEvaluation) -> float:
    """
    Calculate overall score from individual dimension scores.

    Args:
        evaluation: RAGEvaluation object

    Returns:
        Overall score (0-3 scale)
    """
    scores = [
        score_to_numeric(evaluation.context_relevance.score),
        score_to_numeric(evaluation.groundedness.score),
        score_to_numeric(evaluation.answer_relevance.score)
    ]
    return float(np.mean(scores))


def format_evaluation_report(evaluation: RAGEvaluation) -> str:
    """
    Format evaluation results as a human-readable report.

    Args:
        evaluation: RAGEvaluation object

    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 80)
    report.append("RAG EVALUATION REPORT")
    report.append("=" * 80)
    report.append(f"\nOverall Score: {evaluation.overall_score:.2f}/3.0")
    report.append("\n" + "-" * 80)

    report.append("\n1. CONTEXT RELEVANCE")
    report.append(f"   Score: {evaluation.context_relevance.score.value.upper()} ({score_to_numeric(evaluation.context_relevance.score)}/3.0)")
    report.append(f"   Reasoning: {evaluation.context_relevance.explanation}")
    if evaluation.context_relevance.per_context_scores:
        report.append(f"   Per-context scores: {evaluation.context_relevance.per_context_scores}")

    report.append("\n" + "-" * 80)
    report.append("\n2. GROUNDEDNESS")
    report.append(f"   Score: {evaluation.groundedness.score.value.upper()} ({score_to_numeric(evaluation.groundedness.score)}/3.0)")
    report.append(f"   Claims: {evaluation.groundedness.supported_claims}/{evaluation.groundedness.total_claims} supported")
    report.append(f"   Reasoning: {evaluation.groundedness.explanation}")

    report.append("\n" + "-" * 80)
    report.append("\n3. ANSWER RELEVANCE")
    report.append(f"   Score: {evaluation.answer_relevance.score.value.upper()} ({score_to_numeric(evaluation.answer_relevance.score)}/3.0)")
    report.append(f"   Reasoning: {evaluation.answer_relevance.explanation}")

    report.append("\n" + "=" * 80)

    return "\n".join(report)


# Example usage
if __name__ == "__main__":
    result = evaluate_rag(
        query="What are the symptoms of type 2 diabetes?",
        contexts=[
            "Type 2 diabetes symptoms include increased thirst, frequent urination, increased hunger, unintended weight loss, fatigue, blurred vision, slow-healing sores, and frequent infections.",
            "Type 2 diabetes often develops slowly. Some people have no noticeable symptoms initially.",
            "Regular blood sugar monitoring is important for diabetes management and preventing complications."
        ],
        answer="Common symptoms of type 2 diabetes include increased thirst, frequent urination, fatigue, and blurred vision. Some people may also experience weight loss and slow-healing wounds."
    )

    print(format_evaluation_report(result))
