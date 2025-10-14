"""
Complete RAG Evaluation Example

This script demonstrates the full pipeline:
1. Generate answer from query using RAG
2. Calculate lexical metrics (BLEU, ROUGE, etc.)
3. Calculate LLM-judged metrics (context relevance, groundedness, answer relevance)
4. Store all results in the database

Prerequisites:
- Set OPENAI_API_KEY in .env file
- Have a populated vector database collection
- Have test runs and QA pairs in the database
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from db.db import DB
from vectorDb.db import VectorDb
from llm.openai_llm import OpenAILLM
from llm.openai_embeddings import OpenAIEmbeddings
from services.rag_eval_service import RAGEvalService
from repos.qa_repo import QARepo

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def single_evaluation_example():
    """Example: Generate and evaluate a single QA pair."""

    print("=" * 80)
    print("SINGLE QA PAIR EVALUATION EXAMPLE")
    print("=" * 80)

    # Initialize services
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "db.db")
    vector_db_path = os.path.join(os.path.dirname(__file__), "..", "data")

    db = DB(db_path)
    vector_db = VectorDb(vector_db_path)

    # Initialize RAG evaluation service
    service = RAGEvalService(
        db=db,
        vector_db=vector_db,
        llm=OpenAILLM(model_name='openai_4o'),
        embeddings=OpenAIEmbeddings(model_name='openai_text_embedding_large_3')
    )

    # Example parameters (you'll need to replace these with actual IDs from your DB)
    test_run_id = "your-test-run-id"  # Get from test_runs table
    qa_pair_id = "your-qa-pair-id"    # Get from question_answer_pairs table
    collection_name = "your-collection-name"  # Your vector collection name

    # Example query and reference answer
    query = "What are the benefits of regular exercise?"
    reference_answer = "Regular exercise improves cardiovascular health, strengthens muscles, helps maintain healthy weight, reduces stress, and improves mental health."

    try:
        print(f"\nQuery: {query}")
        print(f"Collection: {collection_name}")
        print("\nStarting evaluation pipeline...\n")

        # Run complete evaluation
        result = await service.generate_and_evaluate(
            test_run_id=test_run_id,
            qa_pair_id=qa_pair_id,
            query=query,
            reference_answer=reference_answer,
            collection_name=collection_name,
            top_k=10,
            temperature=0.7,
            eval_model="gpt-4o"
        )

        # Display results
        print("\n" + "=" * 80)
        print("EVALUATION RESULTS")
        print("=" * 80)

        print(f"\nEvaluation ID: {result['eval_id']}")

        print(f"\n--- Generated Answer ---")
        print(result['generated_answer'])

        print(f"\n--- Retrieved Contexts ({len(result['contexts'])}) ---")
        for i, ctx in enumerate(result['contexts'][:3], 1):  # Show first 3
            print(f"\nContext {i} (distance: {ctx['distance']:.4f}):")
            print(ctx['content'][:200] + "..." if len(ctx['content']) > 200 else ctx['content'])

        print("\n--- Lexical Metrics ---")
        for metric, score in result['lexical_metrics'].items():
            print(f"  {metric:25s}: {score:.4f}")

        print("\n--- LLM-Judged Metrics (0-3 scale) ---")
        for metric, score in result['llm_judged_metrics'].items():
            print(f"  {metric:25s}: {score:.4f}")

        print("\n" + "=" * 80)
        print("Results saved to database successfully!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error in evaluation: {e}")
        raise
    finally:
        db.close()


async def batch_evaluation_example():
    """Example: Batch evaluation of multiple QA pairs."""

    print("\n\n")
    print("=" * 80)
    print("BATCH EVALUATION EXAMPLE")
    print("=" * 80)

    # Initialize services
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "db.db")
    vector_db_path = os.path.join(os.path.dirname(__file__), "..", "data")

    db = DB(db_path)
    vector_db = VectorDb(vector_db_path)
    qa_repo = QARepo(db)

    # Initialize RAG evaluation service
    service = RAGEvalService(
        db=db,
        vector_db=vector_db,
        llm=OpenAILLM(model_name='openai_4o'),
        embeddings=OpenAIEmbeddings(model_name='openai_text_embedding_large_3')
    )

    # Get QA pairs from database for a specific project
    project_id = "your-project-id"  # Replace with actual project ID
    test_run_id = "your-test-run-id"  # Replace with actual test run ID
    collection_name = "your-collection-name"  # Your vector collection name

    try:
        # Fetch QA pairs from database
        qa_pairs = qa_repo.get_by_project_id(project_id)

        if not qa_pairs:
            print(f"\nNo QA pairs found for project {project_id}")
            return

        print(f"\nFound {len(qa_pairs)} QA pairs")
        print(f"Processing with collection: {collection_name}\n")

        # Run batch evaluation
        results = await service.batch_evaluate(
            test_run_id=test_run_id,
            qa_pairs=qa_pairs,
            collection_name=collection_name,
            top_k=10,
            temperature=0.7,
            eval_model="gpt-4o"
        )

        # Display summary
        print("\n" + "=" * 80)
        print("BATCH EVALUATION SUMMARY")
        print("=" * 80)

        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']

        print(f"\nTotal QA pairs: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")

        if successful:
            print("\n--- Average Scores ---")

            # Calculate averages
            avg_lexical = {}
            avg_llm = {}

            for result in successful:
                metrics = result['result']
                for key, val in metrics['lexical_metrics'].items():
                    avg_lexical[key] = avg_lexical.get(key, 0) + val
                for key, val in metrics['llm_judged_metrics'].items():
                    avg_llm[key] = avg_llm.get(key, 0) + val

            n = len(successful)
            print("\nLexical Metrics (Average):")
            for key, val in avg_lexical.items():
                print(f"  {key:25s}: {val/n:.4f}")

            print("\nLLM-Judged Metrics (Average, 0-3 scale):")
            for key, val in avg_llm.items():
                print(f"  {key:25s}: {val/n:.4f}")

        if failed:
            print("\n--- Failed Evaluations ---")
            for result in failed:
                print(f"  QA Pair {result['qa_pair_id']}: {result['error']}")

        print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error in batch evaluation: {e}")
        raise
    finally:
        db.close()


async def custom_prompt_example():
    """Example: Using a custom prompt template."""

    print("\n\n")
    print("=" * 80)
    print("CUSTOM PROMPT TEMPLATE EXAMPLE")
    print("=" * 80)

    # Initialize services
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "db.db")
    vector_db_path = os.path.join(os.path.dirname(__file__), "..", "data")

    db = DB(db_path)
    vector_db = VectorDb(vector_db_path)

    service = RAGEvalService(
        db=db,
        vector_db=vector_db,
        llm=OpenAILLM(model_name='openai_4o'),
        embeddings=OpenAIEmbeddings(model_name='openai_text_embedding_large_3')
    )

    # Custom prompt template with specific formatting
    custom_template = """You are a medical expert assistant. Answer the patient's question based ONLY on the provided medical literature contexts.

