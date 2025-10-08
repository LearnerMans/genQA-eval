"""
Example usage of the complete RAG evaluation workflow system.

This example demonstrates how to:
1. Set up a project, test, and corpus
2. Extract text from files and URLs
3. Chunk content with test-specific configuration
4. Generate embeddings and create vector collections
5. Search and evaluate the system
"""
import asyncio
import os
import uuid
from pathlib import Path

from db.db import DB
from repos.store import Store
from services.workflow_service import WorkflowService
from vectorDb.db import VectorDb
from llm import get_llm, get_embedding_model

# Example data
PROJECT_NAME = "RAG Evaluation Example"
TEST_NAME = "Document QA Test"
CORPUS_NAME = "Sample Documents"

# Sample files and URLs for the example
SAMPLE_FILES = [
    # Add paths to sample files you want to process
    # "data/sample_docs/document1.pdf",
    # "data/sample_docs/document2.docx",
    # "data/sample_docs/readme.md"
]

SAMPLE_URLS = [
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    "https://en.wikipedia.org/wiki/Vector_database",
    # Add more URLs as needed
]

async def setup_example_project(db: DB, store: Store) -> tuple[str, str, str]:
    """Set up an example project, test, and corpus."""

    # Create project
    project_data = {"name": PROJECT_NAME}
    project = store.project_repo.create(project_data)

    # Create corpus
    corpus_data = {
        "project_id": project["id"],
        "name": CORPUS_NAME
    }
    corpus = store.corpus_repo.create(corpus_data)

    # Create test
    test_data = {
        "project_id": project["id"],
        "name": TEST_NAME
    }
    test = store.test_repo.create(test_data)

    # Create test configuration
    config_data = {
        "test_id": test["id"],
        "type": "recursive",
        "chunk_size": 1000,
        "overlap": 200,
        "generative_model": "openai_4o",
        "embedding_model": "openai_text_embedding_large_3",
        "top_k": 5
    }
    store.config_repo.create(config_data)

    print(f"✅ Created project: {project['name']} (ID: {project['id']})")
    print(f"✅ Created corpus: {corpus['name']} (ID: {corpus['id']})")
    print(f"✅ Created test: {test['name']} (ID: {test['id']})")

    return project["id"], corpus["id"], test["id"]

async def run_workflow_example(db: DB, store: Store, vdb: VectorDb,
                              project_id: str, corpus_id: str, test_id: str):
    """Run the complete workflow example."""

    print("\n🚀 Starting RAG Evaluation Workflow Example")
    print("=" * 50)

    # Initialize workflow service
    workflow_service = WorkflowService(db, store, vdb)

    # Run the complete workflow
    print("📄 Processing corpus through complete pipeline...")
    result = await workflow_service.process_test_corpus(
        test_id=test_id,
        project_id=project_id,
        corpus_id=corpus_id,
        file_paths=SAMPLE_FILES if SAMPLE_FILES else None,
        urls=SAMPLE_URLS if SAMPLE_URLS else None,
        crawl_depth=1,
        embedding_model_name="openai_text_embedding_large_3"
    )

    # Display results
    if result.success:
        print("✅ Workflow completed successfully!")
        print(f"⏱️  Execution time: {result.execution_time:.2f} seconds")

        print("📊 Extraction Summary:")
        print(f"   • Total sources: {result.extraction_summary['total_sources']}")
        print(f"   • Files: {result.extraction_summary['files']}")
        print(f"   • URLs: {result.extraction_summary['urls']}")
        print(f"   • Total content size: {result.extraction_summary['total_content_size']:,} characters")

        print("✂️  Chunking Summary:")
        print(f"   • Total chunks: {result.chunking_summary['total_chunks']}")
        print(f"   • Average chunk size: {result.chunking_summary['average_size']:.0f} characters")

        print("🧠 Embedding Summary:")
        print(f"   • Total embeddings: {result.embedding_summary['total_embeddings']}")
        print(f"   • Embedding dimensions: {result.embedding_summary['embedding_dimensions']}")
        print(f"   • Embedding model: {result.embedding_summary['embedding_model']}")

        print(f"\n🎯 Collection created: {result.collection_name}")

        return result
    else:
        print(f"❌ Workflow failed: {result.error_message}")
        return None

