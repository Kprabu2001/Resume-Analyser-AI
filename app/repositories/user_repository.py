from app.base.app_session import AppSession
from app.base.base_repository import BaseRepository
from app.database.models import User


class UserRepository(BaseRepository):

    def __init__(self, db: AppSession) -> None:
        super().__init__(db)

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

    def get_by_id(self, user_id: str):
        return self.get_one(User, id=user_id)
