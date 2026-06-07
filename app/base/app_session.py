import logging
from typing import Any, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class AppSession:
    """
    Wraps a raw SQLAlchemy Session and adds:
      - user identity binding (set once per request, cannot be changed)
      - consistent add / flush / commit / rollback / close helpers
      - pre_commit / post_commit hooks for audit logs, events, etc.

    This is the object that repositories and services receive instead of
    a bare sqlalchemy.orm.Session.
    """

    def __init__(self, sa_session: Session) -> None:
        self.session: Session = sa_session
        self._user_id: Optional[str] = None

    # ── identity ─────────────────────────────────────────────────────────────

    def set_user(self, user_id: str) -> None:
        """Bind a user to this session. Can only be set once per request."""
        if self._user_id is None:
            self._user_id = user_id
        else:
            raise ValueError("User ID is already set and cannot be changed.")

    def get_user(self) -> Optional[str]:
        return self._user_id

    # ── lifecycle hooks (override in subclasses) ──────────────────────────────

    def pre_commit(self) -> None:
        """Called automatically before every commit. Override to add audit logic."""
        pass

    def post_commit(self) -> None:
        """Called automatically after every successful commit."""
        pass

    # ── session operations ────────────────────────────────────────────────────

    def add(self, obj: Any) -> None:
        try:
            self.session.add(obj)
        except Exception as e:
            self.rollback()
            logger.error(f"Error during add: {e}")
            raise

    def add_all(self, objs: List[Any]) -> None:
        try:
            self.session.add_all(objs)
        except Exception as e:
            self.rollback()
            logger.error(f"Error during add_all: {e}")
            raise

    def flush(self) -> None:
        try:
            self.session.flush()
        except Exception as e:
            self.rollback()
            logger.error(f"Error during flush: {e}")
            raise

    def commit(self) -> None:
        self.pre_commit()
        try:
            self.session.commit()
            self.post_commit()
        except Exception as e:
            self.rollback()
            logger.error(f"Error during commit: {e}")
            raise

    def rollback(self) -> None:
        self.session.rollback()

    def close(self) -> None:
        self.session.close()

    def refresh(self, obj: Any) -> None:
        try:
            self.session.refresh(obj)
        except Exception as e:
            self.rollback()
            logger.error(f"Error refreshing object: {e}")
            raise

    def delete(self, obj: Any) -> None:
        try:
            self.session.delete(obj)
        except Exception as e:
            self.rollback()
            logger.error(f"Error deleting object: {e}")
            raise

    def get(self, model: Type[ModelType], id: Any) -> Optional[ModelType]:
        try:
            return self.session.get(model, id)
        except Exception as e:
            self.rollback()
            logger.error(f"Error getting object: {e}")
            raise

    def query(self, *entities: Type[ModelType]) -> Any:
        try:
            return self.session.query(*entities)
        except Exception as e:
            self.rollback()
            logger.error(f"Error querying database: {e}")
            raise
