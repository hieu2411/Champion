# """User APIs"""
# import json
# import logging
# from http import HTTPStatus
#
# from flask import request
# from flask_restplus import Resource
#
# from api.base import wrap_response
# from manager import user
# from manager.user import get_a_user, generate_table
# from utils.decorators import authorized, validate_offset_limit
# from utils.request_helper import log_api_request
#
# from app import api_namespace
#
# LOGGER = logging.getLogger('main')
