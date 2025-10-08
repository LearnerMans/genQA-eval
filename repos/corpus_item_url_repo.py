from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime

class CorpusItemUrlRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_by_corpus_id(self, corpus_id: str) -> List[Dict[str, Any]]:
        """Retrieve all URLs by corpus_id."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, url, content, created_at, extraction_at, updated_at FROM corpus_item_url WHERE corpus_id = ?",
            (corpus_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "url": row[3],
                "content": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "url"
            }
            for row in rows
        ]

    def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all URLs by project_id."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, url, content, created_at, extraction_at, updated_at FROM corpus_item_url WHERE project_id = ?",
            (project_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "url": row[3],
                "content": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "url"
            }
            for row in rows
        ]

    def get_by_id(self, url_id: str) -> Dict[str, Any] | None:
        """Retrieve URL item by ID."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, url, content, created_at, extraction_at, updated_at FROM corpus_item_url WHERE id = ?",
            (url_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "url": row[3],
                "content": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "url"
            }
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all URL items."""
        cur = self.db.execute("SELECT id, project_id, corpus_id, url, content, created_at, extraction_at, updated_at FROM corpus_item_url")
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "url": row[3],
                "content": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "url"
            }
            for row in rows
        ]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new URL item."""
        url_id = str(uuid.uuid4())
        project_id = data.get("project_id")
        corpus_id = data.get("corpus_id")
        url = data.get("url")
        content = data.get("content", "")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO corpus_item_url (id, project_id, corpus_id, url, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (url_id, project_id, corpus_id, url, content, created_at)
        )

        return {
            "id": url_id,
            "project_id": project_id,
            "corpus_id": corpus_id,
            "url": url,
            "content": content,
            "created_at": created_at,
            "extraction_at": None,
            "updated_at": None,
            "type": "url"
        }

    def delete_by_id(self, url_id: str) -> bool:
        """Delete a URL item by its ID."""
        cur = self.db.execute("DELETE FROM corpus_item_url WHERE id = ?", (url_id,))
        return cur.rowcount > 0

    def delete_by_corpus_id(self, corpus_id: str) -> bool:
        """Delete all URL items by corpus_id."""
        cur = self.db.execute("DELETE FROM corpus_item_url WHERE corpus_id = ?", (corpus_id,))
        return cur.rowcount > 0

    def update(self, url_id: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Update URL item by ID."""
        update_fields = []
        params = []

        if "url" in data:
            update_fields.append("url = ?")
            params.append(data["url"])

        if "content" in data:
            update_fields.append("content = ?")
            params.append(data["content"])

        if not update_fields:
            return None

        update_fields.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(url_id)

        query = f"UPDATE corpus_item_url SET {', '.join(update_fields)} WHERE id = ?"
        cur = self.db.execute(query, tuple(params))

        if cur.rowcount > 0:
            return self.get_by_id(url_id)
        return None

    def update_content(self, url_id: str, content: str) -> bool:
        """Update content and extraction timestamp for a URL item."""
        cur = self.db.execute(
            "UPDATE corpus_item_url SET content = ?, extraction_at = ? WHERE id = ?",
            (content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url_id)
        )
        return cur.rowcount > 0
