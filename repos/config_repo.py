from db.db import DB
from typing import List, Dict, Any, Optional
import uuid

class ConfigRepo:
    def __init__(self, db: DB):
        self.db = db

    def get_by_test_id(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve config for a given test_id. Returns None if not found."""
        cur = self.db.execute(
            "SELECT id, test_id, type, chunk_size, overlap, generative_model, embedding_model, top_k FROM config WHERE test_id = ?",
            (test_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "test_id": row[1],
                "type": row[2],
                "chunk_size": row[3],
                "overlap": row[4],
                "generative_model": row[5],
                "embedding_model": row[6],
                "top_k": row[7]
            }
        return None

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new config for the test_id. Ensures only one config per test_id by deleting any existing config before inserting."""
        test_id = data["test_id"]
        # Delete existing config for this test_id to ensure only one
        self.db.execute("DELETE FROM config WHERE test_id = ?", (test_id,))

        config_id = str(uuid.uuid4())
        type_ = data["type"]
        chunk_size = data["chunk_size"]
        overlap = data["overlap"]
        generative_model = data.get("generative_model", "openai_4o")
        embedding_model = data.get("embedding_model", "openai_text_embedding_large_3")
        top_k = data.get("top_k", 10)

        self.db.execute(
            "INSERT INTO config (id, test_id, type, chunk_size, overlap, generative_model, embedding_model, top_k) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (config_id, test_id, type_, chunk_size, overlap, generative_model, embedding_model, top_k)
        )

        return {
            "id": config_id,
            "test_id": test_id,
            "type": type_,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "generative_model": generative_model,
            "embedding_model": embedding_model,
            "top_k": top_k
        }

    def delete_by_test_id(self, test_id: str) -> bool:
        """Delete the config for a given test_id. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM config WHERE test_id = ?", (test_id,))
        return cur.rowcount > 0
