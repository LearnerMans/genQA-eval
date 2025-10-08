#!/usr/bin/env python3
"""
Test script to verify the RAG evaluation workflow system is working correctly.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_imports():
    """Test that all main components can be imported."""
    print("🧪 Testing system imports...")

    try:
        # Test main app
        from main import app
        print("   ✅ FastAPI app imported successfully")

        # Test services
        from services import (
            TextExtractionService,
            ChunkingService,
            EmbeddingService,
            WorkflowService,
            progress_tracker
        )
        print("   ✅ All services imported successfully")

        # Test database components
        from db.db import DB
        from repos.store import Store
        print("   ✅ Database components imported successfully")

        # Test vector database
        from vectorDb.db import VectorDb
        print("   ✅ Vector database imported successfully")

        # Test LLM components
        from llm import get_llm, get_embedding_model
        print("   ✅ LLM components imported successfully")

        return True

    except Exception as e:
        print(f"   ❌ Import error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_route_registration():
    """Test that routes are properly registered."""
    print("\n🛣️  Testing route registration...")

    try:
        from main import app

        routes = [route for route in app.routes if hasattr(route, 'path')]
        workflow_routes = [route for route in routes if 'workflow' in str(route.path)]
        websocket_routes = [route for route in routes if 'ws' in str(route.path)]

        print(f"   📋 Total routes: {len(routes)}")
        print(f"   🔧 Workflow routes: {len(workflow_routes)}")
        print(f"   🌐 WebSocket routes: {len(websocket_routes)}")

        # Check for key routes
        key_routes = [
            '/workflow/process-corpus',
            '/workflow/progress/dashboard',
            '/ws/progress/active'
        ]

        for key_route in key_routes:
            route_exists = any(key_route in str(route.path) for route in routes)
            status = "✅" if route_exists else "❌"
            print(f"   {status} {key_route}")

        return len(workflow_routes) > 0 and len(websocket_routes) > 0

    except Exception as e:
        print(f"   ❌ Route test error: {str(e)}")
        return False

def test_database_connection():
    """Test database connection."""
    print("\n💾 Testing database connection...")

    try:
        from db.db import DB

        # Test database initialization
        test_db_path = "data/test_db.db"
        db = DB(test_db_path)

        # Test basic query
        cur = db.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        result = cur.fetchone()

        db.close()
        print("   ✅ Database connection successful")

        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        return True

    except Exception as e:
        print(f"   ❌ Database connection error: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 RAG Evaluation Workflow System - Integration Test")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Route Registration Test", test_route_registration),
        ("Database Connection Test", test_database_connection),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"   🎉 {test_name} PASSED")
        else:
            print(f"   💥 {test_name} FAILED")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\n🚀 Next steps:")
        print("   1. Start the server: python main.py")
        print("   2. Visit the progress dashboard: http://localhost:8000/workflow/progress/dashboard")
        print("   3. Run an example: python examples/workflow_example.py")
        print("   4. Monitor via WebSocket: ws://localhost:8000/ws/progress/active")

        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
