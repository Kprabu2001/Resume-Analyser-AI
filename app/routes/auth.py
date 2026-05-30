from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from app.base.base import ApiResponse
from app.dependencies.db_dependency import AppSessionDep
from app.models.schemas import UserSignUp, UserLogin, UserTokenResponse, UserOut
from app.base.constants import REFRESH_COOKIE
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[UserOut])
def signup(user_data: UserSignUp,app_session: AppSessionDep ):
    authservice= AuthService(app_session)
    authservice.signup(user_data)
    return ApiResponse(
        message="User created successfully")


@router.post("/login", status_code=status.HTTP_200_OK, response_model=ApiResponse[UserTokenResponse])
def login(user_data: UserLogin, request: Request, response: Response,app_session:AppSessionDep):
    authservice= AuthService(app_session)
    login_result=authservice.login(user_data, request, response)
    return ApiResponse(
        message="Login successful",data=login_result)


@router.post("/logout", status_code=status.HTTP_200_OK, response_model=ApiResponse)
def logout(request: Request, response: Response,app_session:AppSessionDep):
    authservice= AuthService(app_session)
    authservice.logout(request, response)
    return ApiResponse (message = "Logged out successfully")


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=ApiResponse[UserTokenResponse])
def refresh_token(request: Request, response: Response,app_session:AppSessionDep):
    refresh_tok = request.cookies.get(REFRESH_COOKIE)
    if not refresh_tok:
        raise HTTPException(status_code=401, detail="Refresh token missing. Please login again.")
    authservice= AuthService(app_session)
    new_tokens=authservice.refresh_access_token(request, response)
    return ApiResponse(message="Token refreshed successfully",data=new_tokens)

