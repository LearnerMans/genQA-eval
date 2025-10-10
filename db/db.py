import sqlite3
import logging
import os
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)

class DBConnectionErr(Exception):
    """Base class for DB-related errors."""

class DB:
    def __init__(self, path: str):
        self.path = path  # e.g., r"C:\Users\...\Rag Eval Core\data\rag_eval.db"
        # Ensure parent directory exists
        parent = os.path.dirname(self.path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        self.conn = self._con()
        self.cur = self.conn.cursor()

        # Enforce foreign keys at connection level
        self.cur.execute("PRAGMA foreign_keys = ON;")
        # Optional but useful for desktop apps
        self.cur.execute("PRAGMA journal_mode = WAL;")
        self.cur.execute("PRAGMA synchronous = NORMAL;")

        # Initialize schema
        try:
            self.conn.executescript(self._init_query())
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DBConnectionErr("Was not able to execute init query") from e

        # Lightweight migrations for existing databases
        try:
            # Ensure test_runs.prompt_id exists (added to link a run to a prompt)
            cur = self.conn.execute("PRAGMA table_info('test_runs')")
            cols = [row[1] for row in cur.fetchall()]
            if 'prompt_id' not in cols:
                with self._tx():
                    # Add column without FK constraint due to SQLite limitations on ALTER TABLE
                    self.conn.execute("ALTER TABLE test_runs ADD COLUMN prompt_id TEXT")
        except Exception:
            # Best-effort; do not crash app if migration fails
            pass

    def _con(self) -> sqlite3.Connection:
        try:
            # For desktop apps, check_same_thread=False can be handy if you’ll hit from multiple threads.
            return sqlite3.connect(self.path, check_same_thread=False)
        except Exception as e:
            logging.error("Error connecting to db at %s", self.path)
            raise DBConnectionErr("Was not able to connect to db") from e

    @contextmanager
    def _tx(self):
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def execute(self, query: str, params: tuple = ()):
        """Execute a single statement and return the cursor."""
        try:
            with self._tx():
                cur = self.conn.execute(query, params)
            return cur
        except Exception as e:
            logging.error("DB execute failed: %s; params=%s", query, params)
            raise DBConnectionErr(str(e)) from e

    def executescript(self, script: str):
        """Execute multiple statements (DDL, etc.)."""
        try:
            with self._tx():
                self.conn.executescript(script)
        except Exception as e:
            logging.error("DB executescript failed")
            raise DBConnectionErr("DB executescript failed") from e

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def _init_query(self) -> str:
        # Your schema, unchanged except executed via executescript.
        return """PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS tests (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TIMESTAMP DEFAULT NULL,
  UNIQUE (project_id, name),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS prompts(
  id TEXT PRIMARY KEY,
  test_id TEXT NOT NULL,
  name TEXT NOT NULL,
  prompt TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TIMESTAMP DEFAULT NULL,
  FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS corpus (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TIMESTAMP DEFAULT NULL,
  UNIQUE (project_id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS config (
  id TEXT PRIMARY KEY,
  test_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('semantic','recursive')),
  chunk_size INTEGER NOT NULL CHECK (chunk_size BETWEEN 0 AND 5000),
  overlap INTEGER NOT NULL CHECK (overlap BETWEEN 0 AND 500),
  generative_model TEXT NOT NULL DEFAULT 'openai_4o',
  embedding_model TEXT NOT NULL DEFAULT 'openai_text_embedding_large_3',
  top_k INTEGER NOT NULL DEFAULT 10 CHECK (top_k >= 1),
  FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS test_runs (
  id TEXT PRIMARY KEY,
  test_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  prompt_id TEXT,
  FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (config_id) REFERENCES config(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS corpus_item_url (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  corpus_id TEXT NOT NULL,
  url TEXT NOT NULL,
  content TEXT DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  extraction_at TIMESTAMP DEFAULT NULL,
  updated_at TIMESTAMP DEFAULT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
  FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE ON UPDATE CASCADE

);

CREATE TABLE IF NOT EXISTS corpus_item_file (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
    corpus_id TEXT NOT NULL,
  name TEXT NOT NULL,
  ext TEXT NOT NULL,
  content TEXT DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  extraction_at TIMESTAMP DEFAULT NULL,
  updated_at TIMESTAMP DEFAULT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
    FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE ON UPDATE CASCADE

);

CREATE TABLE IF NOT EXISTS question_answer_pairs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  hash TEXT NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  UNIQUE (project_id, hash),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS evals (
  id TEXT PRIMARY KEY,
  test_run_id TEXT NOT NULL,
  qa_pair_id TEXT NOT NULL,
  bleu REAL,
  rouge REAL,
  answer_relevance REAL,
  context_relevance REAL,
  groundedness REAL,
  FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (qa_pair_id) REFERENCES question_answer_pairs(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('url','file')),
  path_or_link TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('url','file')),
  source_id TEXT NOT NULL,
  content TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS eval_chunks (
  eval_id TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  PRIMARY KEY (eval_id, chunk_id),
  FOREIGN KEY (eval_id) REFERENCES evals(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE ON UPDATE CASCADE
);

            
            """
