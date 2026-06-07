import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy import asc, desc, or_, and_

from app.base.app_session import AppSession
from app.base.base import Filter, FilterExpression, FilterNode, LogicalFilter, Operator

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

    def delete_by_query(self, model_class: Type[ModelType], filters: Optional[FilterNode] = None, **kwargs) -> int:
        query = self.db.query(model_class)
        if filters is not None:
            query = self._apply_filters(query, model_class, filters)
        if kwargs:
            for key, value in kwargs.items():
                if value is not None:
                    query = query.filter(getattr(model_class, key) == value)
        count = query.delete(synchronize_session=False)
        self.db.flush()
        return count

    # ── read ──────────────────────────────────────────────────────────────────

    def get_by_id(self, model_class: Type[ModelType], record_id: Any) -> Optional[ModelType]:
        return self.db.get(model_class, record_id)

    def get_one(self, model_class: Type[ModelType], filters: Optional[FilterNode] = None, **kwargs) -> Optional[ModelType]:
        query = self.db.query(model_class)
        if filters is not None:
            query = self._apply_filters(query, model_class, filters)
        if kwargs:
            for key, value in kwargs.items():
                if value is not None:
                    query = query.filter(getattr(model_class, key) == value)
        return query.first()

    def list(
        self,
        model_class: Type[ModelType],
        filters: Optional[FilterNode] = None,
        sort_by: Optional[List[Dict[str, str]]] = None,
        skip: int = 0,
        limit: int = 100,
        **kwargs,
    ) -> List[ModelType]:
        query = self.db.query(model_class)
        if filters is not None:
            query = self._apply_filters(query, model_class, filters)
        if kwargs:
            for key, value in kwargs.items():
                if value is not None:
                    query = query.filter(getattr(model_class, key) == value)
        if sort_by:
            query = self._apply_sorting(query, model_class, sort_by)
        return query.offset(skip).limit(limit).all()

    # ── filtering ─────────────────────────────────────────────────────────────

    def _apply_filters(self, query, model: Type[ModelType], filters: FilterNode):
        """
        Convert FilterNode tree to SQLAlchemy filter expressions.
        """
        if isinstance(filters, Filter):
            column = getattr(model, filters.field)
            expr = filters.expression
            op = expr.op.value
            val = expr.value

            match op:
                case "eq":
                    return query.filter(column == val)
                case "ne":
                    return query.filter(column != val)
                case "gt":
                    return query.filter(column > val)
                case "lt":
                    return query.filter(column < val)
                case "gte":
                    return query.filter(column >= val)
                case "lte":
                    return query.filter(column <= val)
                case "in_":
                    return query.filter(column.in_(val))
                case "nin":
                    return query.filter(~column.in_(val))
                case "between":
                    return query.filter(column.between(val[0], val[1]))
                case "contains":
                    return query.filter(column.contains(val))
                case "contains_any":
                    conds = [column.contains([v]) for v in val]
                    return query.filter(or_(*conds))
                case _:
                    raise ValueError(f"Unsupported operator: {op}")

        if isinstance(filters, LogicalFilter):
            if filters.and_:
                for child in filters.and_:
                    query = self._apply_filters(query, model, child)
                return query

            if filters.or_:
                conditions = []
                for child in filters.or_:
                    sub_q = self._apply_filters(self.db.query(model), model, child)
                    conditions.append(sub_q._criterion)
                return query.filter(or_(*conditions))

        raise ValueError("Invalid filter structure")

    def _apply_sorting(self, query, model: Type[ModelType], sort_by: List[Dict[str, str]]):
        for sort in sort_by:
            field = sort.get("field")
            order = sort.get("order", "asc")
            if not field:
                continue
            column = getattr(model, field)
            query = query.order_by(desc(column) if order == "desc" else asc(column))
        return query

    # ── utility ───────────────────────────────────────────────────────────────

    def _to_dict(self, obj: Any) -> dict:
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            result[column.name] = value
        return result
