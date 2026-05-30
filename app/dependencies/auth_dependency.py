import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.base.app_session import AppSession
from app.base.constants import ACCESS_COOKIE
from app.database.models import User
from app.dependencies.db_dependency import AppSessionDep
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class _StrictBearer(HTTPBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )


bearer_scheme = _StrictBearer(auto_error=False)


def get_current_user(
    app_session: AppSessionDep,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get(ACCESS_COOKIE)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = TokenService.verify_token(token)

    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user = app_session.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    app_session.set_user(user.id)

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
