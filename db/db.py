import sqlite3
import logging
import os
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

            # Ensure sources.test_id exists so chunks can be tied to a test for cleanup
            cur = self.conn.execute("PRAGMA table_info('sources')")
            cols = [row[1] for row in cur.fetchall()]
            if 'test_id' not in cols:
                with self._tx():
                    self.conn.execute("ALTER TABLE sources ADD COLUMN test_id TEXT")
                    # Create an index to speed up deletions/lookups by test
                    self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_test_id ON sources(test_id)")

            # Ensure evals.answer exists (added for storing generated answers)
            cur = self.conn.execute("PRAGMA table_info('evals')")
            cols = [row[1] for row in cur.fetchall()]
            if 'answer' not in cols:
                with self._tx():
                    self.conn.execute("ALTER TABLE evals ADD COLUMN answer TEXT")

            # Migrate evals table to support comprehensive metrics
            cur = self.conn.execute("PRAGMA table_info('evals')")
            cols = [row[1] for row in cur.fetchall()]

            # Add lexical metrics if missing
            migrations_needed = []
            if 'rouge_l_precision' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN rouge_l_precision REAL")
            if 'rouge_l_recall' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN rouge_l_recall REAL")
            if 'squad_em' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN squad_em REAL")
            if 'squad_token_f1' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN squad_token_f1 REAL")
            if 'content_f1' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN content_f1 REAL")
            if 'lexical_aggregate' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN lexical_aggregate REAL")
            if 'llm_judged_overall' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN llm_judged_overall REAL")
            if 'answer_relevance_reasoning' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN answer_relevance_reasoning TEXT")
            if 'context_relevance_reasoning' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN context_relevance_reasoning TEXT")
            if 'groundedness_reasoning' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN groundedness_reasoning TEXT")
            if 'context_relevance_per_context' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN context_relevance_per_context TEXT")
            if 'groundedness_supported_claims' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN groundedness_supported_claims INTEGER")
            if 'groundedness_total_claims' not in cols:
                migrations_needed.append("ALTER TABLE evals ADD COLUMN groundedness_total_claims INTEGER")

            # Rename rouge to rouge_l if needed
            if 'rouge' in cols and 'rouge_l' not in cols:
                # SQLite doesn't support RENAME COLUMN directly in older versions
                # We'll add rouge_l and copy data
                migrations_needed.append("ALTER TABLE evals ADD COLUMN rouge_l REAL")

            if migrations_needed:
                with self._tx():
                    for migration in migrations_needed:
                        self.conn.execute(migration)
                    # Copy rouge to rouge_l if both exist now
                    if 'rouge' in cols:
                        self.conn.execute("UPDATE evals SET rouge_l = rouge WHERE rouge_l IS NULL")

            # Ensure only one eval per (test_run_id, qa_pair_id)
            # Create a unique index to enforce the constraint where possible
            try:
                with self._tx():
                    self.conn.execute(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_evals_run_qa_unique ON evals(test_run_id, qa_pair_id)"
                    )
            except Exception:
                # If duplicates exist, index creation may fail; app-level logic overwrites on save
                pass

            # Ensure chunks.metadata exists (added for FAQ support to store question)
            cur = self.conn.execute("PRAGMA table_info('chunks')")
            cols = [row[1] for row in cur.fetchall()]
            if 'metadata' not in cols:
                with self._tx():
                    self.conn.execute("ALTER TABLE chunks ADD COLUMN metadata TEXT")

            # Migrate sources and chunks tables to support 'faq' type
            # SQLite doesn't allow modifying CHECK constraints, so we need to recreate tables
            logger.info("Checking if FAQ migration is needed...")
            needs_migration = False

            # Try to insert a test 'faq' record to see if constraint allows it
            test_id = '__migration_test__'
            try:
                self.conn.execute("BEGIN")
                self.conn.execute(
                    "INSERT INTO sources (id, type, path_or_link) VALUES (?, ?, ?)",
                    (test_id, 'faq', 'test')
                )
                # If successful, delete it and we're good
                self.conn.execute("DELETE FROM sources WHERE id = ?", (test_id,))
                self.conn.commit()
                logger.info("FAQ type already supported in sources table")
            except sqlite3.IntegrityError as e:
                # Constraint doesn't allow 'faq', need to migrate
                self.conn.rollback()
                if "CHECK constraint failed" in str(e):
                    needs_migration = True
                    logger.info("FAQ migration needed - CHECK constraint doesn't include 'faq'")
                else:
                    logger.warning(f"Unexpected integrity error during FAQ check: {e}")

            if needs_migration:
                try:
                    logger.info("Starting FAQ migration: recreating sources and chunks tables...")

                    # Disable foreign keys temporarily
                    self.conn.execute("PRAGMA foreign_keys = OFF")

                    # Create temporary tables with new constraints
                    self.conn.execute("""
                        CREATE TABLE sources_new (
                          id TEXT PRIMARY KEY,
                          type TEXT NOT NULL CHECK (type IN ('url','file','faq')),
                          path_or_link TEXT NOT NULL,
                          test_id TEXT
                        )
                    """)

                    self.conn.execute("""
                        CREATE TABLE chunks_new (
                          id TEXT PRIMARY KEY,
                          type TEXT NOT NULL CHECK (type IN ('url','file','faq')),
                          source_id TEXT NOT NULL,
                          content TEXT NOT NULL,
                          chunk_index INTEGER NOT NULL,
                          metadata TEXT
                        )
                    """)

                    # Copy data from old tables
                    logger.info("Copying data from old sources table...")
                    self.conn.execute("INSERT INTO sources_new (id, type, path_or_link, test_id) SELECT id, type, path_or_link, test_id FROM sources")

                    logger.info("Copying data from old chunks table...")
                    # Check if metadata column exists in old chunks table
                    cur = self.conn.execute("PRAGMA table_info('chunks')")
                    old_chunks_cols = [row[1] for row in cur.fetchall()]
                    if 'metadata' in old_chunks_cols:
                        self.conn.execute("INSERT INTO chunks_new SELECT * FROM chunks")
                    else:
                        self.conn.execute("INSERT INTO chunks_new (id, type, source_id, content, chunk_index, metadata) SELECT id, type, source_id, content, chunk_index, NULL FROM chunks")

                    # Drop old tables (drop chunks first due to foreign key)
                    logger.info("Dropping old tables...")
                    self.conn.execute("DROP TABLE chunks")
                    self.conn.execute("DROP TABLE sources")

                    # Rename new tables
                    logger.info("Renaming new tables...")
                    self.conn.execute("ALTER TABLE sources_new RENAME TO sources")
                    self.conn.execute("ALTER TABLE chunks_new RENAME TO chunks")

                    # Recreate index
                    logger.info("Recreating indexes...")
                    self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_test_id ON sources(test_id)")

                    # Re-enable foreign keys
                    self.conn.execute("PRAGMA foreign_keys = ON")

                    self.conn.commit()
                    logger.info("✅ Successfully migrated sources and chunks tables for FAQ support!")

                except Exception as e:
                    self.conn.rollback()
                    self.conn.execute("PRAGMA foreign_keys = ON")
                    logger.error(f"❌ FAQ migration failed: {e}")
                    raise

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
  training_status TEXT NOT NULL DEFAULT 'not_started' CHECK (training_status IN ('not_started', 'in_progress', 'completed', 'failed')),
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

