# main.py
from vectorDb.db import VectorDb
from db.db import DB
from repos.store import Store
from handlers.project_handler import router as project_router
from handlers.tests_handler import router as test_router
from handlers.config_handler import router as config_router
from handlers.corpus_handler import router as corpus_router
from handlers.corpus_item_file_handler import router as corpus_file_router
from handlers.corpus_item_url_handler import router as corpus_url_router
from handlers.corpus_items_handler import router as corpus_items_router
from handlers.workflow_handler import router as workflow_router
from handlers.websocket_handler import router as websocket_router
from handlers.qa_handler import router as qa_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

DATA_PATH = r"C:/Users/abdullah.alzariqi/Desktop/LLM/Rag Eval Core/data"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) init
    app.state.vdb = VectorDb(path=DATA_PATH)
    app.state.db = DB(path=DATA_PATH+"/db.db")
    app.state.store = Store(app.state.db)
    # 2) print
    print("Hello from rag-eval-core!")
    yield
    # (optional) teardown on shutdown:
    # app.state.vdb.close()  # if your VectorDb exposes a close

app = FastAPI(
    title="RAG Eval Core API",
    description="API for managing RAG (Retrieval-Augmented Generation) evaluation projects, tests, corpus, configurations, evaluations, and vector database interactions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS (note: '*' cannot be used with allow_credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # use explicit origins if you need credentials
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(project_router)
app.include_router(test_router)
app.include_router(config_router)
app.include_router(corpus_router)
app.include_router(corpus_file_router)
app.include_router(corpus_url_router)
app.include_router(corpus_items_router)
app.include_router(workflow_router)
app.include_router(websocket_router)
app.include_router(qa_router)

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "RAG Eval Core API is running", "status": "healthy"}
