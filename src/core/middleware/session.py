from secrets import token_hex

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.config import settings


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
        settings=settings,
    ) -> Response:
        session_id = request.cookies.get("Session-Id")

        if not session_id:
            session_id = token_hex(16)

        response = await call_next(request)
        response.set_cookie(
            "Session-Id",
            session_id,
            max_age=(settings.SESSION_EXPIRE_MINUTES) * 60,
            httponly=True,
            samesite="strict",
        )
        return response
