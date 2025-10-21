from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

class FAQChunker:
    """
    FAQ chunker that doesn't split content - each FAQ pair is already a chunk.
    This is a pass-through chunker that returns the content as-is.
    """

    def __init__(self):
        """Initialize the FAQ chunker."""
        pass

    def chunk_faq_pair(self, content: str, metadata: dict = None) -> dict:
        """
        Process a single FAQ pair without chunking.

        Args:
            content: The answer content to store
            metadata: Metadata including question, embedding_text, etc.

        Returns:
            Dictionary with chunk data
        """
        return {
            'content': content,
            'metadata': metadata or {}
        }

    def chunk_text(self, text: str) -> list[str]:
        """
        For FAQ, each "text" is already a complete chunk.
        This method exists for compatibility but FAQs should use chunk_faq_pair.

        Args:
            text: The text (answer) to be returned as a single chunk

        Returns:
            List with single chunk
        """
        return [text]


class RecursiveChunker:
    """
    A recursive text chunker using LangChain's RecursiveCharacterTextSplitter
    with appropriate separators for hierarchical splitting.
    """

    def __init__(self, separators=None, chunk_size=1000, chunk_overlap=200):
        """
        Initialize the recursive chunker.

        Args:
            separators: List of separators for hierarchical splitting.
                      Defaults to paragraph, line, word, character level.
            chunk_size: Maximum size of each chunk.
            chunk_overlap: Overlap between consecutive chunks.
        """
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]
        self.separators = separators
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            separators=self.separators,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def chunk_text(self, text: str) -> list[str]:
        """
        Split the input text into chunks using recursive character splitting.

        Args:
            text: The text to be chunked.

        Returns:
            List of text chunks.
        """
        return self.splitter.split_text(text)

def chunk_text_recur(text: str, chunk_size: int = 1000, chunk_overlap: int = 200, separators: list[str] = None) -> list[str]:
    """
    Convenience function for chunking text with default recursive separators.

    Args:
        text: The text to be chunked.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Overlap between consecutive chunks.
        separators: List of separators. Defaults to ["\n\n", "\n", " ", ""].

    Returns:
        List of text chunks.
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
    chunker = RecursiveChunker(separators=separators, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_text(text)
