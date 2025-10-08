import chromadb
import logging

class VectorDbError(Exception):
    """Base class for VectorDB-related errors."""

class VectorDb:
    def __init__(self, path: str):
        try:
            self.client = chromadb.PersistentClient(path)
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB client at {path}: {e}")
            raise VectorDbError("Could not initialize vector database.") from e

    def create_collection(self, name: str):
        try:
            collection = self.client.create_collection(name=name)
            return collection
        except Exception as e:
            logging.error(f"Failed to create collection '{name}': {e}")
            raise VectorDbError(f"Could not create collection '{name}'.") from e
