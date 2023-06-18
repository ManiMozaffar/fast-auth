from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .controllers.auth import AuthController
from .core.database import DBManager, get_db
from .core.exceptions import ForbiddenException
from .repository.jwt import JWTHandler

http_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    if credentials.scheme != "Bearer":
        raise ForbiddenException("Invalid Header")
    token = JWTHandler.decode(credentials.credentials)
    user_id = token.get("user_id")
    if not user_id:
        raise ForbiddenException("User Not Authenticated")
    return user_id


async def get_current_user_from_db(
    db_session: DBManager = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    return await AuthController(db_session).me(user_id)
