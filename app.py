import datetime
import importlib
import json
import os
import random
import time
from http import HTTPStatus

import redis
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, make_response, jsonify, request
import logging
from flask_restplus import Api, Namespace, api, Resource
from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship, backref

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///championship.db'
app.config['img_dir'] = 'static/image'

db = SQLAlchemy(app)
LOGGER = logging.getLogger('main')
api_namespace = Api(app)


# region model
# region model done
class PermissionGranted(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "permission_granted"

    user_role_id = db.Column(db.INT, primary_key=True)
    permission_id = db.Column(db.INT, primary_key=True)

    def as_dict(self):
        return {
            'user_role_id': self.user_role_id,
            'permission_id': self.permission_id
        }


class User(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True)
    fullname = db.Column(db.String(125), nullable=False)
    mobile = db.Column(db.String(32))
    is_active = db.Column(db.Boolean, index=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)

    def __repr__(self):
        return "<User '{}'>".format(self.username)

    def as_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'fullname': self.fullname,
            'mobile': self.mobile,
            """'sso_user_id': self.sso_user_id,"""
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S'),
        }

    @classmethod
    def create(cls, email, username, fullname, mobile):
        try:
            user = User(
                email=email,
                username=username,
                fullname=fullname,
                mobile=mobile,
                is_active=True,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                last_login=datetime.datetime.now(),
            )
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create user. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            user_data = {}
            for key in data:
                if hasattr(cls, key):
                    user_data[key] = data[key]
            user_data['updated_at'] = datetime.datetime.now()
            if 'id' not in user_data:
                user = User.query.filter_by(email=user_data.get('email'))
                user.update(user_data)
            else:
                user = User.query.filter_by(id=user_data.get('id'))
                user.update(user_data)
            db.session.commit()
            return User.query.get(user_data['id']).as_dict()
        except:
            return None

    @classmethod
    def delete(cls, user_id):
        try:
            User.query.filter_by(id=user_id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class Role(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "role"

    id = db.Column(db.INT, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    desc = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime)

    # users = relationship('User', secondary='user_role')
    # permissions = relationship('Permission', secondary='role_permission')

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

    @classmethod
    def create(cls, name, desc):
        try:
            role = Role(
                name=name,
                desc=desc,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            db.session.add(role)
            db.session.commit()
            return role
        except:
            return None

    @classmethod
    def update(cls, data):
        try:
            role_data = {}
            for key in data:
                if hasattr(cls, key):
                    role_data[key] = data[key]
            role_data['updated_at'] = datetime.datetime.now()
            role = Role.query.filter_by(id=role_data.get('id')).update(
                role_data)
            db.session.commit()
            return role
        except:
            return None

    @classmethod
    def delete(cls, role_id):
        try:
            list = Role.query.filter_by(id=role_id)
            list.delete()
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False


class RolePermission(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "role_permission"

    role_id = db.Column(db.Integer, nullable=False, primary_key=True)
    permission_id = db.Column(db.Integer, nullable=False, primary_key=True)

    # role = relationship(Role, backref=backref('role_permission', cascade='all, delete-orphan'))
    # permission = relationship(Permission, backref=backref('role_permission', cascade='all, delete-orphan'))

    def as_dict(self):
        return {
            'role_id': self.role_id,
            'permission_id': self.permission_id,
        }

    @classmethod
    def create(cls, role_id, permission_id):
        try:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
            )
            db.session.add(role_permission)
            db.session.commit()
            return role_permission
        except:
            return None


class Permission(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "permission"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    module = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(500), nullable=False)

    # users = relationship('User', secondary='user_permission')
    # roles = relationship('Role', secondary='role_permission')

    def as_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'name': self.name,
            'module': self.module,
            'desc': self.desc,
        }

    @classmethod
    def create(cls, key, name, module, desc):
        try:
            permission = Permission(
                key=key,
                name=name,
                module=module,
                desc=desc
            )
            db.session.add(permission)
            db.session.commit()
            return permission
        except:
            return None

    @classmethod
    def update(cls, data):
        try:
            permission = Permission.query.filter_by(id=data.get('id')).update(
                data)
            db.session.commit()
            return permission
        except:
            return None


class UserPermission(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "user_permission"

    user_id = db.Column(db.Integer,
                        # db.ForeignKey('user.id'), nullable=False,
                        primary_key=True)
    permission_id = db.Column(db.INT,
                              # db.ForeignKey('permission.permission_id'),
                              nullable=False, primary_key=True)

    # user = relationship(User, backref=backref('user_permission', cascade='all, delete-orphan'))
    # permission = relationship(Permission, backref=backref('user_permission', cascade='all, delete-orphan'))

    def as_dict(self):
        return {
            'user_id': self.user_id,
            'permission_id': self.permission_id,
        }

    @classmethod
    def create(cls, user_id, permission_id):
        try:
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
            )
            db.session.add(user_permission)
            db.session.commit()
            return user_permission
        except:
            return None


class UserRole(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "user_role"

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False,
                        primary_key=True)
    role_id = db.Column(db.INT, db.ForeignKey('role.id'), nullable=False,
                        primary_key=True)

    # user = relationship(User, backref=backref('user_role', cascade='all, delete-orphan'))
    # role = relationship(Role, backref=backref('user_role', cascade='all, delete-orphan'))

    def as_dict(self):
        return {
            'user_id': self.user_id,
            'role_id': self.role_id,
        }

    @classmethod
    def create(cls, user_id, role_id):
        try:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
            )
            db.session.add(user_role)
            db.session.commit()
            return user_role
        except:
            return None


class CauThu(db.Model):
    __tablename__ = "cau_thu"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_doi_bong = db.Column(db.Integer)
    ghi_chu = db.Column(db.String(100))
    so_ban_thang = db.Column(db.Integer)

    def __repr__(self):
        return "<cau_thu '{}'>".format(self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'id_doi_bong': self.id_doi_bong,
            'ghi_chu': self.ghi_chu,
            'so_ban_thang': self.so_ban_thang,
        }

    @classmethod
    def create(cls, data):
        try:
            cau_thu = CauThu(
                id_doi_bong=data['id_doi_bong'],
                ghi_chu=data['ghi_chu'],
                so_ban_thang=data['so_ban_thang']
            )
            db.session.add(cau_thu)
            db.session.commit()
            return cau_thu
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create cau_thu. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            cau_thu_data = {}
            for key in data:
                if hasattr(cls, key):
                    cau_thu_data[key] = data[key]
                cau_thu = CauThu.query.filter_by(id=cau_thu_data.get('id'))
                cau_thu.update(cau_thu_data)
            db.session.commit()
            return cau_thu.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            CauThu.query.filter_by(id=id).delete()
            db.session.commit()
            return {'Result': 'Deleted'}
        except Exception as e:
            db.session.rollback()
            return False

    @classmethod
    def get_json(cls, cauthu):
        id = cauthu.id
        id_doi_bong = cauthu.id_doi_bong
        info = ThongTinCauThu.query.filter(ThongTinCauThu.id_cau_thu == id).first()
        team = DoiBong.query.filter(DoiBong.id == id_doi_bong).first()
        if info is not None:
            response = {
                'TenCauThu': info.ten,
                'NgaySinh': info.ngay_sinh,
                'LoaiCauThu': info.loai_thong_tin_cau_thu,
                'ThoiGianGiaNhap': '',
                'ThoiGianKetThuc': '',
                'DoiHienTai': team.ten_doi,
                'TongBanThang': info.tong_ban_thang
            }
            return response
        else:
            return {'Error': 'Khong tim thay'}


class ThongTinCauThu(db.Model):
    __tablename__ = "thong_tin_cau_thu"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cau_thu = db.Column(db.Integer)
    ten = db.Column(db.String(30))
    ngay_sinh = db.Column(db.DateTime)
    loai_thong_tin_cau_thu = db.Column(db.String(60))
    tong_ban_thang = db.Column(db.Integer)

    def __repr__(self):
        return "<thong_tin_cau_thu '{}'>".format(self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'id_cau_thu': self.id_cau_thu,
            'ten': self.ten,
            'ngay_sinh': self.ngay_sinh,
            'loai_thong_tin_cau_thu': self.loai_thong_tin_cau_thu,
            'tong_ban_thang': self.tong_ban_thang,
        }

    @classmethod
    def create(cls, data):
        try:
            datetime_str = data['ngay_sinh']

            ngay_sinh = datetime.datetime.strptime(datetime_str, '%d/%m/%Y')
            thong_tin_cau_thu = ThongTinCauThu(
                id_cau_thu=data['id_cau_thu'],
                ten=data['ten'],
                ngay_sinh=ngay_sinh,
                loai_thong_tin_cau_thu=data['loai_thong_tin_cau_thu'],
                tong_ban_thang=data['so_ban_thang']
            )
            db.session.add(thong_tin_cau_thu)
            db.session.commit()
            return thong_tin_cau_thu
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create thong_tin_cau_thu. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            thong_tin_cau_thu_data = {}
            for key in data:
                if hasattr(cls, key):
                    thong_tin_cau_thu_data[key] = data[key]
                thong_tin_cau_thu = ThongTinCauThu.query.filter_by(id=thong_tin_cau_thu_data.get('id'))
                thong_tin_cau_thu.update(thong_tin_cau_thu_data)
            db.session.commit()
            return thong_tin_cau_thu.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            ThongTinCauThu.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class SanBong(db.Model):
    __tablename__ = "san_bong"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ten_san = db.Column(db.String(60))
    vi_tri = db.Column(db.String(60))

    def __repr__(self):
        return "<san_bong '{}'>".format(self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'ten_san': self.ten_san,
            'vi_tri': self.vi_tri
        }

    @classmethod
    def create(cls, data):
        try:
            san_bong = SanBong(
                ten_san=data['ten_san'],
                vi_tri=data['vi_tri']
            )
            db.session.add(san_bong)
            db.session.commit()
            return san_bong
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create san_bong. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            san_bong_data = {}
            for key in data:
                if hasattr(cls, key):
                    san_bong_data[key] = data[key]
                san_bong = SanBong.query.filter_by(id=san_bong_data.get('id'))
                san_bong.update(san_bong_data)
            db.session.commit()
            return san_bong.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            SanBong.query.filter_by(id=id).delete()
            db.session.commit()
            return {'Result': 'Deleted'}
        except Exception as e:
            db.session.rollback()
            return {'Result': 'Failed'}

    @classmethod
    def get_json(cls, sanbong):
        response = {
            "Id": sanbong.id,
            "TenSanBong": sanbong.ten_san,
            "ViTri": sanbong.vi_tri
        }
        return response


class DoiBong(db.Model):
    __tablename__ = "doi_bong"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_san_bong = db.Column(db.Integer)
    ten_doi = db.Column(db.String(60))
    sl_cau_thu = db.Column(db.Integer)

    def __repr__(self):
        return "<doi_bong '{}'>".format(self.ten_doi)

    def as_dict(self):
        return {
            'id': self.id,
            'id_san_bong': self.id_san_bong,
            'ten_doi': self.ten_doi,
            'sl_cau_thu': self.sl_cau_thu,
        }

    @classmethod
    def create(cls, data):
        try:
            find = DoiBong.query.filter(DoiBong.ten_doi == data['ten_doi']).first()
            if find is not None:
                return {'Error': 'Trùng tên đội'}
            doi_bong = DoiBong(
                id_san_bong=data['id_san_bong'],
                ten_doi=data['ten_doi'],
                sl_cau_thu=data['sl_cau_thu']
            )
            db.session.add(doi_bong)
            db.session.commit()
            return doi_bong
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create doi_bong. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            doi_bong_data = {}
            for key in data:
                if hasattr(cls, key):
                    doi_bong_data[key] = data[key]
            doi_bong = DoiBong.query.filter_by(id=doi_bong_data.get('id'))
            doi_bong.update(doi_bong_data)
            db.session.commit()
            return doi_bong.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            result = DoiBong.query.filter_by(id=id).delete()
            db.session.commit()
            return {'Result': 'Deleted'}
        except Exception as e:
            db.session.rollback()
            return {'Result': 'Failed'}

    @classmethod
    def get_json(cls, team):
        players = CauThu.query.filter(CauThu.id_doi_bong == team.id).all()
        player_as_dict = []
        for player in players:
            player_as_dict.append(player.as_dict())
        response = {
            'Id': team.id,
            'TenDoiBong': team.ten_doi,
            'SanBong': team.id_san_bong,
            'DanhSachCauThu': player_as_dict
        }
        return response


class DsBanThang(db.Model):
    __tablename__ = "ds_ban_thang"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cau_thu = db.Column(db.Integer)
    id_tran_dau = db.Column(db.Integer)
    id_loai = db.Column(db.Integer)
    thoi_diem = db.Column(db.DateTime)
    doi_ghi_ban = db.Column(db.Integer)

    def __repr__(self):
        return "<ds_ban_thang '{}'>".format(self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'id_cau_thu': self.id_cau_thu,
            'id_tran_dau': self.id_tran_dau,
            'id_loai': self.id_loai,
            'thoi_diem': self.thoi_diem,
            'doi_ghi_ban': self.doi_ghi_ban,
        }

    @classmethod
    def create(cls, data):
        try:
            thoi_diem = datetime.datetime.strptime(data['thoi_diem'], '%H:%M:%S')

            ds_ban_thang = DsBanThang(
                id_cau_thu=data['id_cau_thu'],
                id_tran_dau=data['id_tran_dau'],
                id_loai=data['id_loai'],
                thoi_diem=thoi_diem,
                doi_ghi_ban=data['doi_ghi_ban']
            )
            db.session.add(ds_ban_thang)
            db.session.commit()
            return ds_ban_thang
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create ds_ban_thang. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            ds_ban_thang_data = {}
            for key in data:
                if hasattr(cls, key):
                    ds_ban_thang_data[key] = data[key]
                ds_ban_thang = DsBanThang.query.filter_by(id=ds_ban_thang_data.get('id'))
                ds_ban_thang_data['thoi_diem'] = datetime.datetime.strptime(data['thoi_diem'], '%H:%M:%S')

                ds_ban_thang.update(ds_ban_thang_data)
            db.session.commit()
            return ds_ban_thang.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            DsBanThang.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class LichThiDau(db.Model):
    __tablename__ = "lich_thi_dau"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_mua_giai = db.Column(db.Integer)
    id_doi_1 = db.Column(db.Integer)
    id_doi_2 = db.Column(db.Integer)
    id_san_bong = db.Column(db.Integer)
    vong_dau = db.Column(db.String(30))
    ngay_thi_dau = db.Column(db.DateTime)
    gio_thi_dau = db.Column(db.String(30))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    ti_so = db.Column(db.String(20))

    def __repr__(self):
        return "<lich_thi_dau '{}'>".format(self.id)

    def as_dict(self):
        vong_dau = ''
        if int(self.vong_dau) == 1:
            vong_dau = 'vòng loại'
        if int(self.vong_dau) == 2:
            vong_dau = 'tứ kết'
        if int(self.vong_dau) == 3:
            vong_dau = 'bán kết'
        if int(self.vong_dau) == 4:
            vong_dau = 'bán kết'
        return {
            'id': self.id,
            'id_mua_giai': self.id_mua_giai,
            'id_doi_1': self.id_doi_1,
            'id_doi_2': self.id_doi_2,
            'id_san_bong': self.id_san_bong,
            'vong_dau': vong_dau,
            'ngay_thi_dau': self.ngay_thi_dau,
            'gio_thi_dau': self.gio_thi_dau,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'ti_so': self.ti_so,
        }

    @classmethod
    def create(cls, data):
        try:
            # ngay_thi_dau = datetime.datetime.strptime(data['ngay_thi_dau'], '%d/%m/%Y')
            lich_thi_dau = LichThiDau(
                id_mua_giai=data['id_mua_giai'],
                id_doi_1=data['id_doi_1'],
                id_doi_2=data['id_doi_2'],
                id_san_bong=data['id_san_bong'],
                vong_dau=data['vong_dau'],
                ngay_thi_dau=data['ngay_thi_dau'],
                gio_thi_dau=data['gio_thi_dau'],
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
                ti_so=data['ti_so']
            )
            db.session.add(lich_thi_dau)
            db.session.commit()
            return lich_thi_dau
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create ds_doibong_trongbang. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            lich_thi_dau_data = {}
            for key in data:
                if hasattr(cls, key):
                    if key == 'ngay_thi_dau':
                        lich_thi_dau_data[key] = datetime.datetime.strptime(data[key], '%d/%m/%Y')
                    else:
                        lich_thi_dau_data[key] = data[key]
            lich_thi_dau_data['updated_at'] = datetime.datetime.now()
            lich_thi_dau = LichThiDau.query.filter_by(id=lich_thi_dau_data.get('id'))
            lich_thi_dau.update(lich_thi_dau_data)
            db.session.commit()
            return lich_thi_dau.first()
        except Exception as e:
            return None

    @classmethod
    def delete(cls, id):
        try:
            LichThiDau.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False

    @classmethod
    def get_json_tran_dau(cls, tran_dau):
        id_tran_dau = tran_dau.id
        ds_ban_thang = DsBanThang.query.filter(DsBanThang.id_tran_dau == id_tran_dau).all()
        response = {
            'DoiBong1': tran_dau.id_doi_1,
            'DoiBong2': tran_dau.id_doi_2,
            'ThoiGian': tran_dau.ngay_thi_dau,
            'DanhSachBanThang': []
        }
        for ban_thang in ds_ban_thang:
            loai_ban_thang_id = ban_thang.id_loai
            loai_ban_thang = LoaiBanThang.query.filter(LoaiBanThang.id == loai_ban_thang_id).first()

            response['DanhSachBanThang'].append(
                {
                    'CauThuGhiBan': ban_thang.id_cau_thu,
                    'ThoiDiem': ban_thang.thoi_diem,
                    'LoaiBanThang': loai_ban_thang.ten_loai
                })
        return response

    @classmethod
    def get_json_lich_thi_dau(cls):
        response = {
            'LichThiDau': []
        }
        temp = {}
        temp['VongBang'] = []
        temp['TuKet'] = []
        temp['BanKet'] = []
        temp['ChungKet'] = []
        for i in range(1, 5):
            lichthidaus = LichThiDau.query.filter(LichThiDau.vong_dau == i).all()
            for lichthidau in lichthidaus:
                data = {
                    'TranDau': lichthidau.id
                }
                if int(lichthidau.vong_dau) == 1:
                    temp['VongBang'].append(data)
                if int(lichthidau.vong_dau) == 2:
                    temp['TuKet'].append(data)
                if int(lichthidau.vong_dau) == 3:
                    temp['BanKet'].append(data)
                if int(lichthidau.vong_dau) == 4:
                    temp['ChungKet'].append(data)

        response['LichThiDau'].append(temp)
        return response


class LoaiBanThang(db.Model):
    __tablename__ = "loai_ban_thang"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ten_loai = db.Column(db.String(60))

    def __repr__(self):
        return "<loai_ban_thang '{}'>".format(self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'ten_loai': self.ten_loai,
        }

    @classmethod
    def create(cls, data):
        try:
            loai_ban_thang = LoaiBanThang(
                ten_loai=data['ten_loai']
            )
            db.session.add(loai_ban_thang)
            db.session.commit()
            return loai_ban_thang
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create loai_ban_thang. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            loai_ban_thang_data = {}
            for key in data:
                if hasattr(cls, key):
                    loai_ban_thang_data[key] = data[key]
                loai_ban_thang = LoaiBanThang.query.filter_by(id=loai_ban_thang_data.get('id'))
                loai_ban_thang.update(loai_ban_thang_data)
            db.session.commit()
            return loai_ban_thang.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            LoaiBanThang.query.filter_by(id=id).delete()
            db.session.commit()
            return {'Result': 'Deleted'}
        except Exception as e:
            db.session.rollback()
            return False


# endregion model done


class ThamSo(db.Model):
    __tablename__ = "tham_so"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tuoi_toi_thieu = db.Column(db.Integer)
    tuoi_toi_da = db.Column(db.Integer)
    sl_ct_toi_thieu = db.Column(db.Integer)
    sl_ct_toi_da = db.Column(db.Integer)
    sl_ct_nuocngoai_toi_da = db.Column(db.Integer)
    sl_cac_loai_ban_thang = db.Column(db.Integer)
    thoi_diem_ghi_ban_toi_da = db.Column(db.Integer)  # phút thứ mấy

    def __repr__(self):
        return "<tham_so '{}'>".format(self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'tuoi_toi_thieu': self.tuoi_toi_thieu,
            'tuoi_toi_da': self.tuoi_toi_da,
            'sl_ct_toi_thieu': self.sl_ct_toi_thieu,
            'sl_ct_toi_da': self.sl_ct_toi_da,
            'sl_ct_nuocngoai_toi_da': self.sl_ct_nuocngoai_toi_da,
            'sl_cac_loai_ban_thang': self.sl_cac_loai_ban_thang,
            'thoi_diem_ghi_ban_toi_da': self.thoi_diem_ghi_ban_toi_da,
        }

    @classmethod
    def create(cls, id, tuoi_toi_thieu, tuoi_toi_da, sl_ct_toi_thieu,
               sl_ct_toi_da, sl_ct_nuocngoai_toi_da,
               sl_cac_loai_ban_thang, thoi_diem_ghi_ban_toi_da):
        try:
            tham_so = ThamSo(
                id=id,
                tuoi_toi_thieu=tuoi_toi_thieu,
                tuoi_toi_da=tuoi_toi_da,
                sl_ct_toi_thieu=sl_ct_toi_thieu,
                sl_ct_toi_da=sl_ct_toi_da,
                sl_ct_nuocngoai_toi_da=sl_ct_nuocngoai_toi_da,
                sl_cac_loai_ban_thang=sl_cac_loai_ban_thang,
                thoi_diem_ghi_ban_toi_da=thoi_diem_ghi_ban_toi_da
            )
            db.session.add(tham_so)
            db.session.commit()
            return tham_so
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create tham_so. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            tham_so_data = {}
            for key in data:
                if hasattr(cls, key):
                    tham_so_data[key] = data[key]
                tham_so = ThamSo.query.filter_by(id=tham_so_data.get('id'))
                tham_so.update(tham_so_data)
            db.session.commit()
            return tham_so.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            ThamSo.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class BangDau(db.Model):
    __tablename__ = "bang_dau"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ten_bang = db.Column(db.String(60))

    def __repr__(self):
        return "<bang_dau '{}'>".format(self.ngay)

    def as_dict(self):
        return {
            'id': self.id,
            'ten_bang': self.ten_bang,
        }

    @classmethod
    def create(cls, id, ten_bang):
        try:
            bang_dau = BangDau(
                id=id,
                ten_bang=ten_bang
            )
            db.session.add(bang_dau)
            db.session.commit()
            return bang_dau
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create bang_dau. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            bang_dau_data = {}
            for key in data:
                if hasattr(cls, key):
                    bang_dau_data[key] = data[key]
                bang_dau = BangDau.query.filter_by(id=bang_dau_data.get('id'))
                bang_dau.update(bang_dau_data)
            db.session.commit()
            return bang_dau.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            BangDau.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class BangXepHang(db.Model):
    __tablename__ = "bang_xep_hang"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_doi_bong = db.Column(db.Integer)
    thang = db.Column(db.Integer)
    thua = db.Column(db.Integer)
    hoa = db.Column(db.Integer)
    hieu_so = db.Column(db.Integer)
    ngay = db.Column(db.DateTime)

    def __repr__(self):
        return "<bang_xep_hang '{}'>".format(self.ngay)

    def as_dict(self):
        return {
            'id': self.id,
            'id_doi_bong': self.id_doi_bong,
            'thang': self.thang,
            'thua': self.thua,
            'hoa': self.hoa,
            'hieu_so': self.hieu_so,
            'ngay': self.ngay,
        }

    @classmethod
    def create(cls, id, id_doi_bong, thang, thua, hoa, hieu_so, ngay):
        try:
            bang_xep_hang = BangXepHang(
                id=id,
                id_doi_bong=id_doi_bong,
                thang=thang,
                thua=thua,
                hoa=hoa,
                hieu_so=hieu_so,
                ngay=ngay
            )
            db.session.add(bang_xep_hang)
            db.session.commit()
            return bang_xep_hang
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create bang_xep_hang. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            bang_xep_hang_data = {}
            for key in data:
                if hasattr(cls, key):
                    bang_xep_hang_data[key] = data[key]
                bang_xep_hang = BangXepHang.query.filter_by(id=bang_xep_hang_data.get('id'))
                bang_xep_hang.update(bang_xep_hang_data)
            db.session.commit()
            return bang_xep_hang.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            BangXepHang.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class MuaGiai(db.Model):
    __tablename__ = "mua_giai"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ten_mua_giai = db.Column(db.String(60))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)

    def __repr__(self):
        return "<mua_giai '{}'>".format(self.ngay)

    def as_dict(self):
        return {
            'id': self.id,
            'ten_mua_giai': self.ten_mua_giai,
            'start': self.start,
            'end': self.end,
        }

    @classmethod
    def create(cls, data):
        try:

            data['start'] = datetime.datetime.strptime(data['start'], '%d/%m/%Y')
            data['end'] = datetime.datetime.strptime(data['end'], '%d/%m/%Y')

            mua_giai = MuaGiai(
                ten_mua_giai=data['ten_mua_giai'],
                start=data['start'],
                end=data['end']
            )
            db.session.add(mua_giai)
            db.session.commit()
            return mua_giai
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create mua_giai. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            mua_giai_data = {}
            for key in data:
                if hasattr(cls, key):
                    mua_giai_data[key] = data[key]
                mua_giai = MuaGiai.query.filter_by(id=mua_giai_data.get('id'))
                mua_giai.update(mua_giai_data)
            db.session.commit()
            return mua_giai.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            MuaGiai.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


