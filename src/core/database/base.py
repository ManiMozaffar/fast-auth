
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class SQLBase(MappedAsDataclass, DeclarativeBase):
    ...
