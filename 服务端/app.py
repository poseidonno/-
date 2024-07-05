import io
import os
from collections import defaultdict
from datetime import datetime

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from matplotlib import pyplot as plt

from rec_main import run_recognition
from server import sendmsg
from mysql.connector.pooling import MySQLConnectionPool
from user_records import UserRecords

# 数据库配置
DB_CONFIG = {
    'user': os.getenv('DB_USERNAME', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'fun_server')
}

# 创建数据库连接池
db_pool = MySQLConnectionPool(**DB_CONFIG)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 加密通话
USER = None  # 当前 用户
# 初始化变量
low_ = 15
high_ = 30
nowwd = 0  # 当前温度
now_tmepRh = 0  # 当前湿度
wors = ["温", "湿"]  # 模式名称
loc = 0  # 当前模式索引


# 用户登录验证
def validate_login(username, password):
    try:
        cnx = db_pool.get_connection()
        cursor = cnx.cursor(prepared=True)
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        result = cursor.fetchone()
        if not result:
            return False, "用户名不存在"
        stored_password = result[0]
        if stored_password == password:
            return True, None
        else:
            return False, "密码错误"
    finally:
        cursor.close()
        cnx.close()


# 检查用户名是否存在
def check_username_exists(username):
    try:
        cnx = db_pool.get_connection()
        cursor = cnx.cursor(prepared=True)
        cursor.execute("SELECT COUNT(*) FROM user WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result[0] > 0:
            return True
        else:
            return False
    finally:
        cursor.close()
        cnx.close()


# 用户注册
def register_user(username, password):
    try:
        cnx = db_pool.get_connection()
        cursor = cnx.cursor(prepared=True)
        if check_username_exists(username):
            return False, "用户名已存在"
        insert_query = "INSERT INTO user (username, password) VALUES (%s, %s)"
        cursor.execute(insert_query, (username, password))
        cnx.commit()
        return True, None
    finally:
        cursor.close()
        cnx.close()


@app.route('/')
def show_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    global USER
    username = request.form['username']
    password = request.form['password']
    success, message = validate_login(username, password)
    if success:
        USER = UserRecords(username)  # 添加用户记录表
        return redirect(url_for('control_panel_view'))  # 跳转网页
    else:
        flash(message)
        return redirect(url_for('show_login'))


@app.route('/register', methods=['POST'])
def register():
    global USER
    username = request.form['username']
    password = request.form['password']
    success, message = register_user(username, password)
    if success:
        USER = UserRecords(username)  # 添加用户记录表
        flash("注册成功！")
        return redirect(url_for('control_panel_view'))
    else:
        flash(message)
        return redirect(url_for('show_login'))


@app.route('/control_panel')
def control_panel_view():
    return render_template('control_panel.html')


# 用户控制
@app.route('/fan_control', methods=['POST'])
def fan_control():
    global USER
    command = request.json.get('command')
    # 根据command执行相应的风扇控制操作
    if command == 'low':
        sendmsg("开-500")
        USER.add_record("低速")
    elif command == 'medium':
        sendmsg("开-800")
        USER.add_record("中速")
    elif command == 'high':
        sendmsg("开-1023")
        USER.add_record("高速")
    elif command == 'off':
        sendmsg("关")
        USER.add_record("关闭")
    elif command == 'reverse':
        sendmsg("反转")
        USER.add_record("反转")
    # 返回一个空的JSON响应，表示成功
    return jsonify({})


# 设置最低阈值
@app.route('/set_low_temp', methods=['POST'])
def set_low_temp():
    low_temp = request.json.get('low_temp')
    global low_
    low_ = low_temp
    # 发送设置最低温度命令给服务器
    sendmsg(f"setvalue-0-{low_temp}")
    USER.add_record(f"设置最低阈值为{low_temp}")
    # 返回一个空的JSON响应，表示成功
    return jsonify({})


# 设置最高阈值
@app.route('/set_high_temp', methods=['POST'])
def set_high_temp():
    high_temp = request.json.get('high_temp')
    global high_
    high_ = high_temp
    # 发送设置最高温度命令给服务器
    sendmsg(f"setvalue-1-{high_temp}")
    USER.add_record(f"设置最高阈值为{high_temp}")
    return jsonify({})


# 开自动控制 温/湿控制 设置最高最低阈值
@app.route('/open_auto_control', methods=['POST'])
def open_auto_control():
    global low_, high_
    low_temp = 40
    high_temp = 70
    # 自动设置最低和最高阈值
    low_ = low_temp
    high_ = high_temp
    # 发送设置最低和最高温度命令给服务器
    sendmsg(f"setvalue-0-{low_temp}")
    sendmsg(f"setvalue-1-{high_temp}")
    # 返回一个空的JSON响应，表示成功
    return jsonify({})


@app.route('/close_auto_control', methods=['POST'])
def close_auto_control():
    sendmsg("关")
    # 返回一个空的JSON响应，表示成功
    return jsonify({})


# 温湿度切换
@app.route('/switch_control', methods=['POST'])
def switch_control():
    global loc
    loc = 1 - loc
    # 发送切换温湿度控制命令给服务器
    sendmsg("温湿切换-" + str(loc))
    # 返回一个包含新的 loc 值的 JSON 响应
    return jsonify({'loc': loc})


# 获取服务端请求
@app.route('/getmsg', methods=['GET'])
def getmsg():
    global low_, high_, nowwd, now_tmepRh
    strs = sendmsg("getmsg")
    if strs == "空":
        return jsonify({})
    nowwd = int(strs.split("-")[0])  # 当前温度
    now_tmepRh = int(strs.split("-")[1])  # 当前湿度
    low_ = int(strs.split("-")[2])
    high_ = int(strs.split("-")[3])
    # 构建 JSON 响应
    response_data = {
        'nowwd': nowwd,
        'now_tmepRh': now_tmepRh,
        'low_': low_,
        'high_': high_,
    }
    return jsonify(response_data)


# 手势识别
@app.route('/handIdentify', methods=['POST'])
def hand_identify():
    run_recognition()
    return jsonify({})

# 用户中心
@app.route('/userCenter', methods=['GET'])
def user_center():
    return render_template('user_center.html')


# 用户修改密码
@app.route('/change_password', methods=['POST'])
def change_password():
    # 从请求中获取当前密码、新密码和确认密码
    current_password = request.json.get('currentPassword')
    new_password = request.json.get('newPassword')
    confirm_password = request.json.get('confirmPassword')
    # 检查新密码和确认密码是否一致
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': '新密码与确认密码不匹配'})
    global USER
    username = USER.username  # 假设UserRecords类中有username属性
    try:
        cnx = db_pool.get_connection()
        cursor = cnx.cursor(prepared=True)
        # 首先验证当前密码是否正确
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'message': '用户名不存在'})
        stored_password = result[0]
        if stored_password != current_password:
            return jsonify({'success': False, 'message': '当前密码不正确'})
        # 更新数据库中的密码
        update_query = "UPDATE user SET password = %s WHERE username = %s"
        cursor.execute(update_query, (new_password, username))
        cnx.commit()
        return jsonify({'success': True, 'message': '密码修改成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'密码修改失败：{str(e)}'})
    finally:
        cursor.close()
        cnx.close()


# 用户记录查询记录
@app.route('/showUsageChart', methods=['GET'])
def showUsageChart():
    global USER
    username = USER.username
    # 获取用户的使用记录
    try:
        cnx = db_pool.get_connection()
        cursor = cnx.cursor(dictionary=True)    # 字典游标
        query = "SELECT command, time FROM user_records WHERE username = %s"
        cursor.execute(query, (username,))
        records = cursor.fetchall()
        # 统计用户命令的次数
        command_stats = defaultdict(lambda: defaultdict(int))
        for record in records:
            command = record['command']
            timestamp = record['time']
            date_str = timestamp.strftime("%m-%d")
            command_stats[date_str][command] += 1
        # 输出统计信息到控制台
        for date_str, commands in command_stats.items():
            print(f"日期: {date_str}")
            for command, count in commands.items():
                print(f"  命令: {command}，次数: {count}")
        # 绘制柱状图
        fig, ax = plt.subplots()    # 创建图像和坐标轴对象
        dates = sorted(command_stats.keys())
        commands = set()
        for date_str in dates:
            commands.update(command_stats[date_str].keys())  # 存储命令
        commands = sorted(commands)
        bar_width = 0.1
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        bars = []   # 存储每个命令的柱状图对象
        for i, command in enumerate(commands):
            counts = [command_stats[date_str][command] for date_str in dates]
            bar = ax.bar([d + bar_width * i for d in range(len(dates))], counts, bar_width, label=command,
                         color=colors[i % len(colors)])
            bars.append(bar)
            # 在每根柱子的正上方显示次数
            for rect in bar:
                height = rect.get_height()
                if height > 0:
                    ax.annotate(f'{height}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')
        ax.set_xlabel('日期')
        ax.set_ylabel('次数')
        ax.set_title('用户使用命令次数记录')
        ax.set_xticks([d + bar_width * (len(commands) / 2 - 0.5) for d in range(len(dates))])
        ax.set_xticklabels(dates)
        ax.legend()  # 添加每个柱子的命令解释
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ["SimHei"]
        # 将图像保存到内存中的字节流
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        # 将图像作为响应返回
        return Response(img.getvalue(), mimetype='image/png')
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询用户记录失败：{str(e)}'})
    finally:
        cursor.close()
        cnx.close()


if __name__ == '__main__':
    app.run(debug=False)
