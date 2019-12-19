# import logging
#
# from http import HTTPStatus
#
# from sqlalchemy import or_
#
# # from manager.token import de_json
#
#
# from app import Role, User
# from app import UserRole
# from api.base import wrap_response
# from app import db
# from manager.user_role import delete_all_role_by_user_id, \
#     create_roles_with_user_id
# from manager.user_permission import \
#     delete_all_permission_by_user_id, create_permissions_with_user_id, has_permission
# from manager.role import get_all_role_by_user_id
# from manager.permission import get_by_ids, get_all_permission_by_user_id
# from utils.constants import InternalErrorCode, TeamStatus, permissions
#
# LOGGER = logging.getLogger('main')
#
# """must return json"""
