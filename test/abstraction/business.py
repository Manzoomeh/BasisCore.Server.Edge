import idb_manager


class UserPermissionRequest:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id


class UserPermissions:
    def __init__(self, user_id: int, permissions: 'list[str]') -> None:
        self.user_id = user_id
        self.permissions = permissions


class UserPermissionManager:

    def __init__(self, db_manager: idb_manager.IDbManager) -> None:
        self.db = db_manager

    def get_user_permissions(self, request: UserPermissionRequest) -> UserPermissions:
        sql_connection = self.db.open_sql_connection("permissions")
        # fetch permission from db by sql connection
        return UserPermissions(request.user_id, ['add', 'edit'])
