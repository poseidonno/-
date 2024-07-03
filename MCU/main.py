import socket
import network
from OLED_OUTPUT import chinese, OLED, getchinese_num
from rh_temp import getdht
from machine import Pin, PWM, UART
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

uart = UART(1, baudrate=115200, tx=32, rx=35)  # 语音模块

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

timer_mode = False
timer_set = False
timer_duration = 0
timer_start_time = 0

show_status = 0


def auto(value):  # 温度或者湿度
    if value <= threshold_low:
        motor_start(500)
    elif threshold_low < value <= threshold_high:
        motor_start(800)
    elif value > threshold_high:
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

def show_detail():
    show_status = 0
    OLED.fill(0)
    OLED.text('Temp: ' + str(tempAndRh[0]), 0, 0)
    OLED.text('Hum: ' + str(tempAndRh[1]), 0, 10)
    OLED.text('Low Thresh: ' + str(threshold_low), 0, 20)
    OLED.text('High Thresh: ' + str(threshold_high), 0, 30)
    if isAuto:
        OLED.text('Mode: Auto', 0, 40)
    else:
        OLED.text('Mode: Manual', 0, 40)
    if timer_set:
        remaining_time = timer_duration - (time.time() - timer_start_time)
        OLED.text(f'Timer: {int(remaining_time)}s', 0, 50)
    OLED.show()

def show_chinese():
    show_status = 1
    OLED.fill(0)
    chinese('温度', 16, 4)
    chinese(getchinese_num(str(tempAndRh[0])), 16, 32)
    chinese(getchinese_num(str(tempAndRh[1])), 80, 32)
    chinese('湿度', 80, 4)
    OLED.show()

def enter_timer_mode():
    global timer_mode, timer_set, timer_duration, timer_start_time

    timer_mode = True  # 确保进入定时模式
    OLED.fill(0)
    OLED.text('Timer Mode', 0, 0)
    OLED.text('Set duration in', 0, 10)
    OLED.text('seconds:', 0, 20)
    OLED.show()

    duration_str = ""

    while True:
        for i, row in enumerate(row_list):
            for temp in row_list:
                temp.value(0)
            row.value(1)
            time.sleep_ms(10)
            for j, col in enumerate(col_list):
                current_state = col.value()
                if current_state == 1 and last_state[i][j] == 0:
                    key = names[i][j]  # 读取按键值
                    if key == "D":
                        timer_mode = False
                        OLED.fill(0)
                        OLED.text('Timer Canceled', 0, 10)
                        OLED.show()
                        time.sleep(1)
                        OLED.fill(0)
                        return
                    elif key == "C":
                        if duration_str.isdigit():
                            timer_duration = int(duration_str)
                            timer_set = True
                            timer_start_time = time.time()
                            OLED.fill(0)
                            OLED.text(f'Timer Set:', 0, 10)
                            OLED.text(f'{timer_duration} seconds', 0, 20)
                            OLED.show()
                            time.sleep(2)
                            OLED.fill(0)
                            return
                    elif key == "A":
                        duration_str = duration_str[:-1]  # 删除最后一个字符
                        OLED.fill(0)
                        OLED.text('Timer Mode', 0, 0)
                        OLED.text('Set duration in', 0, 10)
                        OLED.text('seconds:', 0, 20)
                        OLED.text(duration_str, 0, 30)
                        OLED.show()
                    elif key == "B":
                        duration_str = ""  # 清空字符串
                        OLED.fill(0)
                        OLED.text('Timer Mode', 0, 0)
                        OLED.text('Set duration in', 0, 10)
                        OLED.text('seconds:', 0, 20)
                        OLED.text(duration_str, 0, 30)
                        OLED.show()
                    elif key.isdigit():
                        duration_str += key
                        OLED.fill(0)
                        OLED.text('Timer Mode', 0, 0)
                        OLED.text('Set duration in', 0, 10)
                        OLED.text('seconds:', 0, 20)
                        OLED.text(duration_str, 0, 30)
                        OLED.show()
                    last_state[i][j] = 1
                elif current_state == 0 and last_state[i][j] == 1:
                    last_state[i][j] = 0

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

HOST = '192.168.4.1'
PORT = 8888

