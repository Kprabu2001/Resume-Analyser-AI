from abc import ABC, abstractmethod
from contextlib import contextmanager

from app.base.app_session import AppSession
from app.base.base_repository import BaseRepository
from app.base.database_session import get_db_session


class BaseService(ABC):

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
