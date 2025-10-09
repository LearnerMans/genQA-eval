from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime

class PromptRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all prompts from the database."""
        cur = self.db.execute("SELECT id, test_id, name, prompt, created_at, updated_at FROM prompts")
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "test_id": row[1],
                "name": row[2],
                "prompt": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
            for row in rows
        ]

    def get_by_test_id(self, test_id: str) -> List[Dict[str, Any]]:
        """Retrieve all prompts for a given test_id."""
        cur = self.db.execute(
            "SELECT id, test_id, name, prompt, created_at, updated_at FROM prompts WHERE test_id = ?",
            (test_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "test_id": row[1],
                "name": row[2],
                "prompt": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
            for row in rows
        ]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt in the database."""
        prompt_id = str(uuid.uuid4())
        test_id = data.get("test_id")
        name = data.get("name")
        prompt = data.get("prompt")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO prompts (id, test_id, name, prompt, created_at) VALUES (?, ?, ?, ?, ?)",
            (prompt_id, test_id, name, prompt, created_at)
        )

        return {
            "id": prompt_id,
            "test_id": test_id,
            "name": name,
            "prompt": prompt,
            "created_at": created_at,
            "updated_at": None
        }

    def delete_by_id(self, prompt_id: str) -> bool:
        """Delete a prompt by its ID. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        return cur.rowcount > 0
