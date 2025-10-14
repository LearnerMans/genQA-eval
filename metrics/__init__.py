"""
Metrics package for text evaluation in RAG systems.

This package provides implementations of common NLG evaluation metrics
including BLEU, ROUGE-L, SQuAD EM/F1, and content-based metrics, as well as
LLM-as-a-Judge evaluation using the RAG Triad framework.
"""

from .text_metrics import (
    bleu,
    rouge_l,
    squad_em,
    squad_token_f1,
    content_f1,
    score_texts,
)

from .rag_evaluator import (
    evaluate_rag,
    RAGEvaluation,
    ContextRelevance,
    Groundedness,
    AnswerRelevance,
    Score,
    score_to_numeric,
    calculate_overall_score,
    format_evaluation_report,
)

__all__ = [
    # Text metrics
    "bleu",
    "rouge_l",
    "squad_em",
    "squad_token_f1",
    "content_f1",
    "score_texts",
    # RAG evaluation
    "evaluate_rag",
    "RAGEvaluation",
    "ContextRelevance",
    "Groundedness",
    "AnswerRelevance",
    "Score",
    "score_to_numeric",
    "calculate_overall_score",
    "format_evaluation_report",
]