class DsDoiBongTrongBang(db.Model):
    __tablename__ = "ds_doibong_trongbang"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_bang_dau = db.Column(db.Integer)
    id_doi_bong = db.Column(db.Integer)
    id_mua_giai = db.Column(db.Integer)

    def __repr__(self):
        return "<ds_doibong_trongbang '{}'>".format(self.ngay)

    def as_dict(self):
        return {
            'id': self.id,
            'id_doi_bong': self.id_doi_bong,
            'id_bang_dau': self.id_bang_dau,
            'id_mua_giai': self.id_mua_giai,
        }

    @classmethod
    def create(cls, id, id_doi_bong, id_bang_dau, id_mua_giai):
        try:
            ds_doibong_trongbang = DsDoiBongTrongBang(
                id=id,
                id_bang_dau=id_bang_dau,
                id_doi_bong=id_doi_bong,
                id_mua_giai=id_mua_giai
            )
            db.session.add(ds_doibong_trongbang)
            db.session.commit()
            return ds_doibong_trongbang
        except Exception as e:
            LOGGER.error(
                'Unexpected error occurred when create ds_doibong_trongbang. Message: ' + str(
                    e))
            return None

    @classmethod
    def update(cls, data):
        try:
            ds_doibong_trongbang_data = {}
            for key in data:
                if hasattr(cls, key):
                    ds_doibong_trongbang_data[key] = data[key]
                ds_doibong_trongbang = DsDoiBongTrongBang.query.filter_by(id=ds_doibong_trongbang_data.get('id'))
                ds_doibong_trongbang.update(ds_doibong_trongbang_data)
            db.session.commit()
            return ds_doibong_trongbang.first()
        except:
            return None

    @classmethod
    def delete(cls, id):
        try:
            DsDoiBongTrongBang.query.filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False


