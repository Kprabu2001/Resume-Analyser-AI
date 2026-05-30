import logging
from contextlib import contextmanager

from app.base.app_session import AppSession

logger = logging.getLogger(__name__)


class DatabaseSessionWrapper:
    """
    Thin wrapper handed to services inside `get_db_session`.

    Exposes:
      - `.session`     → the AppSession (passed to repositories)
      - `.transaction()` → context manager that creates a savepoint for
                           nested calls, so two services can call each other
                           without double-committing or losing partial work.
    """

    def __init__(self, app_session: AppSession) -> None:
        self._app_session = app_session
        self._depth = 0

    @property
    def session(self) -> AppSession:
        """Return the AppSession so repositories can be constructed from it."""
        return self._app_session

    @contextmanager
    def transaction(self):
        """
        Savepoint-safe nested transaction.

        Depth 1  → uses the main transaction (commit handled by get_db_session).
        Depth 2+ → creates a SAVEPOINT so partial failures only roll back
                   the inner block, not the whole request.
        """
        self._depth += 1
        savepoint = None

        try:
            if self._depth > 1:
                savepoint = self._app_session.session.begin_nested()
                logger.debug(f"Savepoint started at depth {self._depth}")
            else:
                logger.debug(f"Main transaction started at depth {self._depth}")

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
    """
    Request-level transaction manager.

    Usage inside any service method:

        with get_db_session(self.session) as db:
            db.session.add(some_obj)
            # or use db.transaction() for nested savepoints

    - Commits on success.
    - Rolls back on any exception and re-raises.
    - Does NOT close the session — lifecycle is owned by get_app_session().
    """
    try:
        yield DatabaseSessionWrapper(app_session)
        app_session.commit()
        logger.debug("Session committed")
    except Exception as e:
        app_session.rollback()
        logger.debug(f"Session rolled back: {e}")
        raise