# 创建UDP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
    for i, row in enumerate(row_list):
        for temp in row_list:
            temp.value(0)
        row.value(1)
        time.sleep_ms(10)
        for j, col in enumerate(col_list):
            current_state = col.value()
            if current_state == 1 and last_state[i][j] == 0:
                if names[i][j] == "1":
                    timer_mode = False
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.on()
                    motor_start(500)
                    print("风扇开始转动 -低")
                elif names[i][j] == "2":
                    timer_mode = False
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.on()
                    motor_start(800)
                    print("风扇开始转动 -中")
                elif names[i][j] == "5":
                    timer_mode = False
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.on()
                    motor_start(1023)
                    print("风扇开始转动 -高")
                elif names[i][j] == "A":
                    timer_mode = False
                    isAuto = True
                    power = Pin(2, Pin.OUT)
                    power.on()
                    print("温控启动")
                elif names[i][j] == "B":
                    timer_mode = False
                    isAuto = False
                    dire_fan = 1 - dire_fan
                    motor_start(800)
                    print("反转")
                elif names[i][j] == "4":
                    timer_mode = False
                    isAuto = False
                    power = Pin(2, Pin.OUT)
                    power.off()
                    motor_shutdown()
                    print("风扇关闭")
                elif names[i][j] == "*":
                    if show_status == 0:
                        show_status = 1
                        print("切换为中文显示")
                    else:
                        show_status = 0
                        print("切换为详情数据显示")

                elif names[i][j] == "C":
                    isAuto = False
                    enter_timer_mode()
                last_state[i][j] = 1
            elif current_state == 0 and last_state[i][j] == 1:
                last_state[i][j] = 0

        # 检查定时器

    if timer_set and (time.time() - timer_start_time >= timer_duration):
        motor_shutdown()
        OLED.fill(0)
        OLED.text('Timer Done', 0, 10)
        OLED.show()
        time.sleep(0.1)
        timer_set = False  # 确保自动模式不重新启动风扇
        timer_mode = False  # 确保定时模式正确重置
        isAuto = False  # 确保自动模式不重新启动风扇
        OLED.fill(0)
        
     #语音识别模块   
    asr_data = uart.read()
    if asr_data:
        print("ASR-收到的数据:",asr_data)
        if asr_data == b"open\r\n":
            timer_mode = False
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(800)
            print("asr-风扇打开")
        elif asr_data == b"close\r\n":
            timer_mode = False
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.off()
            motor_shutdown()
            print("asr-风扇关闭")
        elif asr_data == b"low\r\n":
            timer_mode = False
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(500)
            print("asr-风扇转速---低")
        elif asr_data == b"middle\r\n":
            timer_mode = False
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(800)
            print("asr-风扇转速---中")
        elif asr_data == b"high\r\n":
            timer_mode = False
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(1023)
            print("asr-风扇转速---高")
        elif asr_data == b"reversal\r\n":
            timer_mode = False
            isAuto = False
            dire_fan = 1 - dire_fan
            motor_start(800)
            print("asr-风扇反转")
        elif asr_data == b"open_temp\r\n":
            timer_mode = False
            isAuto = True
            power = Pin(2, Pin.OUT)
            power.on()
            print("asr-温控启动")
        elif asr_data == b"close_temp\r\n":
            timer_mode = False
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(800)
            print("asr-温控关闭")
            
    # 接收客户端消息
    if ready[0]:
        # 有数据可读，接收数据
        data, addr = sock.recvfrom(1024)
        print(f'收到来自客户端 {addr} 的消息：{data.decode()}')
        action = data.decode().split("-")[0]
        if action == "getmsg":
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(
                    threshold_high)).encode(),
                addr)
        if (action == "开"):
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(
                    threshold_high)).encode(),
                addr)
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.on()
            motor_start(int(data.decode().split("-")[1]))
        if (action == "关"):
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(
                    threshold_high)).encode(),
                addr)
            isAuto = False
            power = Pin(2, Pin.OUT)
            power.off()
            motor_shutdown()
        if (action == "温湿切换"):
            value_TempAndRh = int(data.decode().split("-")[1])
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(
                    threshold_high)).encode(),
                addr)

        if (action == "反转"):
            isAuto = False
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(
                    threshold_high)).encode(),
                addr)
            dire_fan = 1 - dire_fan
            motor_start(800)
        if (action == "setvalue"):
            isAuto = True
            sock.sendto(
                (str(tempAndRh[0]) + "-" + str(tempAndRh[1]) + "-" + str(threshold_low) + "-" + str(
                    threshold_high)).encode(),
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

    if isAuto:
        tempAndRh = getdht()
        if value_TempAndRh == 1:
            value = tempAndRh[0]
        else:
            value = tempAndRh[1]
        auto(value)
        print("温控运行中")

    # OLED 显示当前状态
    if show_status == 0:
       show_detail()
    else:
       show_chinese()








