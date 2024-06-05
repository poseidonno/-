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

# 定义GPIO引脚

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
        isStart = 1


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
    # 接收客户端消息
    if ready[0]:
        # 有数据可读，接收数据
        data, addr = sock.recvfrom(1024)
        print(f'收到来自客户端 {addr} 的消息：{data.decode()}')
    else:
        # 没有数据可读，发生了超时
        print('接收数据超时')
        ready = select.select([sock], [], [], 1)
 