async def demonstrate_search(db: DB, store: Store, vdb: VectorDb, test_id: str):
    """Demonstrate searching the created vector collection."""

    print("\n🔍 Demonstrating Vector Search")
    print("=" * 30)

    from services.embedding_service import EmbeddingService

    embedding_service = EmbeddingService(db, vdb)

    # Example search queries
    search_queries = [
        "What is retrieval-augmented generation?",
        "How do vector databases work?",
        "What are the benefits of RAG systems?"
    ]

    for query in search_queries:
        print(f"\n🔎 Query: {query}")

        # Get the first available collection for this test
        collections = embedding_service.list_test_collections(test_id)

        if collections:
            collection_name = collections[0]

            # Perform search
            results = embedding_service.search_similar_chunks(
                collection_name=collection_name,
                query=query,
                top_k=3
            )

            print(f"📄 Found {len(results)} similar chunks:")

            for i, result in enumerate(results, 1):
                print(f"   {i}. Score: {result.get('score', 0):.3f}")
                content = result.get('metadata', {}).get('content', '')[:100] + "..."
                print(f"      Content: {content}")
        else:
            print("   No collections found for search")

async def demonstrate_llm_integration():
    """Demonstrate LLM integration for question answering."""

    print("\n🤖 Demonstrating LLM Integration")
    print("=" * 30)

    try:
        # Initialize LLM
        llm = get_llm('openai_4o')

        # Example context from our processed documents
        context = """
        Retrieval-Augmented Generation (RAG) is a technique that combines
        retrieval-based methods with generative models. It enhances the
        accuracy and reliability of generative AI by incorporating
        external knowledge sources.

        Vector databases store and retrieve high-dimensional vectors
        efficiently. They enable fast similarity search and are crucial
        for RAG systems to find relevant information quickly.
        """

        # Example question
        question = "How does RAG improve generative AI systems?"

        messages = [
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}\n\nPlease provide a detailed answer based only on the context provided."}
        ]

        print(f"❓ Question: {question}")
        print("🤔 Generating answer using LLM...")

        answer = await llm.generate(messages)

        print(f"✅ Answer: {answer}")

    except Exception as e:
        print(f"❌ LLM demonstration failed: {str(e)}")
        print("   Make sure OPENAI_API_KEY environment variable is set")

async def main():
    """Main example function."""

    print("🎯 RAG Evaluation Workflow System Example")
    print("=" * 50)
    print("This example demonstrates the complete workflow for RAG evaluation:")
    print("1. Setting up projects, tests, and corpus")
    print("2. Extracting text from files and URLs")
    print("3. Chunking content with test-specific configuration")
    print("4. Generating embeddings and creating vector collections")
    print("5. Searching and evaluating the system")

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  Warning: OPENAI_API_KEY environment variable not set")
        print("   LLM and embedding functionality will not work without it")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")

    # Initialize database and services
    data_path = "data"
    os.makedirs(data_path, exist_ok=True)

    try:
        db = DB(path=f"{data_path}/db.db")
        store = Store(db)
        vdb = VectorDb(path=data_path)

        # Setup example project
        project_id, corpus_id, test_id = await setup_example_project(db, store)

        # Run complete workflow
        result = await run_workflow_example(db, store, vdb, project_id, corpus_id, test_id)

        if result:
            # Demonstrate search functionality
            await demonstrate_search(db, store, vdb, test_id)

            # Demonstrate LLM integration
            await demonstrate_llm_integration()

            print("\n🎉 Example completed successfully!")
            print("\n📋 Summary:")
            print(f"   • Project: {PROJECT_NAME}")
            print(f"   • Test: {TEST_NAME}")
            print(f"   • Collection: {result.collection_name}")
            print(f"   • Total chunks: {result.chunking_summary['total_chunks']}")
            print(f"   • Total embeddings: {result.embedding_summary['total_embeddings']}")

            print("\n🔗 Available API endpoints:")
            print("   • POST /workflow/process-corpus - Process new corpus")
            print("   • POST /workflow/update-corpus - Update existing corpus")
            print("   • GET /workflow/status/{test_id} - Get workflow status")
            print("   • POST /workflow/test/{test_id}/search - Search collection")
            print("   • GET /workflow/collections/{test_id} - List collections")

        # Cleanup
        db.close()

    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
