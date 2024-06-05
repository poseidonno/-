import socket

import select

#import GetIP


def sendmsg(message):
    # 设置服务器IP和端口
    PORT = 8888
    HOST = "192.168.4.1"
    # HOST="127.0.0.1"
    #print(GetIP.get_wifi_ip_address())#通过wifi获取ESP32的ip地址
    # 创建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode(), (HOST, PORT))
    # 接收服务器响应消息
    ready = select.select([sock], [], [], 1)
    if ready[0]:
        #print(sock.recvfrom(1024))
        data, addr = sock.recvfrom(1024)
        return data.decode()
    else:
        print("超时")
    sock.close()
    return "空"
if __name__ == '__main__':
    sendmsg("开");