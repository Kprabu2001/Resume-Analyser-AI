import logging
from typing import Optional
from datetime import datetime

from app.base.base_repository import BaseRepository
from app.base.base_service import BaseService
from app.database.models import UserSession
from app.repositories.user_session import UserSessionRepository
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class UserSessionService(BaseService):

    def _get_repository(self) -> BaseRepository:
        return UserSessionRepository(self.session)

    def create_session(
        self,
        user_id: str,
        refresh_token: str,
        expires_at: datetime,
        user_agent: str = None,
        ip_address: str = None,
    ) -> UserSession:
        return self.repository.create_session(
            user_id=user_id,
            refresh_token=TokenService.hash_token(refresh_token),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        return self.repository.get_by_refresh_token(
            TokenService.hash_token(refresh_token),
        )

    def revoke(self, session_id: str) -> None:
        self.repository.revoke(session_id)

    def mark_expired(self, session_id: str) -> None:
        self.repository.mark_expired(session_id)
