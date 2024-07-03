import numpy as np
import cv2 as cv
from keras.models import load_model
from PIL import Image
import os
import sys
import io
import tensorflow as tf
import contextlib
from server import sendmsg

# 设置 TensorFlow 日志级别
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 将 TensorFlow 日志级别设置为只输出错误信息
tf.get_logger().setLevel('ERROR')

# 确保 TensorFlow 动态分配 GPU 内存
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

model = load_model('my_model.h5')

# 读取图片, 调整大小(100*100), 转为numpy数组
def pre_pic(picName):
    img = Image.open(picName)
    reIm = img.resize((100, 100), Image.LANCZOS)
    im_arr = np.array(reIm.convert("L"))
    return im_arr

# 封装的识别函数
def run_recognition():
    cap = cv.VideoCapture(0)  # 调用摄像头
    filename = '00.jpg'
    count = 0
    predictions_list = []

    while True:
        success, frame = cap.read()  # 读取每一帧
        if not success:
            break

        new_img = cv.flip(frame, 1)  # 翻转
        roi = new_img

        # YCrCb之Cr分量 + OTSU二值化（肤色检测）
        ycrcb = cv.cvtColor(roi, cv.COLOR_BGR2YCrCb)  # 把图像转换到YUV色域
        (y, cr, cb) = cv.split(ycrcb)  # 图像分割, 分别获取y, cr, br通道图像

        # 高斯滤波, cr 是待滤波的源图像数据, (5,5)是值窗口大小, 0 是指根据窗口大小来计算高斯函数标准差
        cr1 = cv.GaussianBlur(cr, (5, 5), 0)  # 对cr通道分量进行高斯滤波
        # 根据OTSU算法求图像阈值, 对图像进行二值化
        _, skin1 = cv.threshold(cr1, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        cv.imshow('skin', skin1)  # 展示处理后的图片

        # 轮廓查找
        contours, hierarchy = cv.findContours(skin1, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)  # 轮廓查找
        for item in contours:
            (x, y, w, h) = cv.boundingRect(item)  # 获得最小矩形框架
            if w >= 50 and h >= 50:  # 在较大的框架中查找
                img = skin1[y: y + h, x: x + w]  # 获得矩形轮廓图
                cv.imshow('img', img)  # 展示矩形轮廓图
                cv.imwrite(filename, img)  # 将矩形轮廓图保存
                img = pre_pic(filename)
                img = img.reshape(1, 1, 100, 100).astype('float32')  # 修改数据格式
                img = img / 255  # 归一化

                with contextlib.redirect_stdout(io.StringIO()):  # 捕获预测输出
                    predictions = np.argmax(model.predict(img), axis=-1)  # 预测结果
                    flag = model.predict(img)  # 预测概率

                if max(flag[0]) > 0.5:  # 概率大于0.5才框出
                    if predictions[0] != 6:  # 排除预测值为 6 的情况
                        predictions_list.append(predictions[0])
                        count += 1
                        if count == 15:
                            most_common_prediction = max(set(predictions_list), key=predictions_list.count)
                            # output_prediction = str(most_common_prediction)
                            # sendmsg(output_prediction)  #传输给esp32
                            print(f"确定识别值: {most_common_prediction}")
                            count = 0
                            predictions_list = []

                    # 定义识别标签
                    if predictions[0] == 0:
                        s = "zero"
                    elif predictions[0] == 1:
                        s = "one"
                    elif predictions[0] == 2:
                        s = "two"
                    elif predictions[0] == 3:
                        s = "three"
                    elif predictions[0] == 4:
                        s = "four"
                    elif predictions[0] == 5:
                        s = "five"
                    else:
                        s = None  # 如果预测值为6，跳过显示

                    # 如果识别标签不为空，显示矩形框和标签
                    if s is not None:
                        cv.rectangle(new_img, (x, y), (x + w, y + h), (255, 0, 0), 2)  # 用矩形框出
                        cv.putText(new_img, s, (x, y), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2, 8)  # 在矩形上方显示文字

        cv.imshow('image', new_img)
        Key = cv.waitKey(1)
        if Key == ord(' '):  # 按下空格键退出
            break

    cap.release()  # 释放占用资源
    cv.destroyAllWindows()  # 释放opencv创建的所有窗口


# 主程序
if __name__ == '__main__':
    run_recognition()
