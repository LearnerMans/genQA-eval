from db.db import DB
from typing import List, Dict, Any


class EvalRepo:
    def __init__(self, db: DB):
        self.db = db

    def get_by_test_run_id(self, test_run_id: str) -> List[Dict[str, Any]]:
        cur = self.db.execute(
            """
            SELECT e.id, e.test_run_id, e.qa_pair_id, e.bleu, e.rouge, e.answer_relevance, e.context_relevance, e.groundedness, e.answer
            FROM evals e
            WHERE e.test_run_id = ?
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
