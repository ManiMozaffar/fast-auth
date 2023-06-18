import datetime

from pydantic import BaseModel


class UserQuery(BaseModel):
    username: str
    updated_at: datetime.datetime
    created_at: datetime.datetime
