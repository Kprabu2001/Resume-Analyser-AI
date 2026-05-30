from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.base.app_session import AppSession
from app.database.session import SessionLocal


def get_app_session() -> Generator[AppSession, None, None]:
    """
    FastAPI dependency — creates one AppSession per request.

    - Wraps a fresh SQLAlchemy Session in AppSession.
    - Yields the AppSession to the route / other dependencies.
    - Closes the underlying session in the finally block so connections
      are always returned to the pool, even on unhandled errors.

    Usage in a route:
        @router.post("/")
        def my_route(app_session: AppSessionDep):
            service = MyService(app_session)
            ...

    Usage in another dependency (e.g. get_current_user):
        def get_current_user(app_session: AppSessionDep) -> User:
            ...
    """
    raw_session: Session = SessionLocal()
    app_session = AppSession(raw_session)
    try:
        yield app_session
    finally:
        app_session.close()


# Annotated shorthand — use this type hint in routes and dependencies
AppSessionDep = Annotated[AppSession, Depends(get_app_session)]
