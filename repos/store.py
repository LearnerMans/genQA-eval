from abc import ABC, abstractmethod
from typing import List, Dict, Any
from db.db import DB

class Repository(ABC):
    """Abstract base class for repository pattern."""

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all items from the repository."""
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item in the repository."""
        pass

    @abstractmethod
    def delete_by_id(self, id: str) -> bool:
        """Delete an item by its ID. Returns True if deleted, False if not found."""
        pass


class Store:
    """Container class that holds all repositories."""

    def __init__(self, db: DB):
        from repos.project_repo import ProjectRepo
        from repos.test_repo import TestRepo
        from repos.config_repo import ConfigRepo
        from repos.corpus_repo import CorpusRepo
        from repos.corpus_item_file_repo import CorpusItemFileRepo
        from repos.corpus_item_url_repo import CorpusItemUrlRepo
        from repos.corpus_item_faq_repo import CorpusItemFAQRepo
        from repos.qa_repo import QARepo
        from repos.prompt_repo import PromptRepo
        from repos.test_run_repo import TestRunRepo
        from repos.eval_repo import EvalRepo

        self.project_repo = ProjectRepo(db)
        self.test_repo = TestRepo(db)
        self.config_repo = ConfigRepo(db)
        self.corpus_repo = CorpusRepo(db)
        self.corpus_item_file_repo = CorpusItemFileRepo(db)
        self.corpus_item_url_repo = CorpusItemUrlRepo(db)
        self.corpus_item_faq_repo = CorpusItemFAQRepo(db)
        self.qa_repo = QARepo(db)
        self.prompt_repo = PromptRepo(db)
        self.test_run_repo = TestRunRepo(db)
        self.eval_repo = EvalRepo(db)
