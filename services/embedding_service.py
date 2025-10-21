"""
Embedding service for generating vector embeddings and managing vector collections.
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from llm import get_embedding_model
from vectorDb.db import VectorDb
from db.db import DB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChunkEmbedding:
    """Represents a chunk with its embedding vector."""
    chunk_id: str
    source_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]

class EmbeddingService:
    """Service for generating embeddings and managing vector collections."""

    def __init__(self, db: DB, vdb: VectorDb, embedding_model_name: str = None):
        self.db = db
        self.vdb = vdb
        self.embedding_model_name = embedding_model_name or 'openai_text_embedding_large_3'

    async def generate_embeddings(self, chunks: List, batch_size: int = 100) -> List[ChunkEmbedding]:
        """
        Generate embeddings for text chunks in batches.

        Args:
            chunks: List of TextChunk objects
            batch_size: Number of chunks to process in each batch

        Returns:
            List of ChunkEmbedding objects
        """
        if not chunks:
            return []

        try:
            # Get embedding model
            embedding_model = get_embedding_model(self.embedding_model_name)

            # Process chunks in batches
            chunk_embeddings = []

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

                # Extract texts from chunks
                # For FAQ chunks, use embedding_text from metadata
                # For other chunks, use content
                texts = []
                for chunk in batch:
                    if chunk.source_type == 'faq' and 'embedding_text' in chunk.metadata:
                        texts.append(chunk.metadata['embedding_text'])
                    else:
                        texts.append(chunk.content)

                # Generate embeddings
                embeddings = await embedding_model.embed_texts(texts)

                # Create ChunkEmbedding objects
                for chunk, embedding in zip(batch, embeddings):
                    metadata = {
                        'chunk_index': chunk.chunk_index,
                        'source_type': chunk.source_type,
                        'embedding_model': self.embedding_model_name,
                        'embedding_dimensions': len(embedding)
                    }

                    # For FAQ chunks, add question to metadata
                    if chunk.source_type == 'faq':
                        metadata['question'] = chunk.metadata.get('question', '')
                        metadata['embedding_mode'] = chunk.metadata.get('embedding_mode', 'both')

                    chunk_embeddings.append(ChunkEmbedding(
                        chunk_id=chunk.chunk_id,
                        source_id=chunk.source_id,
                        content=chunk.content,
                        embedding=embedding,
                        metadata=metadata
                    ))

            logger.info(f"Generated embeddings for {len(chunk_embeddings)} chunks")
            return chunk_embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def create_test_collection(self, test_id: str, chunks: List, embedding_model_name: str = None) -> str:
        """
        Create a test-specific vector collection with embedded chunks.

        Args:
            test_id: Test identifier
            chunks: List of TextChunk objects to embed and store
            embedding_model_name: Optional embedding model override

        Returns:
            Collection name/ID
        """
        if not chunks:
            logger.warning("No chunks provided for collection creation")
            return None

        model_name = embedding_model_name or self.embedding_model_name
        collection_name = f"test_{test_id}_{model_name}"

        try:
            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks using {model_name}")
            chunk_embeddings = await self.generate_embeddings(chunks)

            # Prepare data for vector database
            collection_data = []
            for chunk_emb in chunk_embeddings:
                metadata_dict = {
                    'test_id': test_id,
                    'source_id': chunk_emb.source_id,
                    'content': chunk_emb.content,
                    'chunk_index': chunk_emb.metadata['chunk_index'],
                    'source_type': chunk_emb.metadata['source_type'],
                    'embedding_model': chunk_emb.metadata['embedding_model']
                }

                # Add FAQ-specific metadata if present
                if 'question' in chunk_emb.metadata:
                    metadata_dict['question'] = chunk_emb.metadata['question']
                if 'embedding_mode' in chunk_emb.metadata:
                    metadata_dict['embedding_mode'] = chunk_emb.metadata['embedding_mode']

                collection_data.append({
                    'id': chunk_emb.chunk_id,
                    'vector': chunk_emb.embedding,
                    'metadata': metadata_dict
                })

            # Create collection in vector database
            self.vdb.create_collection(collection_name)

            # Add vectors to collection
            self.vdb.add_to_collection(collection_name, collection_data)

            logger.info(f"Created collection '{collection_name}' with {len(collection_data)} vectors")
            return collection_name

        except Exception as e:
            logger.error(f"Error creating test collection: {str(e)}")
            raise

    async def update_test_collection(self, test_id: str, new_chunks: List,
                                   collection_name: str = None) -> bool:
        """
        Update existing test collection with new chunks.

        Args:
            test_id: Test identifier
            new_chunks: List of new TextChunk objects to add
            collection_name: Optional collection name override

        Returns:
            Success status
        """
        if not new_chunks:
            return True

        try:
            collection_name = collection_name or f"test_{test_id}_{self.embedding_model_name}"

            # Generate embeddings for new chunks
            chunk_embeddings = await self.generate_embeddings(new_chunks)

            # Prepare data for vector database
            collection_data = []
            for chunk_emb in chunk_embeddings:
                metadata_dict = {
                    'test_id': test_id,
                    'source_id': chunk_emb.source_id,
                    'content': chunk_emb.content,
                    'chunk_index': chunk_emb.metadata['chunk_index'],
                    'source_type': chunk_emb.metadata['source_type'],
                    'embedding_model': chunk_emb.metadata['embedding_model']
                }

                # Add FAQ-specific metadata if present
                if 'question' in chunk_emb.metadata:
                    metadata_dict['question'] = chunk_emb.metadata['question']
                if 'embedding_mode' in chunk_emb.metadata:
                    metadata_dict['embedding_mode'] = chunk_emb.metadata['embedding_mode']

                collection_data.append({
                    'id': chunk_emb.chunk_id,
                    'vector': chunk_emb.embedding,
                    'metadata': metadata_dict
                })

            # Add new vectors to existing collection
            self.vdb.add_to_collection(collection_name, collection_data)

            logger.info(f"Added {len(collection_data)} new vectors to collection '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Error updating test collection: {str(e)}")
            return False

    def search_similar_chunks(self, collection_name: str, query: str,
                            top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in a test collection.

        Args:
            collection_name: Name of the collection to search in
            query: Query text
            top_k: Number of similar chunks to return

        Returns:
            List of similar chunks with scores
        """
        try:
            # Generate embedding for query
            embedding_model = get_embedding_model(self.embedding_model_name)
            query_embedding = embedding_model.embed_text(query)

            # Search vector database
            results = self.vdb.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=top_k
            )

            return results

        except Exception as e:
            logger.error(f"Error searching collection: {str(e)}")
            return []

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        try:
            return self.vdb.get_collection_info(collection_name)
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a test collection."""
        try:
            self.vdb.delete_collection(collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False

    def list_test_collections(self, test_id: str = None) -> List[str]:
        """List all test collections, optionally filtered by test_id."""
        try:
            all_collections = self.vdb.list_collections()

            if test_id:
                # Filter collections by test_id
                test_collections = [
                    coll for coll in all_collections
                    if coll.startswith(f"test_{test_id}_")
                ]
                return test_collections

            return all_collections

        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []

    def get_embedding_summary(self, chunk_embeddings: List[ChunkEmbedding]) -> Dict[str, Any]:
        """Get summary statistics of embedding results."""
        if not chunk_embeddings:
            return {"total_embeddings": 0, "total_dimensions": 0}

        dimensions = len(chunk_embeddings[0].embedding) if chunk_embeddings else 0

        return {
            "total_embeddings": len(chunk_embeddings),
            "embedding_dimensions": dimensions,
            "embedding_model": chunk_embeddings[0].metadata.get('embedding_model', 'unknown') if chunk_embeddings else 'unknown',
            "sources_covered": len(set(emb.source_id for emb in chunk_embeddings)),
            "total_tokens_estimated": sum(len(emb.content.split()) for emb in chunk_embeddings)
        }
