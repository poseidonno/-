# 呐喊
# 开发时间: 2024/7/3 下午8:42
import os
import mysql.connector
from mysql.connector import pooling

from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'user': os.getenv('DB_USERNAME', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'fun_server')
}

# 创建数据库连接池
db_pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                      pool_size=3,
                                      **DB_CONFIG)


class UserRecords:
    def __init__(self, username):
        self.username = username  # 用户的名称
        self.commands = []  # 用户使用的命令列表
        self.count = 0  # 用户使用的次数
        self.times = []  # 用户使用的时间列表

    def add_record(self, command):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取并格式化当前时间
        self.commands.append(command)  # 添加命令到命令列表
        self.count += 1  # 使用次数增加
        self.times.append(current_time)  # 添加时间到时间列表
        # 每插入一条记录就插入到数据库中去
        try:
            connection = db_pool.get_connection()
            cursor = connection.cursor()
            add_record_query = (
                "INSERT INTO user_records (username, command, time) "
                "VALUES (%s, %s, %s)"
            )
            record_data = (self.username, command, current_time)
            cursor.execute(add_record_query, record_data)
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()

    def get_record(self):
        records = {
            "username": self.username,
            "commands": self.commands,
            "count": self.count,
            "times": self.times
        }
        return records
