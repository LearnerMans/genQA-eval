from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime

class ProjectRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all projects from the database."""
        cur = self.db.execute("SELECT id, name, created_at, updated_at FROM projects")
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "created_at": row[2],
                "updated_at": row[3]
            }
            for row in rows
        ]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project in the database."""
        project_id = str(uuid.uuid4())
        name = data.get("name")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO projects (id, name, created_at) VALUES (?, ?, ?)",
            (project_id, name, created_at)
        )

        return {
            "id": project_id,
            "name": name,
            "created_at": created_at,
            "updated_at": None
        }

    def get_by_id(self, project_id: str) -> Dict[str, Any] | None:
        """Retrieve a single project by its ID."""
        cur = self.db.execute(
            "SELECT id, name, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "created_at": row[2],
                "updated_at": row[3]
            }
        return None

    def delete_by_id(self, project_id: str) -> bool:
        """Delete a project by its ID. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cur.rowcount > 0
