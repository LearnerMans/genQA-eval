from db.db import DB
from typing import List, Dict, Any
from repos.store import Repository
import uuid
from datetime import datetime
import hashlib


class QARepo(Repository):
    def __init__(self, db: DB):
        self.db = db

    def _generate_hash(self, question: str, answer: str) -> str:
        """Generate a hash from question and answer to detect duplicates."""
        content = f"{question.strip().lower()}||{answer.strip().lower()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all QA pairs from the database."""
        cur = self.db.execute(
            "SELECT id, project_id, question, answer, hash FROM question_answer_pairs"
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "question": row[2],
                "answer": row[3],
                "hash": row[4]
            }
            for row in rows
        ]

    def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all QA pairs for a given project_id."""
        cur = self.db.execute(
            "SELECT id, project_id, question, answer, hash FROM question_answer_pairs WHERE project_id = ?",
            (project_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "question": row[2],
                "answer": row[3],
                "hash": row[4]
            }
            for row in rows
        ]

    def get_by_id(self, qa_id: str) -> Dict[str, Any] | None:
        """Retrieve a single QA pair by ID."""
        cur = self.db.execute(
            "SELECT id, project_id, question, answer, hash FROM question_answer_pairs WHERE id = ?",
            (qa_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "project_id": row[1],
            "question": row[2],
            "answer": row[3],
            "hash": row[4]
        }

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new QA pair in the database.
        Raises exception if duplicate (same question+answer for project) exists.
        """
        qa_id = str(uuid.uuid4())
        project_id = data.get("project_id")
        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()

        if not question or not answer:
            raise ValueError("Question and answer cannot be empty")

        # Generate hash for duplicate detection
        content_hash = self._generate_hash(question, answer)

        # Check for duplicate
        cur = self.db.execute(
            "SELECT id FROM question_answer_pairs WHERE project_id = ? AND hash = ?",
            (project_id, content_hash)
        )
        if cur.fetchone():
            raise ValueError("Duplicate QA pair: This question-answer combination already exists for this project")

        # Insert new QA pair
        self.db.execute(
            "INSERT INTO question_answer_pairs (id, project_id, question, answer, hash) VALUES (?, ?, ?, ?, ?)",
            (qa_id, project_id, question, answer, content_hash)
        )

        return {
            "id": qa_id,
            "project_id": project_id,
            "question": question,
            "answer": answer,
            "hash": content_hash
        }

    def create_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple QA pairs in a batch.
        Returns summary with counts of created, skipped (duplicates), and failed items.
        """
        created = []
        skipped = []
        failed = []

        for data in data_list:
            try:
                qa = self.create(data)
                created.append(qa)
            except ValueError as e:
                if "Duplicate" in str(e):
                    skipped.append({
                        "question": data.get("question"),
                        "reason": "duplicate"
                    })
                else:
                    failed.append({
                        "question": data.get("question"),
                        "reason": str(e)
                    })
            except Exception as e:
                failed.append({
                    "question": data.get("question"),
                    "reason": str(e)
                })

        return {
            "created": created,
            "created_count": len(created),
            "skipped": skipped,
            "skipped_count": len(skipped),
            "failed": failed,
            "failed_count": len(failed),
            "total_processed": len(data_list)
        }

    def delete_by_id(self, qa_id: str) -> bool:
        """Delete a QA pair by its ID. Returns True if deleted, False if not found."""
        cur = self.db.execute("DELETE FROM question_answer_pairs WHERE id = ?", (qa_id,))
        return cur.rowcount > 0

    def delete_by_project_id(self, project_id: str) -> int:
        """Delete all QA pairs for a project. Returns count of deleted items."""
        cur = self.db.execute(
            "DELETE FROM question_answer_pairs WHERE project_id = ?",
            (project_id,)
        )
        return cur.rowcount
