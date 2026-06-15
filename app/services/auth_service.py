import logging
from datetime import datetime

from fastapi import HTTPException, Request, Response, status
from passlib.context import CryptContext

from app.base.app_session import AppSession
from app.base.base_repository import BaseRepository
from app.base.base_service import BaseService
from app.base.constants import ACCESS_COOKIE, REFRESH_COOKIE
from app.models.schemas import UserLogin, UserSignUp, UserTokenResponse
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService
from app.services.user_session import UserSessionService

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class AuthService(BaseService):

    def __init__(self, session: AppSession) -> None:
        super().__init__(session)
        self.session_service = UserSessionService(session)

    def _get_repository(self) -> BaseRepository:
        return UserRepository(self.session)

    def signup(self, user_data: UserSignUp):
        existing = self.repository.get_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        with self.get_db_session():
            new_user = self.repository.create_user(
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
                full_name=user_data.full_name,
            )

        logger.info(f"New user created: {new_user.email} (id={new_user.id})")
        return new_user

    def login(
        self, user_data: UserLogin, request: Request, response: Response
    ) -> UserTokenResponse:
        user = self.repository.get_by_email(user_data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated"
            )

        access_token, access_expires = TokenService.create_token(
            user.id, user.email, token_type="access"
        )
        refresh_token, refresh_expires = TokenService.create_token(
            user.id, user.email, token_type="refresh"
        )

        user_agent = request.headers.get("user-agent")
        x_forwarded_for = request.headers.get("x-forwarded-for")
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else (request.client.host if request.client else None)
        )

        with self.get_db_session():
            self.session_service.create_session(
                user_id=user.id,
                refresh_token=refresh_token,
                expires_at=refresh_expires,
                user_agent=user_agent,
                ip_address=ip_address,
            )

        logger.info(f"Login successful for: {user.email}")
        self._set_access_cookie(response, access_token, access_expires)
        self._set_refresh_cookie(response, refresh_token, refresh_expires)

        return UserTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )

    def logout(self, request: Request, response: Response) -> None:
        refresh_token = request.cookies.get(REFRESH_COOKIE)

        if refresh_token:
            session = self.session_service.get_by_refresh_token(refresh_token)
            if session:
                with self.get_db_session():
                    self.session_service.revoke(session.id)
                logger.info(f"Session revoked: {session.id}")

        self._clear_refresh_cookie(response)
        self._clear_access_cookie(response)

    def refresh_access_token(self, request: Request, response: Response) -> UserTokenResponse:
        refresh_token = request.cookies.get(REFRESH_COOKIE)
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing. Please login again.",
            )

        try:
            payload = TokenService.verify_token(refresh_token)
        except HTTPException:
            session = self.session_service.get_by_refresh_token(refresh_token)
            if session and session.status == "active":
                with self.get_db_session():
                    self.session_service.mark_expired(session.id)
                logger.info(f"Session marked as expired due to JWT expiry: {session.id}")
            self._clear_refresh_cookie(response)
            self._clear_access_cookie(response)
            raise

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
        session = self.session_service.get_by_refresh_token(refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found. Please login again.",
            )
        if session.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked. Please login again.",
            )
        if session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired. Please login again.",
            )

        user = self.repository.get_by_id(session.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated",
            )

        new_access, access_expires = TokenService.create_token(
            user.id, user.email, token_type="access"
        )
        self._set_access_cookie(response, new_access, access_expires)

        logger.info(f"Token rotated for user: {user.email} | session: {session.id}")
        return UserTokenResponse(
            access_token=new_access,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )

    @staticmethod
    def _set_access_cookie(response: Response, access_token: str, expiration: datetime) -> None:
        response.set_cookie(
            key=ACCESS_COOKIE,
            value=access_token,
            httponly=False,
            samesite="lax",
            path="/",
            expires=expiration,
        )

    @staticmethod
    def _clear_access_cookie(response: Response) -> None:
        response.delete_cookie(key=ACCESS_COOKIE, path="/")

    @staticmethod
    def _set_refresh_cookie(response: Response, refresh_token: str, expiration: datetime) -> None:
        response.set_cookie(
            key=REFRESH_COOKIE,
            value=refresh_token,
            httponly=False,
            samesite="lax",
            path="/",
            expires=expiration,
        )

    @staticmethod
    def _clear_refresh_cookie(response: Response) -> None:
        response.delete_cookie(key=REFRESH_COOKIE, path="/")