Medical Literature:
{contexts}

Patient Question: {query}

Instructions:
- Provide a clear, evidence-based answer
- Cite which context(s) support your answer
- If the contexts don't contain enough information, say so
- Use simple language that a patient can understand

Answer:"""

    test_run_id = "your-test-run-id"
    qa_pair_id = "your-qa-pair-id"
    collection_name = "your-collection-name"

    query = "What are the side effects of aspirin?"
    reference_answer = "Common side effects include stomach upset, heartburn, and increased bleeding risk."

    try:
        print(f"\nQuery: {query}")
        print("\nUsing custom prompt template...\n")

        result = await service.generate_and_evaluate(
            test_run_id=test_run_id,
            qa_pair_id=qa_pair_id,
            query=query,
            reference_answer=reference_answer,
            collection_name=collection_name,
            top_k=5,
            prompt_template=custom_template,
            temperature=0.5,  # Lower temperature for more consistent answers
            eval_model="gpt-4o"
        )

        print("Generated Answer:")
        print(result['generated_answer'])

        print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        db.close()


async def main():
    """Run all examples."""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env file!")
        print("\nPlease create a .env file in the project root with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        return

    print("\nRAG EVALUATION SERVICE - COMPLETE EXAMPLES")
    print("=" * 80)
    print("\nNOTE: Before running, please update the following in the code:")
    print("  - test_run_id: Your test run ID from the database")
    print("  - qa_pair_id: Your QA pair ID from the database")
    print("  - collection_name: Your vector database collection name")
    print("  - project_id: Your project ID (for batch example)")
    print("\n" + "=" * 80)

    try:
        # Run single evaluation example
        # await single_evaluation_example()

        # Run batch evaluation example
        # await batch_evaluation_example()

        # Run custom prompt example
        # await custom_prompt_example()

        print("\n\nUncomment the examples above to run them!")
        print("Make sure to update the IDs and collection names first.")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
