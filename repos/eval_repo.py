import json

from db.db import DB
from typing import List, Dict, Any


class EvalRepo:
    def __init__(self, db: DB):
        self.db = db

    def get_by_test_run_id(self, test_run_id: str) -> List[Dict[str, Any]]:
        cur = self.db.execute(
            """
            SELECT 
                e.id,
                e.test_run_id,
                e.qa_pair_id,
                e.bleu,
                -- ensure compatibility: expose rouge_l as rouge for existing UI
                e.rouge_l AS rouge,
                e.answer_relevance,
                e.context_relevance,
                e.groundedness,
                e.answer
            FROM evals e
            WHERE e.test_run_id = ?
            ORDER BY e.rowid ASC
            """,
            (test_run_id,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "test_run_id": row[1],
                "qa_pair_id": row[2],
                "bleu": row[3],
                "rouge": row[4],
                "answer_relevance": row[5],
                "context_relevance": row[6],
                "groundedness": row[7],
                "answer": row[8],
            }
            for row in rows
        ]

    def get_full_by_run_and_qa(self, test_run_id: str, qa_pair_id: str) -> Dict[str, Any] | None:
        """Return full evaluation record for a given run and QA pair (all metrics)."""
        cur = self.db.execute(
            """
            SELECT 
                id,
                test_run_id,
                qa_pair_id,
                bleu,
                rouge_l,
                rouge_l_precision,
                rouge_l_recall,
                squad_em,
                squad_token_f1,
                content_f1,
                lexical_aggregate,
                answer_relevance,
                context_relevance,
                groundedness,
                llm_judged_overall,
                answer,
                answer_relevance_reasoning,
                context_relevance_reasoning,
                groundedness_reasoning,
                context_relevance_per_context,
                groundedness_supported_claims,
                groundedness_total_claims
            FROM evals
            WHERE test_run_id = ? AND qa_pair_id = ?
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (test_run_id, qa_pair_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        per_context_scores_raw = row[19]
        try:
            per_context_scores = json.loads(per_context_scores_raw) if per_context_scores_raw else []
        except json.JSONDecodeError:
            per_context_scores = []

        return {
            "id": row[0],
            "test_run_id": row[1],
            "qa_pair_id": row[2],
            "bleu": row[3],
            "rouge_l": row[4],
            "rouge_l_precision": row[5],
            "rouge_l_recall": row[6],
            "squad_em": row[7],
            "squad_token_f1": row[8],
            "content_f1": row[9],
            "lexical_aggregate": row[10],
            "answer_relevance": row[11],
            "context_relevance": row[12],
            "groundedness": row[13],
            "llm_judged_overall": row[14],
            "answer": row[15],
            "answer_relevance_reasoning": row[16],
            "context_relevance_reasoning": row[17],
            "groundedness_reasoning": row[18],
            "context_relevance_per_context": per_context_scores,
            "groundedness_supported_claims": row[20],
            "groundedness_total_claims": row[21],
        }

    def get_chunks_by_eval_id(self, eval_id: str) -> List[Dict[str, Any]]:
        """Return chunk contents linked to an evaluation, with basic source info."""
        cur = self.db.execute(
            """
            SELECT 
                c.id,
                c.content,
                c.chunk_index,
                COALESCE(s.type, ''),
                COALESCE(s.path_or_link, '')
            FROM eval_chunks ec
            JOIN chunks c ON c.id = ec.chunk_id
            LEFT JOIN sources s ON s.id = c.source_id
            WHERE ec.eval_id = ?
            ORDER BY c.chunk_index ASC, c.id ASC
            """,
            (eval_id,),
        )
        rows = cur.fetchall()
        return [
            {
                "chunk_id": row[0],
                "content": row[1],
                "chunk_index": row[2],
                "source_type": row[3] or None,
                "source": row[4] or None,
            }
            for row in rows
        ]
