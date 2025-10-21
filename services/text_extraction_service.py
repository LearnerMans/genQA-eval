"""
Text extraction service for processing files and URLs while preserving source boundaries.
"""
import asyncio
import logging
import os
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from extractors.extractors import get_extractor, crawl_and_extract_markdown
from db.db import DB
from repos.store import Store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedContent:
    """Represents extracted content with metadata."""
    source_id: str
    source_type: str  # 'file', 'url', or 'faq'
    source_path: str  # file path, URL, or FAQ item ID
    content: str
    extracted_at: str
    metadata: Dict[str, Any]

class TextExtractionService:
    """Service for extracting text from various sources while preserving boundaries."""

    def __init__(self, db: DB, store: Store):
        self.db = db
        self.store = store

    async def extract_from_files(self, project_id: str, corpus_id: str, file_paths: List[str]) -> List[ExtractedContent]:
        """
        Extract text from multiple files while preserving file boundaries.

        Args:
            project_id: Project identifier
            corpus_id: Corpus identifier
            file_paths: List of file paths to extract text from

        Returns:
            List of ExtractedContent objects
        """
        extracted_contents = []

        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"File not found: {file_path}")
                    continue

                # Get appropriate extractor
                extractor = get_extractor(file_path)
                content = extractor.extract_text()

                if not content.strip():
                    logger.warning(f"No content extracted from: {file_path}")
                    continue

                # Create source record in database
                source_id = str(uuid.uuid4())
                self.db.execute(
                    "INSERT INTO sources (id, type, path_or_link) VALUES (?, ?, ?)",
                    (source_id, 'file', file_path)
                )

                # Get file metadata
                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_path)[1][1:] if os.path.splitext(file_path)[1] else ""

                # Create corpus item record
                corpus_item_data = {
                    "project_id": project_id,
                    "corpus_id": corpus_id,
                    "name": file_name,
                    "ext": file_ext,
                    "content": content
                }

                corpus_item = self.store.corpus_item_file_repo.create(corpus_item_data)

                extracted_content = ExtractedContent(
                    source_id=source_id,
                    source_type='file',
                    source_path=file_path,
                    content=content,
                    extracted_at=datetime.now().isoformat(),
                    metadata={
                        'file_name': file_name,
                        'file_extension': file_ext,
                        'file_size': len(content),
                        'corpus_item_id': corpus_item['id']
                    }
                )

                extracted_contents.append(extracted_content)
                logger.info(f"Successfully extracted text from file: {file_path}")

            except Exception as e:
                logger.error(f"Error extracting text from file {file_path}: {str(e)}")
                continue

        return extracted_contents

    async def extract_from_urls(self, project_id: str, corpus_id: str, urls: List[str], crawl_depth: int = 1) -> List[ExtractedContent]:
        """
        Extract text from multiple URLs while preserving URL boundaries.

        Args:
            project_id: Project identifier
            corpus_id: Corpus identifier
            urls: List of URLs to extract text from
            crawl_depth: Depth for web crawling (default: 1)

        Returns:
            List of ExtractedContent objects
        """
        extracted_contents = []

        for url in urls:
            try:
                # Extract content from URL (with crawling if depth > 1)
                content = crawl_and_extract_markdown(url, depth=crawl_depth)

                if not content.strip():
                    logger.warning(f"No content extracted from URL: {url}")
                    continue

                # Create source record in database
                source_id = str(uuid.uuid4())
                self.db.execute(
                    "INSERT INTO sources (id, type, path_or_link) VALUES (?, ?, ?)",
                    (source_id, 'url', url)
                )

                # Create corpus item record
                corpus_item_data = {
                    "project_id": project_id,
                    "corpus_id": corpus_id,
                    "url": url,
                    "content": content
                }

                corpus_item = self.store.corpus_item_url_repo.create(corpus_item_data)

                extracted_content = ExtractedContent(
                    source_id=source_id,
                    source_type='url',
                    source_path=url,
                    content=content,
                    extracted_at=datetime.now().isoformat(),
                    metadata={
                        'url': url,
                        'crawl_depth': crawl_depth,
                        'content_size': len(content),
                        'corpus_item_id': corpus_item['id']
                    }
                )

                extracted_contents.append(extracted_content)
                logger.info(f"Successfully extracted text from URL: {url}")

            except Exception as e:
                logger.error(f"Error extracting text from URL {url}: {str(e)}")
                continue

        return extracted_contents

    async def extract_from_faqs(self, project_id: str, faq_item_ids: List[str]) -> List[ExtractedContent]:
        """
        Extract content from FAQ items.

        Args:
            project_id: Project identifier
            faq_item_ids: List of FAQ item IDs to extract

        Returns:
            List of ExtractedContent objects (one per FAQ pair)
        """
        extracted_contents = []

        for faq_item_id in faq_item_ids:
            try:
                # Get FAQ item with all pairs
                faq_item = self.store.corpus_item_faq_repo.get_by_id(faq_item_id)

                if not faq_item:
                    logger.warning(f"FAQ item not found: {faq_item_id}")
                    continue

                pairs = faq_item.get('pairs', [])
                embedding_mode = faq_item.get('embedding_mode', 'both')

                if not pairs:
                    logger.warning(f"No FAQ pairs found for item: {faq_item_id}")
                    continue

                # Create source record in database for the FAQ item
                source_id = str(uuid.uuid4())
                self.db.execute(
                    "INSERT INTO sources (id, type, path_or_link) VALUES (?, ?, ?)",
                    (source_id, 'faq', faq_item_id)
                )

                # Each FAQ pair becomes a separate ExtractedContent
                # But they all share the same source_id
                for pair in pairs:
                    question = pair['question']
                    answer = pair['answer']

                    # Determine what to embed based on embedding_mode
                    if embedding_mode == 'question_only':
                        # Embed only the question
                        embedding_text = question
                    else:  # 'both'
                        # Embed question + answer
                        embedding_text = f"Q: {question}\nA: {answer}"

                    # Content is always question + answer (for retrieval results display)
                    content = f"Q: {question}\nA: {answer}"

                    extracted_content = ExtractedContent(
                        source_id=source_id,
                        source_type='faq',
                        source_path=faq_item_id,
                        content=content,
                        extracted_at=datetime.now().isoformat(),
                        metadata={
                            'faq_item_id': faq_item_id,
                            'faq_pair_id': pair['id'],
                            'question': question,
                            'answer': answer,
                            'embedding_mode': embedding_mode,
                            'embedding_text': embedding_text,  # What will be embedded
                            'row_index': pair.get('row_index', 0)
                        }
                    )

                    extracted_contents.append(extracted_content)

                # Update extraction timestamp
                self.store.corpus_item_faq_repo.update_extraction_timestamp(faq_item_id)
                logger.info(f"Successfully extracted {len(pairs)} FAQ pairs from item: {faq_item_id}")

            except Exception as e:
                logger.error(f"Error extracting FAQ item {faq_item_id}: {str(e)}")
                continue

        return extracted_contents

    async def extract_all_sources(self, project_id: str, corpus_id: str,
                                 file_paths: Optional[List[str]] = None,
                                 urls: Optional[List[str]] = None,
                                 faq_item_ids: Optional[List[str]] = None,
                                 crawl_depth: int = 1) -> List[ExtractedContent]:
        """
        Extract text from files, URLs, and FAQs in parallel while preserving boundaries.

        Args:
            project_id: Project identifier
            corpus_id: Corpus identifier
            file_paths: List of file paths (optional)
            urls: List of URLs (optional)
            faq_item_ids: List of FAQ item IDs (optional)
            crawl_depth: Depth for web crawling

        Returns:
            Combined list of ExtractedContent objects
        """
        file_paths = file_paths or []
        urls = urls or []
        faq_item_ids = faq_item_ids or []

        # Create tasks for parallel extraction
        tasks = []

        if file_paths:
            tasks.append(self.extract_from_files(project_id, corpus_id, file_paths))

        if urls:
            tasks.append(self.extract_from_urls(project_id, corpus_id, urls, crawl_depth))

        if faq_item_ids:
            tasks.append(self.extract_from_faqs(project_id, faq_item_ids))

        if not tasks:
            logger.warning("No sources provided for extraction")
            return []

        # Execute extractions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results and handle exceptions
        all_extracted = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Extraction task failed: {str(result)}")
            else:
                all_extracted.extend(result)

        logger.info(f"Successfully extracted content from {len(all_extracted)} sources")
        return all_extracted

    def get_extraction_summary(self, extracted_contents: List[ExtractedContent]) -> Dict[str, Any]:
        """Get summary statistics of extraction results."""
        if not extracted_contents:
            return {"total_sources": 0, "files": 0, "urls": 0, "faqs": 0, "total_content_size": 0}

        files = [c for c in extracted_contents if c.source_type == 'file']
        urls = [c for c in extracted_contents if c.source_type == 'url']
        faqs = [c for c in extracted_contents if c.source_type == 'faq']

        total_size = sum(len(c.content) for c in extracted_contents)

        return {
            "total_sources": len(extracted_contents),
            "files": len(files),
            "urls": len(urls),
            "faqs": len(faqs),
            "total_content_size": total_size,
            "average_content_size": total_size / len(extracted_contents) if extracted_contents else 0
        }