CREATE TABLE IF NOT EXISTS corpus_item_faq (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  corpus_id TEXT NOT NULL,
  name TEXT NOT NULL,
  embedding_mode TEXT NOT NULL DEFAULT 'both' CHECK (embedding_mode IN ('question_only', 'both')),
  created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  extraction_at TIMESTAMP DEFAULT NULL,
  updated_at TIMESTAMP DEFAULT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (corpus_id) REFERENCES corpus(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS faq_pairs (
  id TEXT PRIMARY KEY,
  faq_item_id TEXT NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  row_index INTEGER NOT NULL,
  FOREIGN KEY (faq_item_id) REFERENCES corpus_item_faq(id) ON DELETE CASCADE ON UPDATE CASCADE
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
  rouge_l REAL,
  rouge_l_precision REAL,
  rouge_l_recall REAL,
  squad_em REAL,
  squad_token_f1 REAL,
  content_f1 REAL,
  lexical_aggregate REAL,
  answer_relevance REAL,
  context_relevance REAL,
  groundedness REAL,
  llm_judged_overall REAL,
  answer TEXT,
  answer_relevance_reasoning TEXT,
  context_relevance_reasoning TEXT,
  groundedness_reasoning TEXT,
  context_relevance_per_context TEXT,
  groundedness_supported_claims INTEGER,
  groundedness_total_claims INTEGER,
  FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (qa_pair_id) REFERENCES question_answer_pairs(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('url','file','faq')),
  path_or_link TEXT NOT NULL,
  test_id TEXT,
  FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('url','file','faq')),
  source_id TEXT NOT NULL,
  content TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  metadata TEXT,
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
