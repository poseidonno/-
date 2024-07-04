# 呐喊
# 开发时间: 2024/6/5 上午11:50
import asyncio
import json
import os

from flask import Flask, request, jsonify
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError

from models import db, User, Device, UserDevice, CommonResult, UserDeviceDto  # 导入models中的类

app = Flask(__name__)
"""配置数据库"""
username = os.getenv('DB_USERNAME', 'root')
password = os.getenv('DB_PASSWORD', '123456')
host = os.getenv('DB_HOST', 'localhost')
database = os.getenv('DB_NAME', 'fun_server')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{username}:{password}@{host}/{database}'
db.init_app(app)  # 初始化db实例
"""
路由设置 GET 用于获取资源，POST 用于提交数据
"""


@app.route('/', methods=['GET'])
def aa():
    return 'he'


# 用户注册
@app.route('/user', methods=['POST'])
def register():
    data = request.json  # 获取请求数据，解析为JSON格式
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        result = CommonResult(False, "用户名和密码不能为空")
        return jsonify(result.__dict__)
    # 检查用户名是否已经存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        result = CommonResult(False, "用户名已存在")
        return jsonify(result.__dict__)
    # 创建新用户对象
    new_user = User(username=username, password=password)
    try:
        db.session.add(new_user)
        db.session.commit()  # 提交会话，保存到数据库
        result = CommonResult(True, "注册成功！")  # 表示注册成功
    except IntegrityError:  # 捕捉唯一约束错误（如用户名已存在） 完整性约束
        db.session.rollback()  # 回滚会话
        result = CommonResult(False, "注册失败，请重试")  # 表示注册失败
    return jsonify(result.__dict__)  # 返回响应，转换为JSON格式


# 用户登录
@app.route('/user/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user:
        if user.password == data['password']:  # 检查密码是否匹配
            devices = UserDevice.query.filter_by(user_id=user.id).all()  # 查询用户的设备
            device_list = [device.device_id for device in devices]  # 获取设备ID列表
            print(device_list)
            result = CommonResult(True, "登录成功！", device_list)
        else:
            result = CommonResult(False, "密码错误！")
    else:
        result = CommonResult(False, "当前用户不存在,请注册！")
    print(111111111111111111111111111)
    return jsonify(result.__dict__)  # 返回响应，转换为JSON格式


# 获取所有用户
@app.route('/user', methods=['GET'])
def get_all_users():
    users = User.query.all()  # 查询所有用户
    if not users:
        return jsonify([])
    else:
        user_list = [{'id': user.id, 'username': user.username, 'password': user.password} for user in users]
        return jsonify(user_list)


# 验证用户是否存在 用于判断注册用户的信息
@app.route('/user/verify_user', methods=['POST'])
def verify_user():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()  # 根据用户名查询用户
    if user:
        result = CommonResult(False, "用户已存在")  # 用户已存在，创建CommonResult对象
    else:
        result = CommonResult(True, "请输入密码！")  # 用户不存在，创建CommonResult对象
    return jsonify(result.__dict__)  # 返回响应，转换为JSON格式


# @app.route('/DeviceCommand', methods=['POST'])
# def device_command():
#     data = request.json  # 获取请求数据，解析为 JSON 格式
#     message = data.get('message')  # 获取消息内容
#     if not message:
#         return jsonify({"success": False, "message": "消息内容不能为空"}), 400
#     message_json = json.loads(message)  # 将字符串转为json格式
#     # print(message_json, type(message_json))
#     command = message_json['command']
#     print(command)
#     response = sendmsg(command)  # 调用 sendmsg 函数发送消息
#     if response == "空":
#         return jsonify({"success": False, "message": "发送消息超时"})
#     else:
#         return jsonify({"success": True, "response": response})


# def test_socket():
#     """ 设备指令发送测试 """
#     response = app.test_client().post(
#         '/DeviceCommand',
#         data=json.dumps({'message': '开'}),  # 测试数据
#         content_type='application/json',
#     )
#     print(response.get_json())  # 打印服务器响应


if __name__ == '__main__':
    # with app.app_context():
    #     test_socket()
    #     db.create_all()  # 根据定义的模型类创建所有表
    #     test_database_connection()  # 测试数据库连接
    #     test_register()  # 测试注册用户
    #     test_login()  # 测试用户登录
    #     test_verify_user()  # 测试验证用户是否存d在
    #     test_get_all_users()  # 测试获取所有用户
    app.run(host='192.168.158.203', port=5000, debug=False)  # 运行Flask应用，开启调试模式
