import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)


def get_current_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


CurrentUserIdDep = Annotated[str, Depends(get_current_user)]