# endregion model


# region api

# region base api
class ApiV1BaseException(Exception):
    """Base Exception class"""

    code = HTTPStatus.BAD_REQUEST

    def __init__(self, message='Bad request', status_code=None, payload=None):
        """Init method"""
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.code = status_code
        self.data = payload

    def to_dict(self):
        """Convert Object to dict"""
        rv = dict(error={}, data={})
        rv['error'] = {
            'code': self.code,
            'detail': self.message
        }
        rv['data'] = dict(self.data or ())
        return rv


# trả về json
def wrap_response(message="Success", http_code=200, data=None):
    """ Return general HTTP response
    :param str message: detail info
    :param int http_code:
    :param data: payload data
    :return:
    """

    if data is None:
        message = 'Failed'
    return make_response(jsonify(
        ApiV1BaseException(message, mapping_internal_codes[http_code],
                           data).to_dict()), http_code)


# endregion base api

# region api done
# done
@api_namespace.route('/permissions')
class PermissionList(Resource):
    """ Permission list API """

    def get(self):
        """Get list permissions"""
        try:

            args = request.args
            return jsonify(get_permission_list(args=args))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        """Create a permission"""
        try:
            data = json.loads(request.data.decode())
            return jsonify(add_permission(data=data))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        """Update permission"""
        try:
            data = json.loads(request.data.decode())
            return jsonify(update_permission(data=data))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/permissions/<permission_id>')
