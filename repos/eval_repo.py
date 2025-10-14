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
                answer
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
        }
