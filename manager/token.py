# import ast
# import json
# import logging
# from http import HTTPStatus
#
# import jwt
# import redis
# import requests
#
# import configs
# from app.core.utils.constants import CacheTimeout
#
# LOGGER = logging.getLogger('main')
#
# # secret code
# client_id = '156271504934-q47hs0sj0ru48ddshcuva06nhee87lpg.apps.googleusercontent.com'
# client_secret = 'OEZUSPDW1RHPzXNLAVP4w2QJ'
# jwt_secret = 'OEZUSPDW1RHPzXNLAVP4w2QJ'
# GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
# jwt_algorithm = 'HS256'
# r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
# ACCESS_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'
# AUTH_REDIRECT_URI = 'http://localhost:8040/google/auth'
# BASE_URI = 'http://localhost:5000'
# AUTH_TOKEN_KEY = 'auth_token'
# AUTH_STATE_KEY = 'auth_state'
# AUTHORIZATION_SCOPE = 'openid email profile'
#
#
# def de_json(json_var):
#     decoded_json = []
#     result = ''
#     if isinstance(json_var, dict):
#         json_var = json.dumps(json_var)
#
#     decoded_json = json.loads(json_var)
#     return decoded_json
#
#
# def gen_token(var_json):
#     jwt_token = ''
#     jwt_token = jwt.encode(var_json, jwt_secret, jwt_algorithm)
#     return jwt_token
#
#
# def de_token(jwt_token):
#     payload = ''
#     payload = jwt.decode(jwt_token, jwt_secret, jwt_algorithm)
#     return payload
#
#
# def set_cache(token, user_data):
#     user_data = 'p.hieu2411@gmail.com'
#     r.setex(
#         token,
#         15 * 60,
#         user_data
#     )
#
#
# def get_cache(token):
#     return format(r.get(token))
#
#
# def get_info_token(access_token):
#     result = redis.get(access_token)
#     if result is None:
#         result = requests.get(configs.SSO_URL, params={'accessToken': access_token},
#                               headers={'Content-Type': 'application/json'})
#         if result.status_code == HTTPStatus.OK:
#             redis.set(access_token, str(result.json()), ex=CacheTimeout.CLIENT_TOKEN)
#             return result.json()
#         return None
#     return ast.literal_eval(result.decode('utf-8'))
#
#
# def validate_token(access_token):
#     try:
#         token = get_info_token(access_token)
#         if token is not None:
#             return True
#         return False
#     except Exception as e:
#         LOGGER.error(e)
#         return False
