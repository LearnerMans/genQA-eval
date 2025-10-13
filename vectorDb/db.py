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

    def delete_collection(self, name: str):
        """Delete a collection by name."""
        try:
            self.client.delete_collection(name=name)
        except Exception as e:
            logging.error(f"Failed to delete collection '{name}': {e}")
            raise VectorDbError(f"Could not delete collection '{name}'.") from e

    def list_collections(self) -> list:
        """List all collection names."""
        try:
            return [collection.name for collection in self.client.list_collections()]
        except Exception as e:
            logging.error(f"Failed to list collections: {e}")
            raise VectorDbError("Could not list collections.") from e

    def get_collection_info(self, name: str) -> dict:
        """Get information about a collection."""
        try:
            collection = self.client.get_collection(name=name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            logging.error(f"Failed to get collection info for '{name}': {e}")
            raise VectorDbError(f"Could not get collection info for '{name}'.") from e

    def add_to_collection(self, name: str, data: list):
        """Add documents/vectors to a collection."""
        try:
            collection = self.client.get_collection(name=name)
            if data:
                ids = [item['id'] for item in data]
                vectors = [item['vector'] for item in data]
                metadatas = [item['metadata'] for item in data]
                collection.add(ids=ids, embeddings=vectors, metadatas=metadatas)
        except Exception as e:
            logging.error(f"Failed to add data to collection '{name}': {e}")
            raise VectorDbError(f"Could not add data to collection '{name}'.") from e

    def search_similar(self, collection_name: str, query_embedding: list, top_k: int = 5):
        """Search for similar vectors in a collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            return [
                {
                    'id': results['ids'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                }
                for i in range(len(results['ids'][0]))
            ]
        except Exception as e:
            logging.error(f"Failed to search collection '{collection_name}': {e}")
            raise VectorDbError(f"Could not search collection '{collection_name}'.") from e
