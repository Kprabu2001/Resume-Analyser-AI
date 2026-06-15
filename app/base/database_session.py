import logging
from contextlib import contextmanager

from app.base.app_session import AppSession

logger = logging.getLogger(__name__)


class DatabaseSessionWrapper:

    def __init__(self, app_session: AppSession) -> None:
        self._app_session = app_session
        self._depth = 0

    @property
    def session(self) -> AppSession:
        return self._app_session

    @contextmanager
    def transaction(self):
        self._depth += 1
        savepoint = None

        try:
            if self._depth > 1:
                savepoint = self._app_session.session.begin_nested()
                logger.debug(f"Savepoint started at depth {self._depth}")
            else:
                logger.debug(f"Main transaction at depth {self._depth}")

            yield self._app_session

            if savepoint:
                savepoint.commit()
                logger.debug(f"Savepoint committed at depth {self._depth}")

        except Exception:
            if savepoint:
                savepoint.rollback()
                logger.debug(f"Savepoint rolled back at depth {self._depth}")
            raise

        finally:
            self._depth -= 1

    def flush(self) -> None:
        self._app_session.flush()


@contextmanager
def get_db_session(app_session: AppSession):
    try:
        yield DatabaseSessionWrapper(app_session)
        app_session.commit()
        logger.debug("Session committed")
    except Exception as e:
        app_session.rollback()
        logger.debug(f"Session rolled back: {e}")
        raise
