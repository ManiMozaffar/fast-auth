from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .controllers.auth import AuthController
from .core.database import DBManager, get_db
from .core.exceptions import ForbiddenException
from .repository.jwt import JWTHandler

http_bearer = HTTPBearer()


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    if credentials.scheme != "Bearer":
        raise ForbiddenException("Invalid Header")
    access_token = request.cookies.get("Access-Token")
    if not access_token:
        raise ForbiddenException("Access-Token is not provided")
    token = JWTHandler.decode(access_token)
    user_id = token.get("user_id")
    if not user_id:
        raise ForbiddenException("Invalid Refresh Token")
    csrf_token = JWTHandler.decode(credentials.credentials)
    if csrf_token.get("access_token") != access_token:
        raise ForbiddenException("Invalid CSRF Token")
    return user_id


async def get_current_user_from_db(
    db_session: DBManager = Depends(get_db), user_id: str = Depends(get_current_user)
):
    return await AuthController(db_session).me(user_id)
