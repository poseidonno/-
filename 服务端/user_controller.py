# 呐喊
# 开发时间: 2024/6/5 上午11:50
import json
import os

from flask import Flask, request, jsonify
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError

from models import db, User, Device, UserDevice, CommonResult  # 导入models中的类
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


# 用户注册
@app.route('/user', methods=['POST'])  # 定义POST /user路由，处理用户注册请求
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
@app.route('/user/login', methods=['POST'])  # 定义POST /user/login路由，处理用户登录请求
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user:
        if user.password == data['password']:  # 检查密码是否匹配
            devices = UserDevice.query.filter_by(user_id=user.id).all()  # 查询用户的设备
            device_list = [device.device_id for device in devices]  # 获取设备ID列表
            result = CommonResult(True, "登录成功！", device_list)
        else:
            result = CommonResult(False, "密码错误！")
    else:
        result = CommonResult(False, "当前用户不存在,请注册！")
    return jsonify(result.__dict__)  # 返回响应，转换为JSON格式


# 获取所有用户
@app.route('/user', methods=['GET'])  # 定义GET /user路由，处理获取所有用户请求
def get_all_users():
    users = User.query.all()  # 查询所有用户
    if not users:
        return jsonify([])
    else:
        user_list = [{'id': user.id, 'username': user.username, 'password': user.password} for user in users]
        return jsonify(user_list)


# 验证用户是否存在
@app.route('/user/verifyuser', methods=['POST'])  # 定义POST /user/verifyuser路由，处理用户验证请求
def verify_user():
    data = request.json  # 获取请求数据，解析为JSON格式
    user = User.query.filter_by(username=data['username']).first()  # 根据用户名查询用户
    if user:
        result = CommonResult(False, "用户已存在")  # 用户已存在，创建CommonResult对象
    else:
        result = CommonResult(True, "请输入密码！")  # 用户不存在，创建CommonResult对象
    return jsonify(result.__dict__)  # 返回响应，转换为JSON格式


def test_database_connection():
    """连接数据库测试"""
    try:
        text_query = text('SELECT 1')
        result = db.session.execute(text_query)
        print("数据库连接成功！")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()  # 获取所有表格
        print("数据库中存在的表格：", tables)
    except Exception as e:
        print("数据库连接失败：", e)  # 如果连接失败或其他错误，则打印错误信息


def test_register():
    """ 用户注册测试 """
    response = app.test_client().post(
        '/user',
        data=json.dumps({'username': 'nahan', 'password': '11111111'}),
        content_type='application/json',
    )
    print(response.get_json())


def test_login():
    """ 用户登录测试 """
    response = app.test_client().post(
        '/user/login',
        data=json.dumps({'username': 'nahan', 'password': '11111111'}),
        content_type='application/json',
    )
    print(response.get_json())


def test_verify_user():
    """ 验证用户是否存在测试 """
    response = app.test_client().post(
        '/user/verifyuser',
        data=json.dumps({'username': 'nahan'}),
        content_type='application/json',
    )
    print(response.get_json())


def test_get_all_users():
    """返回所有用户信息"""
    response = app.test_client().get('/user')
    print(response.get_json())


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 根据定义的模型类创建所有表
        test_database_connection()  # 测试数据库连接
        test_register()  # 测试注册用户
        test_login()  # 测试用户登录
        test_verify_user()  # 测试验证用户是否存在
        test_get_all_users()  # 测试获取所有用户
    app.run(debug=False)  # 运行Flask应用，开启调试模式
