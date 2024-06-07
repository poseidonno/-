from machine import Pin
import dht


def getdht():
    # 1. 创建dht11对象
    dht11 = dht.DHT11(Pin(14))

    # 2. 测量数据
    dht11.measure()

    # 3. 提取温度数据
    temperature = dht11.temperature()

    # 4. 提取湿度数据
    humidity = dht11.humidity()

    # 5. 输出结果
    print("当前室内的温度：%.2f, 湿度:%.2f" % (temperature, humidity))
    return (temperature, humidity)
#getdht()

