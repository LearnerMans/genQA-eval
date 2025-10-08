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

        self.project_repo = ProjectRepo(db)
        self.test_repo = TestRepo(db)
        self.config_repo = ConfigRepo(db)
