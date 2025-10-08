"""
Example demonstrating live progress tracking for RAG evaluation workflows.

This example shows how to:
1. Set up a workflow with progress tracking
2. Monitor progress in real-time via WebSocket
3. Use the progress dashboard
4. Handle progress callbacks
"""
import asyncio
import json
import os
import time
import uuid
import websockets
from typing import Dict, Any

from db.db import DB
from repos.store import Store
from services.workflow_service import WorkflowService
from services.progress_tracker import progress_tracker, WorkflowProgress
from vectorDb.db import VectorDb

# Example configuration
PROJECT_NAME = "Progress Tracking Demo"
TEST_NAME = "Live Progress Test"
CORPUS_NAME = "Demo Documents"

# Sample content for demonstration
SAMPLE_FILES = [
    # Add some sample files if available
]

SAMPLE_URLS = [
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    "https://en.wikipedia.org/wiki/Vector_database",
    "https://en.wikipedia.org/wiki/Natural_language_processing"
]

def progress_callback(workflow: WorkflowProgress):
    """Example progress callback function."""
    print(f"\n📊 Progress Update for {workflow.test_id}:")
    print(f"   Status: {workflow.status}")
    print(f"   Overall Progress: {workflow.overall_progress:.1f}%")
    print(f"   Duration: {workflow.duration:.1f}s")

    if workflow.current_step and workflow.current_step in workflow.steps:
        current = workflow.steps[workflow.current_step]
        print(f"   Current Step: {current.name} ({current.progress_percentage:.1f}%)")

    print(f"   Active Steps: {len([s for s in workflow.steps.values() if s.status == 'running'])}")

async def run_workflow_with_progress_monitoring():
    """Run a workflow with comprehensive progress monitoring."""

    print("🚀 RAG Evaluation Workflow with Live Progress Tracking")
    print("=" * 60)

    # Initialize services
    data_path = "data"
    os.makedirs(data_path, exist_ok=True)

    try:
        db = DB(path=f"{data_path}/db.db")
        store = Store(db)
        vdb = VectorDb(path=data_path)

        # Setup example project
        print("📋 Setting up example project...")

        project_data = {"name": PROJECT_NAME}
        project = store.project_repo.create(project_data)

        corpus_data = {"project_id": project["id"], "name": CORPUS_NAME}
        corpus = store.corpus_repo.create(corpus_data)

        test_data = {"project_id": project["id"], "name": TEST_NAME}
        test = store.test_repo.create(test_data)

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

        print(f"✅ Created test: {test['name']} (ID: {test['id']})")

        # Register progress callback
        progress_tracker.add_progress_callback(progress_callback)

        # Initialize workflow service
        workflow_service = WorkflowService(db, store, vdb)

        print("\n🎯 Starting workflow with progress tracking...")
        print("📊 Monitor progress at: http://localhost:8000/workflow/progress/dashboard")
        print("🔗 WebSocket endpoint: ws://localhost:8000/ws/progress/active")
        print("⏳ This will take some time...")

        # Run the workflow
        start_time = time.time()

        result = await workflow_service.process_test_corpus(
            test_id=test["id"],
            project_id=project["id"],
            corpus_id=corpus["id"],
            file_paths=SAMPLE_FILES if SAMPLE_FILES else None,
            urls=SAMPLE_URLS if SAMPLE_URLS else None,
            crawl_depth=1,
            embedding_model_name="openai_text_embedding_large_3"
        )

        total_time = time.time() - start_time

        if result.success:
            print("\n🎉 Workflow completed successfully!")
            print(f"⏱️  Total execution time: {total_time:.2f}")
            print("📊 Final statistics:")
            print(f"   • Collection: {result.collection_name}")
            print(f"   • Sources processed: {result.extraction_summary['total_sources']}")
            print(f"   • Chunks created: {result.chunking_summary['total_chunks']}")
            print(f"   • Embeddings generated: {result.embedding_summary['total_embeddings']}")

            return result
        else:
            print(f"\n❌ Workflow failed: {result.error_message}")
            return None

    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def demonstrate_websocket_monitoring():
    """Demonstrate WebSocket-based progress monitoring."""

    print("\n🔗 Demonstrating WebSocket Progress Monitoring")
    print("=" * 50)

    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/ws/progress/active"

        async with websockets.connect(uri) as websocket:
            print(f"🔌 Connected to WebSocket: {uri}")

            # Listen for progress updates
            print("📡 Listening for progress updates...")

            message_count = 0
            start_time = time.time()

            while time.time() - start_time < 60:  # Listen for 1 minute
                try:
                    # Receive message
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)

                    message_count += 1

                    if data.get("type") == "progress_update":
                        workflow_data = data.get("data", {})
                        print(f"\n📊 Update #{message_count}:")
                        print(f"   Test: {workflow_data.get('test_id')}")
                        print(f"   Status: {workflow_data.get('status')}")
                        print(f"   Progress: {workflow_data.get('overall_progress', 0):.1f}%")

                        # Show current step details
                        current_step = workflow_data.get('current_step')
                        if current_step and current_step in workflow_data.get('steps', {}):
                            step = workflow_data['steps'][current_step]
                            print(f"   Current: {step['name']} ({step['progress_percentage']:.1f}%)")

                    # Send ping to keep connection alive
                    await websocket.send(json.dumps({"type": "ping"}))

                except asyncio.TimeoutError:
                    # Send ping if no message received
                    await websocket.send(json.dumps({"type": "ping"}))
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket connection closed")
                    break

            print(f"\n📡 Received {message_count} progress updates")

    except Exception as e:
        print(f"❌ WebSocket demonstration failed: {str(e)}")
        print("   Make sure the server is running on localhost:8000")

