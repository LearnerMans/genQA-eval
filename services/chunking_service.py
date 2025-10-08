"""
Chunking service for creating text chunks based on test-specific configuration.
"""
import logging
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from chunker.chunker import RecursiveChunker, chunk_text_recur
from db.db import DB
from repos.store import Store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    chunk_id: str
    source_id: str
    source_type: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]

class ChunkingService:
    """Service for chunking text based on test-specific configuration."""

    def __init__(self, db: DB, store: Store):
        self.db = db
        self.store = store

    def chunk_text_with_config(self, text: str, source_id: str, source_type: str,
                              chunk_size: int, overlap: int, chunk_type: str = 'recursive') -> List[TextChunk]:
        """
        Chunk text using specified configuration.

        Args:
            text: Text content to chunk
            source_id: Source identifier
            source_type: Type of source ('file' or 'url')
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks
            chunk_type: Type of chunking ('recursive' or 'semantic')

        Returns:
            List of TextChunk objects
        """
        if chunk_type == 'recursive':
            return self._chunk_recursive(text, source_id, source_type, chunk_size, overlap)
        else:
            # Default to recursive chunking
            logger.warning(f"Unknown chunk type '{chunk_type}', using recursive")
            return self._chunk_recursive(text, source_id, source_type, chunk_size, overlap)

    def _chunk_recursive(self, text: str, source_id: str, source_type: str,
                        chunk_size: int, overlap: int) -> List[TextChunk]:
        """Chunk text using recursive character splitting."""
        try:
            # Use the chunker module
            chunks = chunk_text_recur(
                text=text,
                chunk_size=chunk_size,
                chunk_overlap=overlap
            )

            text_chunks = []
            for i, chunk_content in enumerate(chunks):
                # Create chunk record in database
                chunk_id = str(uuid.uuid4())

                self.db.execute(
                    "INSERT INTO chunks (id, type, source_id, content, chunk_index) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, source_type, source_id, chunk_content, i)
                )

                text_chunks.append(TextChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    source_type=source_type,
                    content=chunk_content,
                    chunk_index=i,
                    metadata={
                        'chunk_size': len(chunk_content),
                        'chunk_type': 'recursive'
                    }
                ))

            logger.info(f"Created {len(text_chunks)} chunks for source {source_id}")
            return text_chunks

        except Exception as e:
            logger.error(f"Error chunking text for source {source_id}: {str(e)}")
            return []

    def chunk_extracted_content(self, extracted_contents: List, config: Dict[str, Any]) -> List[TextChunk]:
        """
        Chunk multiple extracted content items using test configuration.

        Args:
            extracted_contents: List of ExtractedContent objects
            config: Test configuration dictionary

        Returns:
            List of TextChunk objects
        """
        chunk_size = config.get('chunk_size', 1000)
        overlap = config.get('overlap', 200)
        chunk_type = config.get('type', 'recursive')

        all_chunks = []

        for extracted in extracted_contents:
            # Skip if content is too small to chunk meaningfully
            if len(extracted.content) <= chunk_size:
                # Create a single chunk for small content
                chunk_id = str(uuid.uuid4())
                self.db.execute(
                    "INSERT INTO chunks (id, type, source_id, content, chunk_index) VALUES (?, ?, ?, ?, ?)",
                    (chunk_id, extracted.source_type, extracted.source_id, extracted.content, 0)
                )

                chunk = TextChunk(
                    chunk_id=chunk_id,
                    source_id=extracted.source_id,
                    source_type=extracted.source_type,
                    content=extracted.content,
                    chunk_index=0,
                    metadata={
                        'chunk_size': len(extracted.content),
                        'chunk_type': chunk_type,
                        'reason': 'content_smaller_than_chunk_size'
                    }
                )
                all_chunks.append(chunk)
            else:
                # Chunk the content
                chunks = self.chunk_text_with_config(
                    text=extracted.content,
                    source_id=extracted.source_id,
                    source_type=extracted.source_type,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    chunk_type=chunk_type
                )
                all_chunks.extend(chunks)

        logger.info(f"Created total of {len(all_chunks)} chunks from {len(extracted_contents)} sources")
        return all_chunks

    def get_chunking_summary(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Get summary statistics of chunking results."""
        if not chunks:
            return {"total_chunks": 0, "total_size": 0, "average_size": 0}

        total_size = sum(len(chunk.content) for chunk in chunks)

        return {
            "total_chunks": len(chunks),
            "total_size": total_size,
            "average_size": total_size / len(chunks) if chunks else 0,
            "sources_covered": len(set(chunk.source_id for chunk in chunks)),
            "chunk_types": list(set(chunk.metadata.get('chunk_type', 'unknown') for chunk in chunks))
        }

    def get_chunks_by_source(self, source_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a specific source."""
        cur = self.db.execute(
            "SELECT id, type, source_id, content, chunk_index FROM chunks WHERE source_id = ? ORDER BY chunk_index",
            (source_id,)
        )
        rows = cur.fetchall()

        return [
            {
                "id": row[0],
                "type": row[1],
                "source_id": row[2],
                "content": row[3],
                "chunk_index": row[4]
            }
            for row in rows
        ]

    def delete_chunks_by_source(self, source_id: str) -> bool:
        """Delete all chunks for a specific source."""
        cur = self.db.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
        return cur.rowcount > 0
