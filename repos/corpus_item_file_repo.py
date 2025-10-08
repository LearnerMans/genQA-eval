from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
import os
from datetime import datetime

class CorpusItemFileRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_by_corpus_id(self, corpus_id: str) -> List[Dict[str, Any]]:
        """Retrieve all files by corpus_id."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, name, ext, content, created_at, extraction_at, updated_at FROM corpus_item_file WHERE corpus_id = ?",
            (corpus_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "ext": row[4],
                "content": row[5],
                "created_at": row[6],
                "extraction_at": row[7],
                "updated_at": row[8],
                "type": "file"
            }
            for row in rows
        ]

    def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all files by project_id."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, name, ext, content, created_at, extraction_at, updated_at FROM corpus_item_file WHERE project_id = ?",
            (project_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "ext": row[4],
                "content": row[5],
                "created_at": row[6],
                "extraction_at": row[7],
                "updated_at": row[8],
                "type": "file"
            }
            for row in rows
        ]

    def get_by_id(self, file_id: str) -> Dict[str, Any] | None:
        """Retrieve file by ID."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, name, ext, content, created_at, extraction_at, updated_at FROM corpus_item_file WHERE id = ?",
            (file_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "ext": row[4],
                "content": row[5],
                "created_at": row[6],
                "extraction_at": row[7],
                "updated_at": row[8],
                "type": "file"
            }
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all files."""
        cur = self.db.execute("SELECT id, project_id, corpus_id, name, ext, content, created_at, extraction_at, updated_at FROM corpus_item_file")
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "ext": row[4],
                "content": row[5],
                "created_at": row[6],
                "extraction_at": row[7],
                "updated_at": row[8],
                "type": "file"
            }
            for row in rows
        ]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file item."""
        file_id = str(uuid.uuid4())
        project_id = data.get("project_id")
        corpus_id = data.get("corpus_id")
        name = data.get("name")
        ext = data.get("ext", "")
        content = data.get("content", "")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO corpus_item_file (id, project_id, corpus_id, name, ext, content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (file_id, project_id, corpus_id, name, ext, content, created_at)
        )

        return {
            "id": file_id,
            "project_id": project_id,
            "corpus_id": corpus_id,
            "name": name,
            "ext": ext,
            "content": content,
            "created_at": created_at,
            "extraction_at": None,
            "updated_at": None,
            "type": "file"
        }

    def delete_by_id(self, file_id: str) -> bool:
        """Delete a file by its ID."""
        cur = self.db.execute("DELETE FROM corpus_item_file WHERE id = ?", (file_id,))
        return cur.rowcount > 0

    def delete_by_corpus_id(self, corpus_id: str) -> bool:
        """Delete all files by corpus_id."""
        cur = self.db.execute("DELETE FROM corpus_item_file WHERE corpus_id = ?", (corpus_id,))
        return cur.rowcount > 0

    def update(self, file_id: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Update file by ID."""
        update_fields = []
        params = []

        if "name" in data:
            update_fields.append("name = ?")
            params.append(data["name"])

        if "ext" in data:
            update_fields.append("ext = ?")
            params.append(data["ext"])

        if "content" in data:
            update_fields.append("content = ?")
            params.append(data["content"])

        if not update_fields:
            return None

        update_fields.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(file_id)

        query = f"UPDATE corpus_item_file SET {', '.join(update_fields)} WHERE id = ?"
        cur = self.db.execute(query, tuple(params))

        if cur.rowcount > 0:
            return self.get_by_id(file_id)
        return None

    def save_file_to_disk(self, file_id: str, file_path: str) -> bool:
        """Save file content to disk and update the database."""
        file_item = self.get_by_id(file_id)
        if not file_item:
            return False

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_item["content"])

            # Update extraction_at timestamp
            self.db.execute(
                "UPDATE corpus_item_file SET extraction_at = ? WHERE id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_id)
            )

            return True
        except Exception:
            return False

    def delete_file_from_disk(self, file_path: str) -> bool:
        """Delete file from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
