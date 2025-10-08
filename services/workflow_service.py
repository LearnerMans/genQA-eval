"""
Main workflow service that orchestrates the complete RAG evaluation pipeline.
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from services.text_extraction_service import TextExtractionService, ExtractedContent
from services.chunking_service import ChunkingService, TextChunk
from services.embedding_service import EmbeddingService, ChunkEmbedding
from db.db import DB
from repos.store import Store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowResult:
    """Result of the complete workflow execution."""
    test_id: str
    project_id: str
    corpus_id: str
    collection_name: str
    extraction_summary: Dict[str, Any]
    chunking_summary: Dict[str, Any]
    embedding_summary: Dict[str, Any]
    execution_time: float
    success: bool
    error_message: Optional[str] = None

class WorkflowService:
    """Main service orchestrating the complete RAG evaluation workflow."""

    def __init__(self, db: DB, store: Store, vdb):
        self.db = db
        self.store = store
        self.vdb = vdb

        # Initialize sub-services
        self.extraction_service = TextExtractionService(db, store)
        self.chunking_service = ChunkingService(db, store)

    async def process_test_corpus(self, test_id: str, project_id: str, corpus_id: str,
                                 file_paths: Optional[List[str]] = None,
                                 urls: Optional[List[str]] = None,
                                 crawl_depth: int = 1,
                                 embedding_model_name: str = None) -> WorkflowResult:
        """
        Process a complete test corpus through the entire pipeline.

        Args:
            test_id: Test identifier
            project_id: Project identifier
            corpus_id: Corpus identifier
            file_paths: List of file paths to process
            urls: List of URLs to process
            crawl_depth: Web crawling depth
            embedding_model_name: Embedding model to use

        Returns:
            WorkflowResult with complete execution summary
        """
        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"Starting workflow for test {test_id}")

            # Step 1: Extract text from sources
            logger.info("Step 1: Extracting text from sources")
            extracted_contents = await self.extraction_service.extract_all_sources(
                project_id=project_id,
                corpus_id=corpus_id,
                file_paths=file_paths,
                urls=urls,
                crawl_depth=crawl_depth
            )

            if not extracted_contents:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=project_id,
                    corpus_id=corpus_id,
                    collection_name="",
                    extraction_summary=self.extraction_service.get_extraction_summary(extracted_contents),
                    chunking_summary={"total_chunks": 0},
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message="No content extracted from provided sources"
                )

            extraction_summary = self.extraction_service.get_extraction_summary(extracted_contents)
            logger.info(f"Extracted content from {extraction_summary['total_sources']} sources")

            # Step 2: Get test configuration for chunking
            logger.info("Step 2: Getting test configuration")
            config = self.store.config_repo.get_by_test_id(test_id)

            if not config:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=project_id,
                    corpus_id=corpus_id,
                    collection_name="",
                    extraction_summary=extraction_summary,
                    chunking_summary={"total_chunks": 0},
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message=f"No configuration found for test {test_id}"
                )

            # Step 3: Chunk the extracted content
            logger.info("Step 3: Chunking extracted content")
            chunks = self.chunking_service.chunk_extracted_content(extracted_contents, config)
            chunking_summary = self.chunking_service.get_chunking_summary(chunks)
            logger.info(f"Created {chunking_summary['total_chunks']} chunks")

            # Step 4: Create embeddings and vector collection
            logger.info("Step 4: Creating embeddings and vector collection")
            embedding_service = EmbeddingService(self.db, self.vdb, embedding_model_name)

            collection_name = await embedding_service.create_test_collection(
                test_id=test_id,
                chunks=chunks,
                embedding_model_name=embedding_model_name
            )

            if not collection_name:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=project_id,
                    corpus_id=corpus_id,
                    collection_name="",
                    extraction_summary=extraction_summary,
                    chunking_summary=chunking_summary,
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message="Failed to create vector collection"
                )

            # Generate embeddings for summary (already done in create_test_collection)
            chunk_embeddings = await embedding_service.generate_embeddings(chunks)
            embedding_summary = embedding_service.get_embedding_summary(chunk_embeddings)

            execution_time = asyncio.get_event_loop().time() - start_time

            logger.info(f"Workflow completed successfully in {execution_time:.2f}s")
            logger.info(f"Collection '{collection_name}' created with {embedding_summary['total_embeddings']} embeddings")

            return WorkflowResult(
                test_id=test_id,
                project_id=project_id,
                corpus_id=corpus_id,
                collection_name=collection_name,
                extraction_summary=extraction_summary,
                chunking_summary=chunking_summary,
                embedding_summary=embedding_summary,
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Workflow failed: {str(e)}")

            return WorkflowResult(
                test_id=test_id,
                project_id=project_id,
                corpus_id=corpus_id,
                collection_name="",
                extraction_summary=self.extraction_service.get_extraction_summary([]),
                chunking_summary={"total_chunks": 0},
                embedding_summary={"total_embeddings": 0},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )

    async def update_test_corpus(self, test_id: str,
                               new_file_paths: Optional[List[str]] = None,
                               new_urls: Optional[List[str]] = None,
                               crawl_depth: int = 1) -> WorkflowResult:
        """
        Update an existing test corpus with new sources.

        Args:
            test_id: Test identifier
            new_file_paths: New file paths to add
            new_urls: New URLs to add
            crawl_depth: Web crawling depth

        Returns:
            WorkflowResult with update summary
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Get existing test and corpus info
            test = self.store.test_repo.get_by_id(test_id)
            if not test:
                return WorkflowResult(
                    test_id=test_id,
                    project_id="",
                    corpus_id="",
                    collection_name="",
                    extraction_summary={"total_sources": 0},
                    chunking_summary={"total_chunks": 0},
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message=f"Test {test_id} not found"
                )

            corpus = self.store.corpus_repo.get_by_project_id(test['project_id'])
            if not corpus:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=test['project_id'],
                    corpus_id="",
                    collection_name="",
                    extraction_summary={"total_sources": 0},
                    chunking_summary={"total_chunks": 0},
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message=f"No corpus found for project {test['project_id']}"
                )

            # Extract new content
            extracted_contents = await self.extraction_service.extract_all_sources(
                project_id=test['project_id'],
                corpus_id=corpus['id'],
                file_paths=new_file_paths,
                urls=new_urls,
                crawl_depth=crawl_depth
            )

            if not extracted_contents:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=test['project_id'],
                    corpus_id=corpus['id'],
                    collection_name="",
                    extraction_summary=self.extraction_service.get_extraction_summary(extracted_contents),
                    chunking_summary={"total_chunks": 0},
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=True,  # Not an error if no new content
                    error_message="No new content to add"
                )

            # Get test configuration
            config = self.store.config_repo.get_by_test_id(test_id)
            if not config:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=test['project_id'],
                    corpus_id=corpus['id'],
                    collection_name="",
                    extraction_summary=self.extraction_service.get_extraction_summary(extracted_contents),
                    chunking_summary={"total_chunks": 0},
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message=f"No configuration found for test {test_id}"
                )

            # Chunk new content
            chunks = self.chunking_service.chunk_extracted_content(extracted_contents, config)

            # Update vector collection
            embedding_service = EmbeddingService(self.db, self.vdb)
            collection_name = f"test_{test_id}_{config.get('embedding_model', 'openai_text_embedding_large_3')}"

            success = await embedding_service.update_test_collection(
                test_id=test_id,
                new_chunks=chunks,
                collection_name=collection_name
            )

            if not success:
                return WorkflowResult(
                    test_id=test_id,
                    project_id=test['project_id'],
                    corpus_id=corpus['id'],
                    collection_name=collection_name,
                    extraction_summary=self.extraction_service.get_extraction_summary(extracted_contents),
                    chunking_summary=self.chunking_service.get_chunking_summary(chunks),
                    embedding_summary={"total_embeddings": 0},
                    execution_time=asyncio.get_event_loop().time() - start_time,
                    success=False,
                    error_message="Failed to update vector collection"
                )

            # Generate embeddings for summary
            chunk_embeddings = await embedding_service.generate_embeddings(chunks)
            embedding_summary = embedding_service.get_embedding_summary(chunk_embeddings)

            execution_time = asyncio.get_event_loop().time() - start_time

            return WorkflowResult(
                test_id=test_id,
                project_id=test['project_id'],
                corpus_id=corpus['id'],
                collection_name=collection_name,
                extraction_summary=self.extraction_service.get_extraction_summary(extracted_contents),
                chunking_summary=self.chunking_service.get_chunking_summary(chunks),
                embedding_summary=embedding_summary,
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Update workflow failed: {str(e)}")

            return WorkflowResult(
                test_id=test_id,
                project_id="",
                corpus_id="",
                collection_name="",
                extraction_summary={"total_sources": 0},
                chunking_summary={"total_chunks": 0},
                embedding_summary={"total_embeddings": 0},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )

    def get_workflow_status(self, test_id: str) -> Dict[str, Any]:
        """Get the current status of a test's workflow."""
        try:
            # Get test info
            test = self.store.test_repo.get_by_id(test_id)
            if not test:
                return {"error": f"Test {test_id} not found"}

            # Get corpus info
            corpus = self.store.corpus_repo.get_by_project_id(test['project_id'])

            # Get config info
            config = self.store.config_repo.get_by_test_id(test_id)

            # Get corpus items count
            files_count = len(self.store.corpus_item_file_repo.get_by_project_id(test['project_id']))
            urls_count = len(self.store.corpus_item_url_repo.get_by_project_id(test['project_id']))

            # Get chunks count
            cur = self.db.execute("""
                SELECT COUNT(*) FROM chunks c
                INNER JOIN sources s ON c.source_id = s.id
                INNER JOIN corpus_item_file cif ON s.path_or_link = cif.name AND cif.project_id = ?
                UNION ALL
                SELECT COUNT(*) FROM chunks c
                INNER JOIN sources s ON c.source_id = s.id
                INNER JOIN corpus_item_url ciu ON s.path_or_link = ciu.url AND ciu.project_id = ?
            """, (test['project_id'], test['project_id']))

            chunks_count = sum(row[0] for row in cur.fetchall())

            # Get collection info
            embedding_service = EmbeddingService(self.db, self.vdb)
            collections = embedding_service.list_test_collections(test_id)
            collection_info = {}

            for collection_name in collections:
                info = embedding_service.get_collection_info(collection_name)
                collection_info[collection_name] = info

            return {
                "test_id": test_id,
                "test_name": test['name'],
                "project_id": test['project_id'],
                "corpus_id": corpus['id'] if corpus else None,
                "config": config,
                "sources": {
                    "files": files_count,
                    "urls": urls_count,
                    "total": files_count + urls_count
                },
                "chunks": chunks_count,
                "collections": collection_info,
                "status": "ready" if config and (files_count > 0 or urls_count > 0) else "incomplete"
            }

        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {"error": str(e)}
