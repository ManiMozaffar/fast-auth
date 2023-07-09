from datetime import datetime, timedelta
from typing import Any, Dict

from jose import ExpiredSignatureError, JWTError, jwt

from ..core.config import settings
from ..core.exceptions import CustomException


class JWTDecodeError(CustomException):
    code = 401
    message = "Invalid token"


class JWTExpiredError(CustomException):
    code = 401
    message = "Token expired"


class JWTHandler:
    secret_key = settings.SECRET_KEY
    algorithm = settings.JWT_ALGORITHM
    access_token_expire = settings.JWT_EXPIRE_MINUTES
    refresh_token_expire = 60 * 60 * 24 * 7

    @staticmethod
    def encode(payload: Dict[str, Any]) -> str:
        expire = datetime.utcnow() + timedelta(minutes=JWTHandler.access_token_expire)
        payload.update({"exp": expire})
        return jwt.encode(payload, JWTHandler.secret_key, algorithm=JWTHandler.algorithm)

    @staticmethod
    def encode_refresh_token(payload: Dict[str, Any]) -> str:
        expire = datetime.utcnow() + timedelta(minutes=JWTHandler.refresh_token_expire)
        payload.update({"exp": expire})
        return jwt.encode(payload, JWTHandler.secret_key, algorithm=JWTHandler.algorithm)

    @staticmethod
    def decode(token: str) -> dict:
        try:
            result: dict = jwt.decode(
                token, JWTHandler.secret_key, algorithms=[JWTHandler.algorithm]
            )
            exp = result.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise JWTExpiredError
            return result
        except ExpiredSignatureError as exception:
            raise JWTExpiredError() from exception
        except JWTError as exception:
            raise JWTDecodeError() from exception

    @staticmethod
    def decode_expired(token: str) -> dict:
        try:
            return jwt.decode(
                token,
                JWTHandler.secret_key,
                algorithms=[JWTHandler.algorithm],
                options={"verify_exp": False},
            )
        except JWTError as exception:
            raise JWTDecodeError() from exception
