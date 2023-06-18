# pylint: skip-file
import datetime
import uuid

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column

from .sqlbase import UUID


class TimestampMixin(MappedAsDataclass):
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default_factory=func.now, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default_factory=func.now, nullable=False
    )


class IdMixin(MappedAsDataclass):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, nullable=False)


class UUIDMixin(MappedAsDataclass):
    id: Mapped[str] = mapped_column(
        UUID,
        primary_key=True,
        unique=True,
        nullable=False,
        default_factory=uuid.uuid4,
    )
