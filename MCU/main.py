import socket
import network

from OLED_OUTPUT import chinese, OLED, getchinese_num
from rh_temp import getdht
from machine import Pin, PWM
import time

p25 = Pin(25, Pin.OUT)
p26 = Pin(26, Pin.OUT)

isAuto = True
isStart = 0
threshold_low = 15
threshold_high = 30
dire_fan = 1
tempAndRh = [0, 0]
value_TempAndRh = 1  # 初始湿度
# 矩阵引脚
row1 = Pin(19, Pin.OUT)
row2 = Pin(18, Pin.OUT)
row3 = Pin(5, Pin.OUT)
row4 = Pin(17, Pin.OUT)
row_list = [row1, row2, row3, row4]

col1 = Pin(16, Pin.IN, Pin.PULL_DOWN)
col2 = Pin(4, Pin.IN, Pin.PULL_DOWN)
col3 = Pin(2, Pin.IN, Pin.PULL_DOWN)
col4 = Pin(15, Pin.IN, Pin.PULL_DOWN)
col_list = [col1, col2, col3, col4]

names = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

last_state = [[0 for j in range(4)] for i in range(4)]


# 定义GPIO引脚
# 控制1个电机
def auto(value):  # 温度或者湿度
    if (value <= threshold_low):
        motor_start(500)
    elif (value > threshold_low and value <= threshold_high):
        motor_start(800)
    elif (value > threshold_high):
        motor_start(1023)
    print("最高阈值" + str(threshold_high) + "最低阈值" + str(threshold_low))


def motor_shutdown():
    # 2个电机停止转动
    p25.value(0)
    p26.value(0)


def motor_start(num):
    ENA = PWM(Pin(33))
    ENA.duty(num)

    p25.value(1 - dire_fan)
    p26.value(dire_fan)


while isStart != 2:
    motor_shutdown()
    if isStart == 0:
        print("按下'*'启动风扇")
        OLED.text('      Press', 0, 10)
        OLED.text('        *', 0, 20)
        OLED.text('   To Continue', 0, 30)
        OLED.show()
        isStart = 1
    for i, row in enumerate(row_list):
        for temp in row_list:
            temp.value(0)
        row.value(1)
        time.sleep_ms(10)
        for j, col in enumerate(col_list):
            if col.value() == 1:
                if names[i][j] == "*":
                    print("风扇启动")
                    isStart = 2
                    OLED.fill(0)


ap = network.WLAN(network.MODE_11B)

ap.active(True)

ap.config(essid='my_esp32', password='12345678')

# ip_address = ap.ifconfig()[0]
# 设置服务器IP和端口
# HOST = ip_address
HOST = '192.168.4.1'
# HOST = '127.0.0.1'
PORT = 8888

# 创建UDP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 绑定服务器IP和端口

sock.bind((HOST, PORT))
print("绑定" + HOST + "PORT" + str(PORT))
print('UDP服务器已启动，等待客户端连接...')
sock.settimeout(2)
import select

# 监视套接字是否有数据可读
try:
    ready = select.select([sock], [], [], 1)
except:
    ready = select.select([sock], [], [], 1)

last_state = [[0 for j in range(4)] for i in range(4)]

while True:
    # 按键控制
    for i, row in enumerate(row_list):
        for temp in row_list:
            temp.value(0)
        row.value(1)
        time.sleep_ms(10)
        for j, col in enumerate(col_list):
            current_state = col.value()
            if current_state == 1 and last_state[i][j] == 0:
                if names[i][j] == "1":
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.on()
                    motor_start(500)
                    print("风扇开始转动 -低")
                if names[i][j] == "2":
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.on()
                    motor_start(800)
                    print("风扇开始转动 -中")
                if names[i][j] == "5":
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.on()
                    motor_start(1023)
                    print("风扇开始转动 -高")
                if names[i][j] == "A":
                    power = Pin(2, Pin.OUT)
                    power.on()
                    print("温控启动")
                if names[i][j] == "B":
                    isAuto = False
                    dire_fan = 1 - dire_fan
                    motor_start(800)
                    print("反转")
                if names[i][j] == "4":
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.off()
                    motor_shutdown()
                    print("风扇关闭")
                last_state[i][j] = 1
            elif current_state == 0 and last_state[i][j] == 1:
                last_state[i][j] = 0
    # 接收客户端消息
    if ready[0]:
        # 有数据可读，接收数据
        data, addr = sock.recvfrom(1024)
        print(f'收到来自客户端 {addr} 的消息：{data.decode()}')
        action = data.decode().split("-")[0]
        if action == "getmsg":
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(threshold_high)).encode(),
                addr)
        if (action == "开"):
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(threshold_high)).encode(),
                addr)
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(int(data.decode().split("-")[1]))
        if (action == "关"):
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(threshold_high)).encode(),
                addr)
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.off()
            motor_shutdown()
        if (action == "温湿切换"):
            value_TempAndRh = int(data.decode().split("-")[1])
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(threshold_high)).encode(),
                addr)

        if (action == "反转"):
            isAuto = False
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(threshold_high)).encode(),
                addr)
            dire_fan = 1 - dire_fan
            motor_start(800)
        if (action == "setvalue"):
            isAuto = True
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(threshold_high)).encode(),
                addr)
            if (data.decode().split("-")[1] == "1"):
                threshold_low = int(data.decode().split("-")[2])
            else:
                threshold_high = int(data.decode().split("-")[2])

        ready = select.select([sock], [], [], 1)
    else:
        # 没有数据可读，发生了超时
        print('接收数据超时')
        ready = select.select([sock], [], [], 1)
    print(getdht())

    chinese('温度', 16, 4)
    chinese(getchinese_num(str(tempAndRh[0])), 16, 32)
    chinese(getchinese_num(str(tempAndRh[1])), 80, 32)
    chinese('湿度', 80, 4)
    OLED.show()
    if isAuto:
        tempAndRh[0], tempAndRh[1] = getdht()
        auto(tempAndRh[value_TempAndRh])






