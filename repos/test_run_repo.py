from db.db import DB
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class TestRunRepo:
    def __init__(self, db: DB):
        self.db = db

    def get_by_test_id(self, test_id: str) -> List[Dict[str, Any]]:
        cur = self.db.execute(
            "SELECT id, test_id, config_id, COALESCE(prompt_id, '') FROM test_runs WHERE test_id = ?",
            (test_id,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "test_id": row[1],
                "config_id": row[2],
                "prompt_id": row[3] or None,
            }
            for row in rows
        ]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test run.

        Expects data with keys: test_id, config_id, prompt_id (optional but recommended).
        """
        run_id = str(uuid.uuid4())
        test_id = data["test_id"]
        config_id = data["config_id"]
        prompt_id = data.get("prompt_id")

        self.db.execute(
            "INSERT INTO test_runs (id, test_id, config_id, prompt_id) VALUES (?, ?, ?, ?)",
            (run_id, test_id, config_id, prompt_id),
        )

        return {
            "id": run_id,
            "test_id": test_id,
            "config_id": config_id,
            "prompt_id": prompt_id,
        }

