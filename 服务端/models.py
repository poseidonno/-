# 呐喊
# 开发时间: 2024/6/6 下午3:36
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy  # 从flask_sqlalchemy库中引入SQLAlchemy，用于数据库操作

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, comment='设备id')  # 表示第几个用户 id 默认自增长
    username = db.Column(db.String(20), nullable=False, comment='用户名')
    password = db.Column(db.String(20), nullable=False, comment='用户密码')
    user_devices = relationship('UserDevice', back_populates='user')


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_uuid = db.Column(db.String(20), nullable=False, comment='设备id-mac地址')
    device_name = db.Column(db.String(20), nullable=False, comment='设备名称')
    user_devices = relationship('UserDevice', back_populates='device')


class UserDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    user = relationship('User', back_populates='user_devices')
    device = relationship('Device', back_populates='user_devices')


class CommonResult:  # 定义CommonResult类，用于统一返回的响应格式
    def __init__(self, status, message, device_list=None):
        self.status = status  # 设置响应状态
        self.message = message  # 设置响应消息
        self.device_list = device_list  # 设置设备列表


# DTO 类定义 用于数据传输对象
class UserDeviceDto:
    def __init__(self, device_uuid, user_name, device_name):
        self.device_uuid = device_uuid
        self.user_name = user_name
        self.device_name = device_name


class Temp:
    def __init__(self, device_id, message):
        self.device_id = device_id
        self.message = message
