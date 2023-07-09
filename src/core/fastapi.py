from typing import List

from asyncpg.exceptions._base import PostgresError  # type: ignore
from fastapi import Depends, FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import CustomException
from src.routers import routers

from .config import settings
from .exceptions import BadRequestException
from .logging import Logging
from .middleware import ResponseLoggerMiddleware, SessionMiddleware


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Custom schema",
        version="1.0.0",
        description="Auth Schema By Mani Mozaffar",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {"type": "http", "scheme": "bearer", "in": "headers"},
        "CookieAuth": {"type": "apiKey", "in": "cookie", "name": "access_token"},
        "RefreshCookieAuth": {"type": "apiKey", "in": "cookie", "name": "refresh_token"},
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def on_auth_error(request: Request, exc: Exception):
    status_code, error_code, message = 401, None, str(exc)
    if isinstance(exc, CustomException):
        status_code = int(exc.code)
        error_code = exc.error_code
        message = exc.message

    return JSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message},
    )


def init_routers(app_: FastAPI) -> FastAPI:
    app_.include_router(routers)
    return app_


async def postgres_exception_handler(request: Request, exc: PostgresError):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )


async def sqlalchemy_unique_constraint(request, exc: IntegrityError):
    if "unique constraint" in str(exc.orig):
        return JSONResponse(
            status_code=BadRequestException.error_code,
            content={"message": "Object already exists in database"},
        )
    raise exc from exc


def make_middleware() -> List[Middleware]:
    middleware = [Middleware(ResponseLoggerMiddleware), Middleware(SessionMiddleware)]
    return middleware


async def custom_exception_handler(request: Request, exc: CustomException):  # type: ignore
    return JSONResponse(status_code=exc.code, content={"error": exc.message})


def create_app() -> FastAPI:
    app_ = FastAPI(
        title="Fairtobot Backend",
        description="Fairtobot Backend",
        version="1.0.0",
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
        dependencies=[Depends(Logging)],
        middleware=make_middleware(),
    )
    app_ = init_routers(app_=app_)
    app_.add_exception_handler(CustomException, custom_exception_handler)
    app_.add_exception_handler(PostgresError, postgres_exception_handler)
    app_.add_exception_handler(IntegrityError, sqlalchemy_unique_constraint)
    app_.openapi = custom_openapi
    return app_


app = create_app()
