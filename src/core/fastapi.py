from typing import List

from asyncpg.exceptions._base import PostgresError  # type: ignore
from fastapi import Depends, FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import CustomException
from src.routers import routers

from .config import settings
from .exceptions import BadRequestException
from .logging import Logging
from .middleware import ResponseLoggerMiddleware


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
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(ResponseLoggerMiddleware),
        # Middleware(
        #     AuthenticationMiddleware,
        #     backend=AuthBackend(),
        #     on_error=on_auth_error,
        # ),

    ]
    return middleware


async def custom_exception_handler(request: Request, exc: CustomException):  # type: ignore
    return JSONResponse(
        status_code=exc.code,
        content={"error":exc.message}
    )


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
    return app_


app = create_app()