async def demonstrate_http_polling():
    """Demonstrate HTTP polling for progress monitoring."""

    print("\n🌐 Demonstrating HTTP Polling Progress Monitoring")
    print("=" * 50)

    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            print("📡 Polling progress endpoint...")

            poll_count = 0
            start_time = time.time()

            while time.time() - start_time < 60:  # Poll for 1 minute
                try:
                    async with session.get('http://localhost:8000/ws/progress/active') as response:
                        if response.status == 200:
                            data = await response.json()

                            poll_count += 1

                            if data.get('active_workflows'):
                                workflow = data['active_workflows'][0]  # Show first workflow
                                print(f"\n📊 Poll #{poll_count}:")
                                print(f"   Test: {workflow.get('test_id')}")
                                print(f"   Status: {workflow.get('status')}")
                                print(f"   Progress: {workflow.get('overall_progress', 0):.1f}%")

                                # Show step details
                                for step_id, step in workflow.get('steps', {}).items():
                                    if step['status'] == 'running':
                                        print(f"   Current: {step['name']} ({step['progress_percentage']:.1f}%)")
                                        break
                            else:
                                print(f"\n📊 Poll #{poll_count}: No active workflows")

                    await asyncio.sleep(3)  # Poll every 3 seconds

                except Exception as e:
                    print(f"❌ Polling error: {str(e)}")
                    break

            print(f"\n📡 Completed {poll_count} polling requests")

    except Exception as e:
        print(f"❌ HTTP polling demonstration failed: {str(e)}")

async def demonstrate_server_sent_events():
    """Demonstrate Server-Sent Events for progress monitoring."""

    print("\n📡 Demonstrating Server-Sent Events Progress Monitoring")
    print("=" * 50)

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Connect to SSE endpoint
            async with session.get('http://localhost:8000/workflow/progress/test/stream') as response:
                print(f"🔌 Connected to SSE endpoint (status: {response.status})")

                if response.status != 200:
                    print(f"❌ Failed to connect to SSE: {response.status}")
                    return

                event_count = 0
                start_time = time.time()

                async for line in response.content:
                    if time.time() - start_time > 60:  # Stop after 1 minute
                        break

                    line = line.decode('utf-8').strip()

                    if line.startswith('data: '):
                        event_count += 1
                        data_str = line[6:]  # Remove 'data: ' prefix

                        try:
                            data = json.loads(data_str)

                            if data.get('status') == 'not_found':
                                print(f"\n📊 SSE Event #{event_count}: Workflow not found")
                            else:
                                print(f"\n📊 SSE Event #{event_count}:")
                                print(f"   Test: {data.get('test_id')}")
                                print(f"   Status: {data.get('status')}")
                                print(f"   Progress: {data.get('overall_progress', 0):.1f}%")

                        except json.JSONDecodeError:
                            print(f"❌ Invalid JSON in SSE data: {data_str}")

                print(f"\n📡 Received {event_count} SSE events")

    except Exception as e:
        print(f"❌ SSE demonstration failed: {str(e)}")

async def main():
    """Main demonstration function."""

    print("🎯 RAG Evaluation Workflow - Progress Tracking Demo")
    print("=" * 60)
    print("This demo shows different ways to monitor workflow progress:")
    print("1. Console callback monitoring")
    print("2. WebSocket real-time updates")
    print("3. HTTP polling")
    print("4. Server-Sent Events (SSE)")
    print("5. Web dashboard")

    # Check if server is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/', timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ Server is running - progress monitoring available")
                else:
                    print(f"⚠️  Server responded with status: {response.status}")
    except Exception:
        print("⚠️  Server not detected - start with: python main.py")
        print("   Progress monitoring will be limited to console output")

    print("\n" + "=" * 60)

    # Run workflow with progress monitoring
    result = await run_workflow_with_progress_monitoring()

    if result:
        print("\n🎉 Demo completed successfully!")

        # Demonstrate different monitoring approaches
        print("\n📊 Monitoring Demonstrations:")
        print("=" * 30)

        # HTTP Polling demo
        await demonstrate_http_polling()

        # SSE demo (requires server running)
        await demonstrate_server_sent_events()

        print("\n🎯 Summary:")
        print("✅ Workflow completed with progress tracking")
        print("✅ Multiple monitoring methods demonstrated")
        print("✅ Real-time updates working")

        print("\n🔗 Access the progress dashboard at:")
        print("   http://localhost:8000/workflow/progress/dashboard")

        print("\n🔌 WebSocket endpoints:")
        print("   ws://localhost:8000/ws/progress/active")
        print("   ws://localhost:8000/ws/progress/{workflow_id}")
        print("   ws://localhost:8000/ws/progress/test/{test_id}")

        print("\n📡 HTTP endpoints:")
        print("   GET /ws/progress/active")
        print("   GET /workflow/progress/{workflow_id}/stream")

    else:
        print("\n❌ Demo failed - check error messages above")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