class PermissionDetail(Resource):
    """ Permission detail API """

    def get(self, permission_id):
        """Get Permission detail"""
        try:
            return jsonify(get_permission_detail(permission_id=permission_id))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/roles')
class RoleList(Resource):
    """ Role list API """

    def get(self):
        """Get List roles"""
        try:

            args = request.args
            response = get_role_list(args=args)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        """Add new role"""
        try:
            temp = request.data.decode()
            data = json.loads(temp)
            response = add_role(data=data)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        """Update an existing role"""
        try:
            temp = request.data.decode()
            data = json.loads(temp)
            response = update_role(data=data)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/roles/<role_id>')
class RoleDetail(Resource):
    """ Role detail API """

    def get(self, role_id):
        """Get detail of a role"""
        try:

            response = get_role_detail(role_id=role_id)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def delete(self, role_id):
        """Delete an existing role"""
        try:

            response = delete_role(role_id=role_id)
            return jsonify(response)

        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/users')
class UserList(Resource):
    """ User list API """

    def get(self):
        """Get user list"""
        try:
            data = User.query.all()
            if data is None:
                return wrap_response('Server Internal Error: ',
                                     HTTPStatus.INTERNAL_SERVER_ERROR)
            users = []
            for user in data:
                users.append(user.as_dict())

            response = {
                'users': users,
                'length': len(data),
            }
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        """Create a user"""
        try:
            """
                {
                    "email":"",
                    "fullname":"",
                    "mobile":"",
                    "permissions":"",
                    "roles":""
                }
            """
            temp = request.data.decode()
            data = json.loads(temp)
            return jsonify(create_user(data=data))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        """Update an user"""
        try:

            data = json.loads(request.data.decode())
            return wrap_response(data=update_user(data=data))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/users/<user_id>')
class UserDetail(Resource):
    """ User detail API """

    def get(self, user_id):
        """Get an user"""
        try:
            user_id = int(user_id)
        except Exception as e:
            LOGGER.error(str(e))
            return wrap_response('Bad request', HTTPStatus.BAD_REQUEST)
        try:

            response = get_a_user(user_id=user_id)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    #
    # def delete(self, user_id):
    #     """Delete an user"""
    #     try:
    #         
    #         return wrap_response(user.delete_user(user_id=user_id))
    #     except Exception as e:
    #         return wrap_response('Server Internal Error: ' + str(e),
    #                              HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/users/roles')
class UsersAssignRole(Resource):
    """ User assign role API"""

    def post(self):
        # Assign role for user
        try:
            """
            {
            "user_id":"",
            "role_id":""
            }
            """

            args = request.args
            data = json.loads(request.data.decode())
            assign_role(data=data)
            return jsonify(get_a_user(data['user_id']))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/teams')
class TeamList(Resource):
    def get(self):
        try:
            teams = DoiBong.query.all()
            response = {
                'length': len(teams),
                'teams': []
            }
            for team in teams:
                response['teams'].append(DoiBong.get_json(team))
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            """
            {
                "id_san_bong": "",
                "ten_doi": "",
                "sl_cau_thu": "",
            }
            """
            temp = request.data.decode()
            response = DoiBong.create(data=json.loads(temp))
            return jsonify(DoiBong.get_json(response))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            """
                 {
                    "id" : "",
                     "id_san_bong": "",
                     "ten_doi": "",
                     "sl_cau_thu": "",
                 }
             """
            temp = request.data.decode()
            response = DoiBong.update(data=json.loads(temp))
            return jsonify(DoiBong.get_json(response))

        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/teams/<id>')
class TeamDetail(Resource):
    def get(self, id):
        try:
            team = DoiBong.query.get(id)
            return jsonify(DoiBong.get_json(team))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def delete(self, id):
        try:
            result = DoiBong.delete(id)
            return jsonify(result)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/players')
class PlayerList(Resource):
    def get(self):
        try:
            players = CauThu.query.all()
            response = {
                'length': len(players),
                'players': []
            }
            for player in players:
                response['players'].append(CauThu.get_json(player))
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            """
            {
                "id_doi_bong": "",
                "ghi_chu":"",
                "ten": "",
                "ngay_sinh": "",
                "loai_thong_tin_cau_thu": "",
                "so_ban_thang": ""
            }
            """
            temp = request.data.decode()
            cauthu = CauThu.create(data=json.loads(temp))
            temp = json.loads(temp)
            temp['id_cau_thu'] = cauthu.id
            temp = json.dumps(temp)
            info = ThongTinCauThu.create(data=json.loads(temp))
            return jsonify(CauThu.get_json(cauthu))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            """
               {
                    "id":" "
                   "id_doi_bong": "",
                   "ghi_chu":"",
                   "ten": "",
                   "ngay_sinh": "",
                   "loai_thong_tin_cau_thu": "",
                   "so_ban_thang": ""
               }
            """
            temp = request.data.decode()
            cauthu = CauThu.update(data=json.loads(temp))
            temp = json.loads(temp)
            temp['id_cau_thu'] = cauthu.id
            temp = json.dumps(temp)
            info = ThongTinCauThu.update(data=json.loads(temp))
            return jsonify(CauThu.get_json(cauthu))

        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/players/<id>')
