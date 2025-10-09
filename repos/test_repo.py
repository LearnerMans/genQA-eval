from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime

class TestRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all tests from the database."""
        cur = self.db.execute("SELECT id, project_id, name, created_at, updated_at FROM tests")
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            }
            for row in rows
        ]

    def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all tests for a given project_id."""
        cur = self.db.execute(
            "SELECT id, project_id, name, created_at, updated_at FROM tests WHERE project_id = ?",
            (project_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            }
            for row in rows
        ]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test in the database."""
        test_id = str(uuid.uuid4())
        project_id = data.get("project_id")
        name = data.get("name")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO tests (id, project_id, name, created_at) VALUES (?, ?, ?, ?)",
            (test_id, project_id, name, created_at)
        )

        return {
            "id": test_id,
            "project_id": project_id,
            "name": name,
            "created_at": created_at,
            "updated_at": None
        }

    def delete_by_id(self, test_id: str) -> bool:
        """Delete a test by its ID. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM tests WHERE id = ?", (test_id,))
        return cur.rowcount > 0
