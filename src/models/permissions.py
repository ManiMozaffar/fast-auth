from enum import Enum


class CRUDPermission:
    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"


class UserPermission(CRUDPermission, Enum):
    pass
