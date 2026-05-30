from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime
from pydantic import BaseModel,ConfigDict,Field
from typing import Generic, Optional, Type, TypeVar, List, Dict, Any
from sqlalchemy.sql import func
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator
from typing import Union, List, Optional

Base = declarative_base()
# Type variable for the data field
T = TypeVar('T')


class AppBase(Base):
    __abstract__ = True

    # modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Operator(str, Enum):
    eq = "eq"
    ne = "ne"
    gt = "gt"
    lt = "lt"
    gte = "gte"
    lte = "lte"
    in_ = "in"
    nin = "nin"
    between = "between"
    contains = "contains"
    contains_any = "contains_any"

class FilterExpression(BaseModel):
    op: Operator
    value: Any

class Filter(BaseModel):
    field: str
    expression: FilterExpression


class LogicalFilter(BaseModel):
    and_: Optional[List['FilterNode']] = Field(default=None, alias="and")
    or_: Optional[List['FilterNode']] = Field(default=None, alias="or")

    model_config = {
        "populate_by_name": True
    }

    @classmethod
    def AND(cls, *filters: 'FilterNode'):
        return cls(**{"and": list(filters)})

    @classmethod
    def OR(cls, *filters: 'FilterNode'):
        return cls(**{"or": list(filters)})

    @model_validator(mode="before")
    def normalize(cls, data):
        if "and" in data:
            data["and_"] = data.pop("and")
        if "or" in data:
            data["or_"] = data.pop("or")
        return data

FilterNode = Union[Filter, LogicalFilter]


class PaginationInfo(BaseModel):
    """
    Pagination metadata following industry standards.
    """
    count: int = Field(description="Number of items in current page")
    total_count: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Maximum items per page")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 10,
                "total_count": 100,
                "page": 1,
                "limit": 10
            }
        }
    )


class ApiResponse(BaseModel, Generic[T]):
    """
    Standardized API response structure for all endpoints in the application.
    
    Attributes:
        message (str): A descriptive message about the result of the operation
        data (Optional[T]): The response data payload, can be of any type
    """
    message: str
    data: Optional[T] = None
    
    # When serializing, avoid including keys with `None` values by default.
    # This ensures responses like {"message": "OK"} (without "data": null)
    # unless a caller explicitly requests otherwise by passing exclude_none=False.
    def model_dump(self, *args, **kwargs):
        if 'exclude_none' not in kwargs:
            kwargs['exclude_none'] = True
        return super().model_dump(*args, **kwargs)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
                "data": {}
            }
        }
    )

class ApiListResponse(BaseModel, Generic[T]):
    """
    Standardized API response structure for paginated list endpoints.
    Follows industry standard pattern with structured pagination metadata.
    
    Attributes:
        message (str): A descriptive message about the result of the operation
        data (List[T]): The list of data items
        page (PaginationInfo): Pagination metadata
    """
    message: str
    data: List[T]
    page: PaginationInfo
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Items retrieved successfully",
                "data": [{}],
                "page": {
                    "count": 1,
                    "total_count": 100,
                    "page": 1,
                    "limit": 10
                }
            }
        }
    )
