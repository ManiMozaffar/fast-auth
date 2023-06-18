from pydantic import BaseModel  # pylint: disable=no-name-in-module


class UserIn(BaseModel):
    username: str
    password: str
