from datetime import datetime, timezone
from typing import Optional

from app.base.base_repository import BaseRepository
from app.database.models import UserSession


class UserSessionRepository(BaseRepository):

    def create_session(
        self,
        user_id: str,
        refresh_token: str,
        expires_at,
        user_agent: str = None,
        ip_address: str = None,
    ) -> UserSession:
        return self.create(
            UserSession,
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            status="active",
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        return self.get_one(UserSession, refresh_token=refresh_token)

    def get_by_id(self, session_id: str) -> Optional[UserSession]:
        return self.get_one(UserSession, id=session_id)

    def revoke(self, session_id: str) -> Optional[UserSession]:
        session = self.get_one(UserSession, id=session_id)
        if session and session.status != "revoked":
            session.status = "revoked"
            session.revoked_at = datetime.now(timezone.utc)
        return session

    def mark_expired(self, session_id: str) -> Optional[UserSession]:
        session = self.get_one(UserSession, id=session_id)
        if session and session.status != "expired":
            session.status = "expired"
        return session
