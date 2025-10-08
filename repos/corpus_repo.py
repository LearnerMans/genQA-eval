from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime

class CorpusRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_by_project_id(self, project_id: str) -> Dict[str, Any] | None:
        """Retrieve corpus by project_id. Returns None if not found."""
        cur = self.db.execute(
            "SELECT id, project_id, name, created_at, updated_at FROM corpus WHERE project_id = ?",
            (project_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "project_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            }
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all corpus entries from the database."""
        cur = self.db.execute("SELECT id, project_id, name, created_at, updated_at FROM corpus")
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
        """Create a new corpus in the database."""
        corpus_id = str(uuid.uuid4())
        project_id = data.get("project_id")
        name = data.get("name", "Default Corpus")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO corpus (id, project_id, name, created_at) VALUES (?, ?, ?, ?)",
            (corpus_id, project_id, name, created_at)
        )

        return {
            "id": corpus_id,
            "project_id": project_id,
            "name": name,
            "created_at": created_at,
            "updated_at": None
        }

    def delete_by_id(self, corpus_id: str) -> bool:
        """Delete a corpus by its ID. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM corpus WHERE id = ?", (corpus_id,))
        return cur.rowcount > 0

    def delete_by_project_id(self, project_id: str) -> bool:
        """Delete corpus by project_id. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM corpus WHERE project_id = ?", (project_id,))
        return cur.rowcount > 0

    def update(self, corpus_id: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Update corpus by ID. Returns updated corpus data or None if not found."""
        update_fields = []
        params = []

        if "name" in data:
            update_fields.append("name = ?")
            params.append(data["name"])

        if not update_fields:
            return None

        update_fields.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(corpus_id)

        query = f"UPDATE corpus SET {', '.join(update_fields)} WHERE id = ?"
        cur = self.db.execute(query, tuple(params))

        if cur.rowcount > 0:
            # Return updated corpus
            return self.get_by_id(corpus_id)
        return None

    def get_by_id(self, corpus_id: str) -> Dict[str, Any] | None:
        """Retrieve corpus by ID. Returns None if not found."""
        cur = self.db.execute(
            "SELECT id, project_id, name, created_at, updated_at FROM corpus WHERE id = ?",
            (corpus_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "project_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            }
        return None
