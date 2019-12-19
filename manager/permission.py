from http import HTTPStatus
from app.core.models.permission import Permission
from app.core.models.user_permission import UserPermission
from app.core.models.role_permission import RolePermission
from app.core.manager.role import get_all_role_by_user_id
from api.base import wrap_response

import logging

LOGGER = logging.getLogger('main')

