from abc import ABC, abstractmethod
from contextlib import contextmanager

from app.base.app_session import AppSession
from app.base.base_repository import BaseRepository
from app.base.database_session import get_db_session


class BaseService(ABC):
    """
    All services inherit from this class.

    self.session  → AppSession (injected from the FastAPI dependency)
    self.repository → concrete repo returned by _get_repository()

    Use self.get_db_session() as a context manager whenever you need
    to write to the database:

        with self.get_db_session() as db:
            self.repository.create(MyModel, field=value)

    For nested service-to-service calls, use db.transaction():

        with self.get_db_session() as db:
            with db.transaction():          # savepoint — safe to nest
                other_service.do_work(...)
    """

    def __init__(self, session: AppSession) -> None:
        self.session = session
        self.repository = self._get_repository()

    @abstractmethod
    def _get_repository(self) -> BaseRepository:
        pass

    @contextmanager
    def get_db_session(self):
        with get_db_session(self.session) as db:
            yield db
