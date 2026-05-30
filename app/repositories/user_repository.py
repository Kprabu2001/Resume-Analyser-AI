from app.base.app_session import AppSession
from app.base.base_repository import BaseRepository
from app.database.models import User


class UserRepository(BaseRepository):
    """
    Handles all DB operations for User model.
    Receives an AppSession through BaseRepository.__init__.
    """

    def __init__(self, db: AppSession) -> None:
        super().__init__(db)

    # ── User ──────────────────────────────────────────────────────────────────

    def create_user(self, email: str, hashed_password: str, full_name: str = None) -> User:
        return self.create(
            User,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
        )

    def get_by_email(self, email: str):
        return self.get_one(User, email=email)

    def get_by_id(self, user_id: int):
        return self.get_one(User, id=user_id)