class PlayerDetail(Resource):
    def get(self, id):
        try:
            player = CauThu.query.get(id)
            response = CauThu.get_json(player)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def delete(self, id):
        try:
            response = CauThu.delete(id)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/sanbongs')
class SanBongList(Resource):
    def get(self):
        try:
            san_bongs = SanBong.query.all()
            response = {
                'length': len(san_bongs),
                'san_bongs': []
            }
            for san_bong in san_bongs:
                response['san_bongs'].append(SanBong.get_json(san_bong))
            return response
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            """
                {
                    "ten_san" : "",
                    "vi_tri" : ""
                }   
            """
            temp = request.data.decode()
            data = json.loads(temp)
            san_bong = SanBong.create(data=data)
            return jsonify(SanBong.get_json(san_bong))
            return None
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            temp = request.data.decode()
            data = json.loads(temp)
            san_bong = SanBong.update(data=data)
            return jsonify(SanBong.get_json(san_bong))
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/sanbongs/<id>')
class SanBongDetail(Resource):
    def get(self, id):
        try:
            san_bong = SanBong.query.get(id)

            return SanBong.get_json(san_bong)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def delete(self, id):
        try:
            response = SanBong.delete(id)

            return response
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/loaibanthangs')
class LoaiBanThangList(Resource):
    def get(self):
        try:
            loai_ban_thangs = LoaiBanThang.query.all()
            response = []
            for loai_ban_thang in loai_ban_thangs:
                response.append(loai_ban_thang.as_dict())
            return response
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            temp = request.data.decode()
            loai_ban_thang = LoaiBanThang.create(data=json.loads(temp))
            return loai_ban_thang.as_dict()
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            temp = request.data.decode()
            loai_ban_thang = LoaiBanThang.update(data=json.loads(temp))
            return loai_ban_thang.as_dict()
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/loaibanthangs/<id>')
class LoaiBanThangDetail(Resource):
    def get(self, id):
        try:
            response = LoaiBanThang.query.get(id)

            return response.as_dict()
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def delete(self, id):
        try:
            response = LoaiBanThang.delete(id)
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/trandaus')
class TranDauList(Resource):
    def get(self):
        try:
            tran_daus = LichThiDau.query.all()
            response = []
            for tran_dau in tran_daus:
                response.append(
                    {
                        'TranDau:': LichThiDau.get_json_tran_dau(tran_dau)

                    })
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/banthangs')
class BanThangList(Resource):
    def get(self):
        try:
            ban_thangs = DsBanThang.query.all()
            response = []
            for ban_thang in ban_thangs:
                response.append(ban_thang.as_dict())
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            temp = request.data.decode()
            ban_thang = DsBanThang.create(data=json.loads(temp))
            return jsonify(ban_thang.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            temp = request.data.decode()
            ban_thang = DsBanThang.update(data=json.loads(temp))
            return jsonify(ban_thang.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# done
@api_namespace.route('/lichthidaus')
class LichThiDauList(Resource):
    def get(self):
        try:
            lichthidaus = LichThiDau.query.all()
            response = []
            for lichthidau in lichthidaus:
                response.append(lichthidau.as_dict())
            return jsonify(LichThiDau.get_json_lich_thi_dau())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        return jsonify({'Error': 'Use /taolichthidau instead'})

    def put(self):
        try:
            temp = request.data.decode()
            lich_thi_dau = LichThiDau.update(data=json.loads(temp))
            return jsonify(lich_thi_dau.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


@api_namespace.route('/muagiais')
class MuaGiaiList(Resource):
    def get(self):
        try:

            mua_giais = MuaGiai.query.all()
            response = []
            for mua_giai in mua_giais:
                response.append(mua_giai.as_dict())
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            temp = request.data.decode()
            mua_giai = MuaGiai.create(data=json.loads(temp))
            return jsonify(mua_giai.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            temp = request.data.decode()
            mua_giai = MuaGiai.update(data=json.loads(temp))
            return jsonify(mua_giai.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)


# tạo lịch thi đấu
@api_namespace.route('/taolichthidau')
class create_schedule(Resource):
    def post(self):
        try:
            # vong dau 1: vong loai, 2: tu ket, 3: ban ket, 4: chung ket
            # lichthidaus = LichThiDau.query.all()
            # for i in lichthidaus:
            #     LichThiDau.delete(i.id)
            temp = json.loads(request.data.decode())
            muagiai = MuaGiai.query.filter(MuaGiai.id == temp['id_mua_giai']).first()
            sanbongs = SanBong.query.all()
            sdate = muagiai.start
            # tạo lịch cho 1 tháng, các tháng còn lại để đá bán kết và chung kết ...
            ptime = random_date(sdate)
            teams = DoiBong.query.all()

            if int(temp['vong_dau']) != 1:  # vòng loại thì có tất cả các đội, vòng trong thì chỉ có đội đã thắng
                won_teams = get_won_teams(temp['vong_dau'])
                teams = []
                for team in won_teams:
                    teams.append(DoiBong.query.get(team))
            teams_length = len(teams)
            if (teams_length % 2) == 0:
                # random các đội với nhau
                list = []
                datas = []
                while len(teams) > 0:
                    team1 = random.choice(teams)
                    # xoá để không trùng
                    teams.remove(team1)
                    team2 = random.choice(teams)
                    teams.remove(team2)
                    sanbong = random.choice(sanbongs)
                    datas.append({
                        'id_mua_giai': temp['id_mua_giai'],
                        'id_doi_1': team1.id,
                        'id_doi_2': team2.id,
                        'id_san_bong': sanbong.id,
                        'vong_dau': temp['vong_dau'],
                        'ngay_thi_dau': ptime,
                        'gio_thi_dau': str(ptime.hour) + ':00',
                        'ti_so': '0'
                    })
                for data in datas:
                    lichthidau = LichThiDau.create(data=data)
                    list.append(lichthidau.id)
                response = []
                for id in list:
                    response.append(LichThiDau.query.get(id).as_dict())
                return jsonify(response)
            return jsonify({'Result': 'Not enough team'})
        except Exception as e:
            return jsonify({'Result': 'Failed'})

# endregion api done


@api_namespace.route('/bangxephangs')
class BangXepHangList(Resource):
    def get(self):
        try:

            bang_xep_hangs = BangXepHang.query.all()
            response = []
            for bang_xep_hang in bang_xep_hangs:
                response.append(bang_xep_hang.as_dict())
            return jsonify(response)
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def post(self):
        try:
            """
            {
                "DoiBong": "ID",
                "Rank": "",
                "MP": "",
                "D": "",
                "L": "",
                "GF": "" / * số bàn thắng * /,
                "GA": "",
                "GD": "" / * hiệu số * /,
            "Pts": "" / * tổng
            điểm * /
            },
            
            
                id = db.Column(db.Integer, primary_key=True, autoincrement=True)
                id_doi_bong = db.Column(db.Integer)
                thang = db.Column(db.Integer)
                thua = db.Column(db.Integer)
                hoa = db.Column(db.Integer)
                hieu_so = db.Column(db.Integer)
                ngay = db.Column(db.DateTime)
            """
            temp = request.data.decode()
            bang_xep_hang = BangXepHang.create(data=json.loads(temp))
            return jsonify(bang_xep_hang.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)

    def put(self):
        try:
            temp = request.data.decode()
            bang_xep_hang = BangXepHang.update(data=json.loads(temp))
            return jsonify(bang_xep_hang.as_dict())
        except Exception as e:
            return wrap_response('Server Internal Error: ' + str(e),
                                 HTTPStatus.INTERNAL_SERVER_ERROR)



# api cap nhat ti so
# endregion api


# region manager

def get_permission_list(args):
    try:
        limit = int(args.get('limit', 100))
        offset = int(args.get('offset', 0))
    except Exception as e:
        LOGGER.error('Bad request', HTTPStatus.BAD_REQUEST)
        return None

    try:
        data = Permission.query.offset(offset).limit(limit).all()
        response = {
            'total': len(data),
            'items': [],
        }
        for element in data:
            item = element.as_dict()
            response['items'].append(item)
        return response
    except Exception as e:
        LOGGER.error('Server Internal Error: ' + str(e), HTTPStatus.INTERNAL_SERVER_ERROR)
        return None


def get_permission_detail(permission_id):
    try:
        permission_id = int(permission_id)
    except Exception as e:
        LOGGER.error('Bad request', HTTPStatus.BAD_REQUEST)
        return None

    try:
        data = Permission.query.filter_by(id=permission_id).first()
        return data.as_dict()
    except Exception as e:
        LOGGER.error('Server Internal Error: ' + str(e), HTTPStatus.INTERNAL_SERVER_ERROR)
        return None


def add_permission(data):
    try:
        key = data.get('key')
        permission = Permission.query.filter_by(key=key).first()
        if permission is not None:
            msg = 'Duplicated permission name'
            LOGGER.error(msg, HTTPStatus.CONFLICT)
            return msg

        new_permission = Permission.create(
            key=data.get('key'),
            name=data.get('name', ''),
            module=data.get('module', ''),
            desc=data.get('desc', ''),
        )
        return new_permission.as_dict()
    except Exception as e:
        return wrap_response('Server Internal Error: ' + str(e),
                             HTTPStatus.INTERNAL_SERVER_ERROR)


def update_permission(data):
    try:
        key = data.get('key')
    except Exception as e:
        LOGGER.error('Bad request', HTTPStatus.BAD_REQUEST)
        return None

    try:
        permission = Permission.query.filter_by(key=key).first()
        if permission is None:
            msg = 'permission not found {key}'.format(key=key)
            LOGGER.error(msg, HTTPStatus.NOT_FOUND)
            return None
        data['id'] = permission.id
        Permission.update(data)
        return permission
    except Exception as e:
        LOGGER.error('Server Internal Error: ' + str(e), HTTPStatus.INTERNAL_SERVER_ERROR)


def get_all_permission_by_user_id(user_id: int):
    try:
        permissions = Permission.query \
            .join(UserPermission, Permission.id == UserPermission.permission_id) \
            .filter(UserPermission.user_id == user_id) \
            .all()
        result = [permissions.as_dict() for permission in permissions]

        roles = get_all_role_by_user_id(user_id=user_id)
        roles_id = [role.get('id') for role in roles]
        permissions_role = Permission.query \
            .join(RolePermission, Permission.id == RolePermission.permission_id) \
            .filter(RolePermission.role_id.in_(roles_id)) \
            .all()
        result.extend([permissions.as_dict() for permission in permissions_role])
        result = list({v['id']: v for v in result}.values())
        return result
    except:
        return None


def get_by_ids(ids: list):
    try:
        perms = Permission.query.filter(Permission.id.in_(ids)).all()
        return [perm.as_dict() for perm in perms] if perms is not None else []
    except Exception as e:
        return None


def get_perms_by_user_id(user_id: int):
    try:
        permissions = Permission.query \
            .join(UserPermission, Permission.id == UserPermission.permission_id) \
            .filter(UserPermission.user_id == user_id) \
            .all()
        return [permissions.as_dict() for permission in permissions]
    except:
        return None


def delete_all_role_by_user_id(user_id: int):
    try:
        UserRole.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        LOGGER.error('Unexpected error occurred when '
                     'deleting all roles of user. Message: ' + str(e))
        db.session.rollback()
        return False


def create_roles_with_user_id(user_id: int, roles_id: list):
    try:
        for role_id in roles_id:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            db.session.add(user_role)
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def delete_all_user_by_role_id(role_id: int):
    try:
        UserRole.query.filter_by(role_id=role_id).delete()
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def delete_all_permission_by_user_id(user_id: int):
    try:
        UserPermission.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def create_permissions_with_user_id(user_id: int, permissions_id: list):
    try:
        for permission_id in permissions_id:
            user_permission = UserPermission(user_id=user_id,
                                             permission_id=permission_id)
            db.session.add(user_permission)
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def has_permission(email, permission_key: list, **kwargs):
    try:
        if kwargs.get('user_id', None) is None:
            user_id = 0
        else:
            user_id = kwargs['user_id']
        if user_id is not None:
            obj = UserPermission.query \
                .filter((UserPermission.user_id == user_id) | (User.email == email),
                        Permission.key.in_(permission_key)) \
                .join(User, UserPermission.user_id == User.id) \
                .join(Permission, UserPermission.permission_id == Permission.id) \
                .first()
            return obj is not None
        return False
    except:
        return False


# def get_by_id(id):
#     """Get an user by ID from cache, if data does not exists in cache then get from database"'"
#     try:
#         key = 'USER:{id}'.format(id=id)
#         user = cache.get(key)
#         if user is None:
#             user = User.query.filter_by(id=id).first()
#             if user is not None:
#                 cache.set(key, user, timeout=300) # 5 minutes
#     except:
#         user = None
#     return user


def get_a_user(user_id):
    try:
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            LOGGER.error('Get user by user_id: {user_id} not found'.format(user_id=user_id))
            return None
        response = user.as_dict()
        response['roles'] = get_all_role_by_user_id(user_id=user.id)
        response['permissions'] = get_all_permission_by_user_id(
            user_id=user.id)
        return response
    except Exception as e:
        LOGGER.error('Get detail user {user_id} has error: {error}'
                     .format(user_id=user_id, error=str(e)))
        return None


def create_user(data):
    try:
        email = data.get('email')
        username = data.get('username')
        user = User.query.filter(
            (User.email == email) | (User.username == username)).first()
        if user is not None:
            LOGGER.error('email/username already existed')
            return None

        new_user = User.create(
            email=data.get('email'),
            username=data.get('email'),
            fullname=data.get('fullname', ''),
            mobile=data.get('mobile', ''),
        )
        db.session.close()
        user = User.query.filter((User.email == email) | (User.username == username)).first()
        id = user.id
        inserted = create_roles_with_user_id(user_id=id,
                                             roles_id=data.get('roles', []))
        if not inserted:
            LOGGER.error('role not inserted')
            return None

        inserted = create_permissions_with_user_id(user_id=id,
                                                   permissions_id=data.get(
                                                       'permissions', []))
        if not inserted:
            LOGGER.error('permission not inserted')
            return None
        return new_user.as_dict()

    except Exception as e:
        db.session.rollback()
        LOGGER.error('Server Internal Error: ' + str(e), HTTPStatus.INTERNAL_SERVER_ERROR)
        return None


def update_user(data):
    try:
        id = int(data.get('id'))
    except Exception as e:
        LOGGER.error(e)
        return None

    try:
        user = User.query.filter((User.email == data.get('email')) | (
                User.username == data.get('username'))).first()
        if user is not None and user.id != id:
            LOGGER.error('email/username already existed')
            return None

        user = User.query.filter_by(id=id).first()
        if user is None:
            LOGGER.error('user id {} NOT EXIST in our system.'.format(id))
            return None
        res = user.update(data)
        LOGGER.info('update_user result {} | updated data: {}'.format(res, data))
        deleted = delete_all_role_by_user_id(user_id=id)
        if not deleted:
            LOGGER.error('Failed to Delete old roles of user id: {}'.format(id))
            return None
        insert_data = data.get('roles', [])
        inserted = create_roles_with_user_id(user_id=id,
                                             roles_id=insert_data)
        if not inserted:
            LOGGER.error('Failed to RE-INSERT new roles of user id: {}'.format(id))
            return None

        deleted = delete_all_permission_by_user_id(user_id=id)
        if not deleted:
            LOGGER.error('Failed to Delete old permissions of user id: {}'.format(id))
            return None

        perm_ids = data.get('permissions', [])
        inserted = create_permissions_with_user_id(user_id=id,
                                                   permissions_id=perm_ids)
        if not inserted:
            LOGGER.error('Failed to RE-INSERT new permissions of user id: {}'.format(id))
            return None

        # perm_lst = get_by_ids(perm_ids)
        # can_auto_process = any(permissions['order_process'] == perm['key']
        #                        for perm in perm_lst) if len(perm_lst) > 0 else False

        # get team which user belongs to
        # updated_user = User.query.filter_by(id=id).first()
        return []
    except Exception as e:
        LOGGER.error(e)
        return None


def assign_role(data):
    try:
        user_id = int(data.get('user_id'))
        role_id = int(data.get('role_id'))
    except Exception as e:
        LOGGER.error(e)
        return None

    try:
        user = User.query.filter_by(id=user_id).first()
        role = Role.query.filter_by(id=role_id).first()

        if user is None:
            LOGGER.error('User not found')
            return None

        if role is None:
            LOGGER.error('Role not found')
            return None

        user_role = UserRole.query.filter_by(user_id=user_id,
                                             role_id=role_id).first()
        if user_role is not None:
            LOGGER.error('User already assigned with the given role. No effect.')
            return None
        else:
            msg = 'Successfully assign'
            UserRole.create(user_id=user_id, role_id=role_id)
            return user.as_dict()
    except Exception as e:
        LOGGER.error(e)
        return None


def get_raw_user_by_id(id: int):
    user = User.query.filter_by(id=id).first()
    return user


def get_by_email(email):
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        LOGGER.error(e)
        return None
    return user.as_dict() if user is not None else None


def get_by_sso_id(sso_id):
    try:
        user = User.query.filter_by(sso_user_id=sso_id).first()
        return user.as_dict()
    except Exception as e:
        LOGGER.error(e)
        return None


# def generate_table(in_fields, table_name):
#     if isinstance(in_fields, dict):
#         # get info from json
#         fields = de_json(in_fields)
#         query = ''
#         for value in fields:
#             if query != '':
#                 query = query + ','
#             field_name = value
#             query = query + field_name + ' '
#             field_type = fields[value]
#             query = query + field_type
#
#         cur = generate_connection().cursor()
#
#         execute_query = 'CREATE TABLE ' + table_name + ' (' + query + ')'
#         cur.execute(execute_query)


# def generate_token(user):
#     try:
#         # generate the auth token
#         auth_token = User.encode_auth_token(user.id)
#         response_object = {
#             'status': 'success',
#             'message': 'Successfully registered.',
#             'Authorization': auth_token.decode()
#         }
#         return response_object, 201
#     except Exception as e:
#         response_object = {
#             'status': 'fail',
#             'message': 'Some error occurred. Please try again.'
#         }
#         return response_object, 401


# def validate_access_token(data):
#     resp = get_info_token(data)
#     if resp is None:
#         LOGGER.error('User doesn\'t have permission access to our system.')
#         return None
#
#     user_data = {
#         'email': resp.get('email'),
#         'sso_user_id': resp.get('id')
#     }
#     our_user_info = User.update(user_data)
#     if our_user_info is None:
#         LOGGER.error('User doesnt exist in system')
#         return None
#
#     wrapped_resp = resp.copy()
#     wrapped_resp['user_id'] = our_user_info.id
#     wrapped_resp['is_leader'] = is_leader(our_user_info.id)
#     wrapped_resp['is_manager'] = is_manager(our_user_info.id)
#     wrapped_resp['roles'] = get_all_role_by_user_id(
#         user_id=our_user_info.id)
#     wrapped_resp['permission'] = get_all_permission_by_user_id(
#         user_id=our_user_info.id)
#     user_teams = get_teams_by_user(our_user_info.id)
#     wrapped_resp['team_ids'] = [team.get('id') for team in user_teams] \
#         if user_teams is not None else []
#     if our_user_info.email in configs.REVIEW_NATION_DEBT_USERS:
#         wrapped_resp['order_review_debt'] = 1
#
#     user_team_statuses = get_user_status_by_id(our_user_info.id)
#     wrapped_resp['status'] = user_team_statuses.get('status') if user_team_statuses is not None \
#         else UserStatuses.OFFLINE
#
#     return wrapped_resp


def get_role_list(args):
    try:
        limit = int(args.get('limit', 100))
        offset = int(args.get('offset', 0))
        if limit < 0 or offset < 0:
            msg = 'Error'
            LOGGER.error(msg, HTTPStatus.BAD_REQUEST)
            return None
    except Exception as e:
        LOGGER.error(e)
        return None

    try:
        roles = Role.query.offset(offset).limit(limit).all()
        response = {
            'total': len(roles),
            'items': [],
        }
        for role in roles:
            item = role.as_dict()
            permissions = Permission.query \
                .join(RolePermission,
                      Permission.permission_id == RolePermission.permission_id) \
                .filter(RolePermission.role_id == role.id)
            item['permissions'] = [permission.as_dict() for permission in
                                   permissions]
            response['items'].append(item)
        return response
    except Exception as e:
        LOGGER.error(e)
        return None


def get_role_detail(role_id):
    try:
        role_id = int(role_id)
    except Exception as e:
        LOGGER.error(e)
        return None

    try:
        role = Role.query.filter_by(id=role_id).first()
        if role is None:
            msg = 'Role id not found'
            LOGGER.error(msg, HTTPStatus.NOT_FOUND)
            return None

        response = role.as_dict()
        permissions = Permission.query \
            .join(RolePermission, Permission.id == RolePermission.permission_id) \
            .filter(RolePermission.role_id == role.id)
        response['permissions'] = [permission.as_dict() for permission in
                                   permissions]
        return response
    except Exception as e:
        LOGGER.error(e)
        return None


def add_role(data):
    try:
        new_role = Role.create(
            name=data.get('name'),
            desc=data.get('desc'),
        )

        id = new_role.id
        inserted = create_permissions_with_role_id(role_id=id,
                                                   permissions_id=data.get(
                                                       'permissions', []))
        if not inserted:
            LOGGER.error('Not Inserted')
            return None

        return Role.query.get(id).as_dict()
    except Exception as e:
        db.session.rollback()
        LOGGER.error(e)
        return None


def update_role(data):
    try:
        id = int(data.get('id'))
    except Exception as e:
        LOGGER.error(e)
        return None

    try:
        role = Role.query.filter_by(id=id).first()
        if role is None:
            msg = 'Role id not found'
            LOGGER.error(msg, HTTPStatus.BAD_REQUEST)
            return None

        role.update(data)
        deleted = delete_all_permission_by_role_id(role_id=id)
        if not deleted:
            msg = 'Not deleted'
            LOGGER.error(msg, HTTPStatus.INTERNAL_SERVER_ERROR)
            return None
        inserted = create_permissions_with_role_id(role_id=id,
                                                   permissions_id=data.get('permissions', []))
        if not inserted:
            msg = 'Not inserted'
            LOGGER.error(msg, HTTPStatus.INTERNAL_SERVER_ERROR)
            return None

        return Role.query.get(id).as_dict()
    except Exception as e:
        LOGGER.error(e)
        return None


def delete_role(role_id):
    try:
        role_id = int(role_id)
    except Exception as e:
        LOGGER.error(e)
        return None

    try:
        delete_permission = delete_all_permission_by_role_id(role_id=role_id)
        if not delete_permission:
            msg = 'Not deleted permission'
            LOGGER.error(msg, HTTPStatus.INTERNAL_SERVER_ERROR)
            return None
        delete_user = delete_all_user_by_role_id(role_id=role_id)
        if not delete_user:
            msg = 'Not deleted user'
            LOGGER.error(msg, HTTPStatus.INTERNAL_SERVER_ERROR)
            return None

        role = Role.query.filter(Role.id == role_id).first()
        if role is None:
            LOGGER.error('Get role by role_id: {role_id} not found'.format(role_id=role_id))
            return None
        Role.delete(role_id=role_id)
        return role.as_dict()
    except Exception as e:
        LOGGER.error(e)
        return None


# method
def get_all_role_by_user_id(user_id):
    try:
        roles = Role.query \
            .join(UserRole, Role.id == UserRole.role_id) \
            .filter(UserRole.user_id == user_id) \
            .all()
        return [role.as_dict() for role in roles]
    except Exception as e:
        LOGGER.error(e)
        return None


def delete_all_permission_by_role_id(role_id: int):
    try:
        RolePermission.query.filter_by(role_id=role_id).delete()
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def create_permissions_with_role_id(role_id: int, permissions_id: list):
    try:
        for permission_id in permissions_id:
            role_permission = RolePermission(role_id=role_id,
                                             permission_id=permission_id)
            db.session.add(role_permission)
        db.session.commit()
        db.session.close()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def get_won_teams(vong_dau):
    won_team = []
    temp = []
    lichthidaus_vong_dau = LichThiDau.query.filter(LichThiDau.vong_dau == int(vong_dau)).all()
    for lichthidau_vong_dau in lichthidaus_vong_dau:
        temp.append(lichthidau_vong_dau.as_dict())

    lichthidaus = LichThiDau.query.filter(LichThiDau.vong_dau == int(
        vong_dau) - 1).all()  # thêm điều kiện chưa thêm vào vòng đấu hiện tại và thời gian trận đấu < hiện tại
    a = 1
    for lichthidau in lichthidaus:
        # format: x:y

        if (datetime.datetime.now() - lichthidau.ngay_thi_dau).seconds > 100 and (
                datetime.datetime.now() - lichthidau.ngay_thi_dau).days >= 0:
            for tmp in temp:
                if tmp['id_doi_1'] == lichthidau.id_doi_1 and tmp['id_doi_2'] == lichthidau.id_doi_2:
                    continue
            ti_so = lichthidau.ti_so
            bool_ts1 = True
            ts1 = ''
            ts2 = ''
            for i in range(0, len(ti_so)):
                if ti_so[i] == ':':
                    bool_ts1 = False
                else:
                    if bool_ts1:
                        ts1 = ts1 + ti_so[i]
                    else:
                        ts2 = ts2 + ti_so[i]
            if int(ts1) > int(ts2):
                won_team.append(lichthidau.id_doi_1)
            else:
                won_team.append(lichthidau.id_doi_2)
    return won_team


# random end date
def random_date(sdate):
    edate = datetime.datetime.strptime(str(sdate.day) + '/' + str(sdate.month + 1) + '/' + str(sdate.year),
                                       '%d/%m/%Y')
    prop = random.random()
    ptime = sdate + prop * (edate - sdate)
    # random hour from 9:00 - 19:00
    hour = random.randint(9, 19)
    ptime = ptime.replace(hour=hour)
    ptime = ptime.replace(minute=0)
    return ptime


# endregion manager


# region utils

def get_client_ip(request):
    try:
        if request.headers.getlist("X-Forwarded-For"):
            x_forwarded_for = request.headers.getlist('X-Forwarded-For')[0]
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.remote_addr
        return ip
    except:
        return None


# def :
#     ip = get_client_ip(request)
#     try:
#         token = request.headers['Authorization'].split()[1]
#         sso_info = get_info_token(token)
#         actor = sso_info.get('email')
#     except:
#         actor = None
#
#     logger.info('Request | ip: {} | url: {} | method: {} | payload: {} | actor: {}'.format(
#         ip,
#         request.full_path,
#         request.method,
#         request.data,
#         actor
#     ))


class InternalErrorCode:
    UNAUTHORIZED = 8
    INTERNAL_SERVER_ERROR = 1
    BAD_REQUEST = 2
    SUCCESS = 0
    NOT_FOUND = 14
    CONFLICT = 15


mapping_internal_codes = {
    HTTPStatus.UNAUTHORIZED: InternalErrorCode.UNAUTHORIZED,
    HTTPStatus.BAD_REQUEST: InternalErrorCode.BAD_REQUEST,
    HTTPStatus.OK: InternalErrorCode.SUCCESS,
    HTTPStatus.NOT_FOUND: InternalErrorCode.NOT_FOUND,
    HTTPStatus.CONFLICT: InternalErrorCode.CONFLICT,
    HTTPStatus.INTERNAL_SERVER_ERROR: InternalErrorCode.INTERNAL_SERVER_ERROR
}

mapping_ops_channel_role = {
    2: 'Online Leader',
    4: 'Agent Leader'
}

mapping_om_statuses = {
    'DRAFT': 'WAITING-PROCESS',
    'SUCCESS': 'PROCESSED',
    'CANCELLED-DRAFT': 'CANCELLED-DRAFT',
    'CANCELLED': 'CANCELLED'
}

mapping_channel = {
    1: 'SHOWROOM',
    2: 'ONLINE',
    3: 'Telesale',
    4: 'AGENT',
    5: 'VNSHOP'
}


class TeamStatus:
    ACTIVE = 1
    INACTIVE = 0


permissions = {
    'order_area_transferring': 'order_area_transferring',
    'order_process': 'order_process',
    'order_review_debt': 'order_review_debt',
    'order_cancel': 'order_cancel',
}


class CacheTimeout:
    LO_LIST_REGION = 300
    CLIENT_TOKEN = 900
    LIST_SALESMEN = 600


class UserStatuses:
    OFFLINE = 0
    ONLINE = 1
    IDLE = 2


class OrphanOrderStatus:
    IN_PROCESSED = 1
    NO_PROCESSED = 0


class CacheKey:
    LIST_SALESMEN = 'list_salesmen'
    ORDER_PROCESSING_BY_USER = 'order_processing_by_user'


def memoize(func):
    """
    Memoize function, can be used as decorator
    Does not share memoized cache between processes
    :param func: function should be cache
    :return:
    """
    memoized_cache = dict()

    def memoized_func(*args):
        if args in memoized_cache:
            return memoized_cache[args]
        result = func(*args)
        memoized_cache[args] = result
        return result

    return memoized_func


# def method_dispatch(func):
#     dispatcher = functools.singledispatch(func)
#
#     def wrapper(*args, **kw):
#         return dispatcher.dispatch(args[1].__class__)(*args, **kw)
#
#     wrapper.register = dispatcher.register
#     functools.update_wrapper(wrapper, func)
#     return wrapper


def ignore_first_call(fn):
    called = False

    def wrapper(*args, **kwargs):
        nonlocal called
        if called:
            return fn(*args, **kwargs)
        else:
            called = True
            return None

    return wrapper


def authorized(fn):
    """Decorator that checks that requests
    contain an id-token in the request header.

    Usage:
    @app.route("/")
   
    """

    def _wrap(*args, **kwargs):
        pass

        return fn(*args, **kwargs)

    return _wrap


# def validate_offset_limit(fn):
#     """Decorator that validate offset limit in request.args
#        Usage:
#        @validate_offset_litmit
#        """
#
#     def _wrap(*args, **kwargs):
#         params = request.args
#         schema_offset_limit = OffsetLimitSchema()
#         schema_offset_limit.load_data(params)
#         if not (schema_offset_limit.is_valid()):
#             abort(400, data={},
#                   error={"code": 8,
#                          "detail": "Bad request"})
#         data = schema_offset_limit.data
#         kwargs.update({'limit': data['limit'], 'offset': data['offset']})
#         return fn(*args, **kwargs)
#
#     return _wrap


# def validate_params(model):
#     """Decorator that validate params filter in request.args
#        Usage:
#        @validate_params(model)
#        """
#
#     def decorator(f):
#         def _wrap(*args, **kwargs):
#             params = request.args
#             schema = set_up_schema(model)
#             schema.load_data(params)
#             if not (schema.is_valid()):
#                 abort(400, data={},
#                       error={"code": 8,
#                              "detail": "Bad request"})
#             data = schema.data
#             kwargs.update(data)
#             return f(*args, **kwargs)
#
#         return _wrap
#
#     return decorator
#

def import_class_by_path(class_path: str):
    """
    Import class by path
    :param class_path: module path of class
    :return: Class

    :example:
        import_class_by_path('core.db.DatabaseClass')
    """
    class_path = class_path.split('.')
    class_name = class_path.pop()
    module_path = '.'.join(class_path)
    module = importlib.import_module(module_path)
    class_ = getattr(module, class_name)
    return class_


def to_json(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


def read_firebase_cred(fb_server_acc):
    with open('/tmp/gsa.json', 'w') as outfile:
        json.dump(fb_server_acc, outfile)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gsa.json"


def obj_to_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def intersection(lst1, lst2):
    """
    Find the intersection of 2 given lists
    :param lst1:
    :param lst2:
    :return:
    """
    return [item for item in lst1 if item in lst2]


class NullSettings:
    pass


#
# class RedisHelper:
#     _connections = {}
#     settings = None
#
#     def __init__(self):
#         os.environ.setdefault('SETTINGS_MODULE', 'configs')
#         if os.environ.get('SETTINGS_MODULE', None) is not None:
#             self.settings = importlib.import_module(os.environ.get('SETTINGS_MODULE'))
#         else:
#             self.settings = NullSettings()
#
#         if not hasattr(self.settings, 'REDIS'):
#             setattr(self.settings, 'REDIS', {})
#
#     def connect(self, config_key, config_dict=None):
#         if not isinstance(config_dict, dict):
#             if config_key not in self.settings.REDIS:
#                 return False
#             else:
#                 config_dict = self.settings.REDIS[config_key]
#
#         options = config_dict.get('OPTIONS', None)
#         if not isinstance(options, dict):
#             options = {}
#         max_connections = options.get('MAX_CONNECTION', 100)
#         socket_path = config_dict.get('SOCKET_PATH', None)
#         host = config_dict.get('HOST', '127.0.0.1')
#         port = config_dict.get('PORT', 6379)
#         db = config_dict.get('DB', 0)
#         self._connections[config_key] = redis.Redis(
#             host=host, port=port, db=db, unix_socket_path=socket_path,
#             max_connections=max_connections,
#             ssl_keyfile=options.get('SSL_KEYFILE', None),
#             ssl_certfile=options.get('SSL_CERTFILE', None),
#             ssl_cert_reqs=options.get('SSL_CERT_REQS', None),
#             ssl_ca_certs=options.get('SSL_CA_CERTS', None),
#             ssl=options.get('SSL', False)
#         )
#         return self._connections[config_key]
#
#     def get_connection(self, config_key):
#         if not self.is_connected(config_key):
#             self.connect(config_key)
#         return self._connections[config_key]
#
#     def get_connections(self):
#         for key, config in self.settings.REDIS.items():
#             self.get_connection(key)
#         return self._connections
#
#     def is_connected(self, config_key):
#         if config_key not in self._connections:
#             return False
#         return self._connections[config_key] is not None


# redis_helper = RedisHelper()
# REDIS_CONNECTIONS = redis_helper.get_connections()

# endregion utils

# api.add_resource(user, '/users')


if __name__ == '__main__':
    app.run()
