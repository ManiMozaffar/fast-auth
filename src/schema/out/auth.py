from pydantic import BaseModel


class RefreshToken(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str | None
    refresh_token: str
    csrf_token: str
