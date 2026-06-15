from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.base.app_session import AppSession
from app.database.session import SessionLocal


def get_app_session() -> Generator[AppSession, None, None]:
    raw_session: Session = SessionLocal()
    app_session = AppSession(raw_session)
    try:
        yield app_session
    finally:
        app_session.close()


AppSessionDep = Annotated[AppSession, Depends(get_app_session)]
