import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from tabulate import tabulate
from server import sendmsg
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


class FanControlPanel:
    def __init__(self):
        self.current_user = None
        self.total_users = []
        self.login_window = None
        self.root = None
        self.entry_username = None
        self.entry_password = None
        self.show_password_var = None
        self.low_ = 15
        self.high_ = 30
        self.nowwd = 0
        self.now_tmepRh = 0
        self.wors = ["温", "湿"]
        self.loc = 0

    def register_user(self, username, password):  # 用户注册
        try:
            cnx = db_pool.get_connection()
            cursor = cnx.cursor(prepared=True)
            cursor.execute("SELECT COUNT(*) FROM user WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result[0] > 0:
                messagebox.showerror("注册失败", "用户名已存在")
                return False
            insert_query = "INSERT INTO user (username, password) VALUES (%s, %s)"
            cursor.execute(insert_query, (username, password))
            cnx.commit()
            messagebox.showinfo("注册成功", "用户注册成功")
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    def validate_login(self, username, password):  # 用户登录
        try:
            cnx = db_pool.get_connection()
            cursor = cnx.cursor(prepared=True)
            cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                messagebox.showerror("登录失败", "用户名不存在")  # messagebox 弹出消息框
                return False, "用户名不存在"
            stored_password = result[0]
            if stored_password == password:
                return True, None
            else:
                return False, "密码错误"
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False, "数据库错误"
        finally:
            cursor.close()
            cnx.close()

    def login_clicked(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        success, message = self.validate_login(username, password)
        if success:
            self.current_user = UserRecords(username)
            self.login_window.destroy()
            self.show_main_window()
        else:
            if message == "用户名不存在":
                response = messagebox.askyesno("用户不存在", "用户不存在，是否注册新用户？")   # askyesno选择是否
                if response:
                    if self.register_user(username, password):
                        self.login_window.destroy()
                        self.current_user = UserRecords(username)
                        self.show_main_window()
            elif message == "密码错误":
                messagebox.showerror("登录失败", "密码错误，请重新输入")
            else:
                messagebox.showerror("登录失败", "发生未知错误，请稍后再试")

    def getmsg(self):   # 获取服务器信息
        strs = sendmsg("getmsg")
        if strs == "空":
            return
        self.nowwd = int(strs.split("-")[0])
        self.now_tmepRh = int(strs.split("-")[1])
        self.low_ = int(strs.split("-")[2])
        self.high_ = int(strs.split("-")[3])
        self.updatereg()
        self.updatenow()

    def updatereg(self):    # 更新阈值
        label3 = tk.Label(self.root, text="当前最低阈值为:" + str(self.low_))
        label3.place(x=0, y=0)
        label4 = tk.Label(self.root, text="当前最高阈值为:" + str(self.high_))
        label4.place(x=0, y=20)

    def updatenow(self):    # 更新温湿度
        label3 = tk.Label(self.root, text="当前温度为" + str(self.nowwd))
        label3.place(x=400, y=100)
        label4 = tk.Label(self.root, text="当前湿度为" + str(self.now_tmepRh))
        label4.place(x=400, y=150)

    def button_click_shift(self):   # 温湿切换
        self.loc = 1 - self.loc
        self.button6.config(text="开启" + self.wors[self.loc] + "控", command=self.begain_auto)
        self.button7.config(text="关闭" + self.wors[self.loc] + "控", command=self.button_click_off)
        self.label6.config(text="当前模式为:【" + self.wors[self.loc] + "】控")
        sendmsg("温湿切换" + "-" + str(self.loc))
        self.current_user.add_record("温湿切换")
        self.getmsg()

    def begain_auto(self):
        self.button_click_low_val(40)
        self.button_click_high_val(70)

    def button_click_low(self):
        sendmsg("开-500")
        self.current_user.add_record("低速")

    def button_click_cen(self):
        sendmsg("开-800")
        self.current_user.add_record("中速")

    def button_click_high(self):
        sendmsg("开-1023")
        self.current_user.add_record("高速")

    def button_click_off(self):
        sendmsg("关")
        self.current_user.add_record("关闭")

    def button_click_return(self):
        sendmsg("反转")
        self.current_user.add_record("反转")

    def button_click_low_val(self, val):
        self.low_ = val
        sendmsg("setvalue-0-" + str(val))
        self.updatereg()
        self.current_user.add_record(f"设置最低阈值为{val}")

    def button_click_high_val(self, val):
        self.high_ = val
        sendmsg("setvalue-1-" + str(val))
        self.updatereg()
        self.current_user.add_record(f"设置最高阈值为{val}")

    def toggle_password(self):  # 显示密码
        if self.show_password_var.get():
            self.entry_password.config(show='')
        else:
            self.entry_password.config(show='*')

    def show_main_window(self):  # 控制窗口
        self.root = tk.Tk()
        self.root.geometry("600x450")
        self.root.configure(bg='lightblue')
        self.root.title("风扇控制面板")
        self.root.resizable(False, False)
        self.label1 = tk.Label(self.root, text="风扇开关", font=("Arial", 12, "bold"))
        self.label1.place(x=50, y=50)
        self.button = tk.Button(self.root, text="  低速  ", command=self.button_click_low, bg="#FFB6C1")
        self.button.place(x=50, y=100)
        self.button1 = tk.Button(self.root, text="  中速  ", command=self.button_click_cen, bg="#FFB6C1")
        self.button1.place(x=50, y=150)
        self.button2 = tk.Button(self.root, text="  高速  ", command=self.button_click_high, bg="#FFB6C1")
        self.button2.place(x=50, y=200)
        self.button3 = tk.Button(self.root, text="  关  ", command=self.button_click_off, bg="#FFB6C1")
        self.button3.place(x=50, y=250)
        self.button3 = tk.Button(self.root, text="  反转  ", command=self.button_click_return, bg="#FFB6C1")
        self.button3.place(x=50, y=300)
        self.label2 = tk.Label(self.root, text="温湿控制", font=("Arial", 12, "bold"))
        self.label2.place(x=200, y=50)
        self.label6 = tk.Label(self.root, text="当前模式为:【" + self.wors[self.loc] + "】控", fg="#666666")
        self.label6.place(x=278, y=52)
        self.input_box = tk.Entry(self.root)
        self.input_box.place(x=200, y=100)
        self.button4 = tk.Button(self.root, text="设置最低温度阈值",
                                 command=lambda: self.button_click_low_val(int(self.input_box.get())), bg="peach puff")
        self.button4.place(x=200, y=150)
        self.input_box1 = tk.Entry(self.root)
        self.input_box1.place(x=200, y=200)
        self.button5 = tk.Button(self.root, text="设置最高温度阈值",
                                 command=lambda: self.button_click_high_val(int(self.input_box1.get())),
                                 bg="peach puff")
        self.button5.place(x=200, y=250)
        self.button6 = tk.Button(self.root, text="开启" + self.wors[self.loc] + "控", command=self.begain_auto,
                                 bg="light gray")
        self.button6.place(x=400, y=250)
        self.button7 = tk.Button(self.root, text="关闭" + self.wors[self.loc] + "控", command=self.button_click_off,
                                 bg="light gray")
        self.button7.place(x=400, y=300)
        self.label3_now = tk.Label(self.root, text="当前温度为:" + str(self.nowwd), font=("Arial", 10, "bold"))
        self.label3_now.place(x=400, y=100)
        self.label4_now = tk.Label(self.root, text="当前湿度为:" + str(self.now_tmepRh), font=("Arial", 10, "bold"))
        self.label4_now.place(x=400, y=150)
        self.button8 = tk.Button(self.root, text="切换温湿度控制", command=self.button_click_shift, bg="light gray")
        self.button8.place(x=400, y=200)
        self.button9 = tk.Button(self.root, text="获取信息", command=self.getmsg, bg="light gray")
        self.button9.place(x=500, y=200)
        self.label7 = tk.Label(self.root, text="控制面板", font=("Arial", 20, "bold"), fg="#FFC0CB")
        self.label7.place(x=220, y=0)
        self.updatereg()
        self.getmsg()
        self.root.mainloop()

    def show_login_window(self):
        self.login_window = tk.Tk()
        self.login_window.geometry("400x200")
        self.login_window.title("用户登录")
        label_username = tk.Label(self.login_window, text="用户名:")
        label_username.pack()
        self.entry_username = tk.Entry(self.login_window)
        self.entry_username.pack()
        label_password = tk.Label(self.login_window, text="密码:")
        label_password.pack()
        self.entry_password = tk.Entry(self.login_window, show="*")
        self.entry_password.pack()
        self.show_password_var = tk.BooleanVar()
        show_password_check = tk.Checkbutton(self.login_window, text="显示密码", variable=self.show_password_var,
                                             command=self.toggle_password)
        show_password_check.pack()
        button_login = tk.Button(self.login_window, text="登录", command=self.login_clicked)
        button_login.pack()
        self.login_window.mainloop()

    def output_user_operations(self):
        try:
            connection = db_pool.get_connection()
            cursor = connection.cursor()
            # 查询user_records表中的数据
            query = "SELECT username, command, time FROM user_records"
            cursor.execute(query)
            records = cursor.fetchall()

            if records:
                headers = ['Username', 'Command', 'Time']
                rows = [[record[0], record[1], record[2].strftime('%Y-%m-%d %H:%M:%S')] for record in records]
                table = tabulate(rows, headers=headers, tablefmt='grid', stralign='center')
                print(table)
            else:
                print("No records found.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()


if __name__ == '__main__':
    app = FanControlPanel()
    app.show_login_window()
    app.total_users.append(app.current_user)
    # 调用输出用户操作信息表格的方法
    app.output_user_operations()
