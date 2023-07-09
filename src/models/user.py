from sqlalchemy.orm import Mapped, mapped_column

from ..core.access_controll import Allow, Everyone, RolePrincipal, UserPrincipal
from .base import SQLBase, TimestampMixin, UUIDMixin
from .permissions import UserPermission


class User(SQLBase, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(unique=True, default=None)
    password: Mapped[str] = mapped_column(default=None)
    gauth: Mapped[str] = mapped_column(default=None)

    def __acl__(self):
        basic_permissions = [UserPermission.READ, UserPermission.CREATE]
        self_permissions = [
            UserPermission.READ,
            UserPermission.EDIT,
            UserPermission.CREATE,
        ]
        all_permissions = list(UserPermission)

        return [
            (Allow, Everyone, basic_permissions),
            (Allow, UserPrincipal(value=str(self.id)), self_permissions),
            (Allow, RolePrincipal(value="admin"), all_permissions),
        ]
