import datetime

from pydantic import BaseModel

from ..query.user import UserQuery


class UserOut(BaseModel):
    username: str
    updated_at: datetime.datetime
    created_at: datetime.datetime


class UserOutRegister(UserQuery):
    qr_img: str
