import logging
from typing import Any, List, Optional, Type, TypeVar

from app.base.app_session import AppSession

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class BaseRepository:
    """
    All repositories inherit from this class.

    Receives an AppSession (not a raw sqlalchemy Session).
    All DB access goes through self.db which is the AppSession,
    so operations benefit from the consistent error-handling,
    rollback-on-error, and lifecycle management in AppSession.
    """

    def __init__(self, db: AppSession) -> None:
        self.db = db

    # ── write ─────────────────────────────────────────────────────────────────

    def create(self, model_class: Type[ModelType], **kwargs) -> ModelType:
        obj = model_class(**kwargs)
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update(self, db_obj: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            if hasattr(db_obj, key) and value is not None:
                setattr(db_obj, key, value)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        self.db.delete(db_obj)
        self.db.flush()

    def delete_by_query(self, model_class: Type[ModelType], **filters) -> int:
        query = self.db.query(model_class)
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model_class, key) == value)
        count = query.delete(synchronize_session=False)
        self.db.flush()
        return count

    # ── read ──────────────────────────────────────────────────────────────────

    def get_by_id(self, model_class: Type[ModelType], record_id: Any) -> Optional[ModelType]:
        return self.db.get(model_class, record_id)

    def get_one(self, model_class: Type[ModelType], **filters) -> Optional[ModelType]:
        query = self.db.query(model_class)
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model_class, key) == value)
        return query.first()

    def list(self, model_class: Type[ModelType], **filters) -> List[ModelType]:
        query = self.db.query(model_class)
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model_class, key) == value)
        return query.all()

    # ── utility ───────────────────────────────────────────────────────────────

    def _to_dict(self, obj: Any) -> dict:
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            result[column.name] = value
        return result
