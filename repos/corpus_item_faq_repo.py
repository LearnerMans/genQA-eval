from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime
import json

class CorpusItemFAQRepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def get_by_corpus_id(self, corpus_id: str) -> List[Dict[str, Any]]:
        """Retrieve all FAQ items by corpus_id."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, name, embedding_mode, created_at, extraction_at, updated_at FROM corpus_item_faq WHERE corpus_id = ?",
            (corpus_id,)
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            faq_item = {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "embedding_mode": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "faq"
            }
            # Get FAQ pairs count
            pair_count = self._get_faq_pair_count(row[0])
            faq_item["faq_count"] = pair_count
            result.append(faq_item)
        return result

    def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all FAQ items by project_id."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, name, embedding_mode, created_at, extraction_at, updated_at FROM corpus_item_faq WHERE project_id = ?",
            (project_id,)
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            faq_item = {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "embedding_mode": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "faq"
            }
            # Get FAQ pairs count
            pair_count = self._get_faq_pair_count(row[0])
            faq_item["faq_count"] = pair_count
            result.append(faq_item)
        return result

    def get_by_id(self, faq_id: str) -> Dict[str, Any] | None:
        """Retrieve FAQ item by ID."""
        cur = self.db.execute(
            "SELECT id, project_id, corpus_id, name, embedding_mode, created_at, extraction_at, updated_at FROM corpus_item_faq WHERE id = ?",
            (faq_id,)
        )
        row = cur.fetchone()
        if row:
            faq_item = {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "embedding_mode": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "faq"
            }
            # Get FAQ pairs
            pairs = self.get_faq_pairs(faq_id)
            faq_item["pairs"] = pairs
            faq_item["faq_count"] = len(pairs)
            return faq_item
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all FAQ items."""
        cur = self.db.execute("SELECT id, project_id, corpus_id, name, embedding_mode, created_at, extraction_at, updated_at FROM corpus_item_faq")
        rows = cur.fetchall()
        result = []
        for row in rows:
            faq_item = {
                "id": row[0],
                "project_id": row[1],
                "corpus_id": row[2],
                "name": row[3],
                "embedding_mode": row[4],
                "created_at": row[5],
                "extraction_at": row[6],
                "updated_at": row[7],
                "type": "faq"
            }
            # Get FAQ pairs count
            pair_count = self._get_faq_pair_count(row[0])
            faq_item["faq_count"] = pair_count
            result.append(faq_item)
        return result

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new FAQ item."""
        faq_id = str(uuid.uuid4())
        project_id = data.get("project_id")
        corpus_id = data.get("corpus_id")
        name = data.get("name")
        embedding_mode = data.get("embedding_mode", "both")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.execute(
            "INSERT INTO corpus_item_faq (id, project_id, corpus_id, name, embedding_mode, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (faq_id, project_id, corpus_id, name, embedding_mode, created_at)
        )

        # Create FAQ pairs if provided
        pairs = data.get("pairs", [])
        for idx, pair in enumerate(pairs):
            self.create_faq_pair(faq_id, pair["question"], pair["answer"], idx)

        return {
            "id": faq_id,
            "project_id": project_id,
            "corpus_id": corpus_id,
            "name": name,
            "embedding_mode": embedding_mode,
            "created_at": created_at,
            "extraction_at": None,
            "updated_at": None,
            "type": "faq",
            "faq_count": len(pairs)
        }

    def create_faq_pair(self, faq_item_id: str, question: str, answer: str, row_index: int) -> str:
        """Create a single FAQ pair."""
        pair_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO faq_pairs (id, faq_item_id, question, answer, row_index) VALUES (?, ?, ?, ?, ?)",
            (pair_id, faq_item_id, question, answer, row_index)
        )
        return pair_id

    def get_faq_pairs(self, faq_item_id: str) -> List[Dict[str, Any]]:
        """Get all FAQ pairs for a given FAQ item."""
        cur = self.db.execute(
            "SELECT id, question, answer, row_index FROM faq_pairs WHERE faq_item_id = ? ORDER BY row_index",
            (faq_item_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "row_index": row[3]
            }
            for row in rows
        ]

    def _get_faq_pair_count(self, faq_item_id: str) -> int:
        """Get count of FAQ pairs for a given FAQ item."""
        cur = self.db.execute(
            "SELECT COUNT(*) FROM faq_pairs WHERE faq_item_id = ?",
            (faq_item_id,)
        )
        row = cur.fetchone()
        return row[0] if row else 0

    def delete_by_id(self, faq_id: str) -> bool:
        """Delete an FAQ item by its ID (cascade deletes pairs)."""
        cur = self.db.execute("DELETE FROM corpus_item_faq WHERE id = ?", (faq_id,))
        return cur.rowcount > 0

    def delete_by_corpus_id(self, corpus_id: str) -> bool:
        """Delete all FAQ items by corpus_id."""
        cur = self.db.execute("DELETE FROM corpus_item_faq WHERE corpus_id = ?", (corpus_id,))
        return cur.rowcount > 0

    def update(self, faq_id: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
        """Update FAQ item by ID."""
        update_fields = []
        params = []

        if "name" in data:
            update_fields.append("name = ?")
            params.append(data["name"])

        if "embedding_mode" in data:
            update_fields.append("embedding_mode = ?")
            params.append(data["embedding_mode"])

        if not update_fields:
            return None

        update_fields.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(faq_id)

        query = f"UPDATE corpus_item_faq SET {', '.join(update_fields)} WHERE id = ?"
        cur = self.db.execute(query, tuple(params))

        if cur.rowcount > 0:
            return self.get_by_id(faq_id)
        return None

    def update_extraction_timestamp(self, faq_id: str) -> bool:
        """Update extraction_at timestamp."""
        self.db.execute(
            "UPDATE corpus_item_faq SET extraction_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), faq_id)
        )
        return True
