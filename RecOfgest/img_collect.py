import os
import cv2 as cv

def get_image_count(label):
    folder = f"E:\\Python\\ML\\RecOfgest\\data\\gesture_data\\{label}"
    if not os.path.exists(folder):
        os.makedirs(folder)
    return len([name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))])

def save_image(img, label, count):
    path = f"E:\\Python\\ML\\RecOfgest\\data\\gesture_data\\{label}\\{count}.png"
    cv.imencode('.jpg', img)[1].tofile(path)
    print(f'正在保存{label}-roi图片, 本次图片编号: {count}')

if __name__ == "__main__":
    cap = cv.VideoCapture(0)  # 调用摄像头
    if not cap.isOpened():
        print("无法打开摄像头")
        exit()

    # 初始化各个手势和人脸图片的计数器
    m_0 = get_image_count('0')  # 手势0
    m_1 = get_image_count('1')  # 手势1
    m_2 = get_image_count('2')  # 手势2
    m_3 = get_image_count('3')  # 手势3
    m_4 = get_image_count('4')  # 手势4
    m_5 = get_image_count('5')  # 手势5
    m_f = get_image_count('face')  # 人脸（加个人脸标签用于避免将人脸错误识别）

    while True:
        success, frame = cap.read()  # 读取每一帧
        if not success:
            print("无法读取摄像头帧")
            break
        new_img = cv.flip(frame, 1)  # 翻转图像
        roi = new_img

        # YCrCb之Cr分量 + OTSU二值化（肤色检测）
        ycrcb = cv.cvtColor(roi, cv.COLOR_BGR2YCrCb)  # 把图像转换到YUV色域
        (y, cr, cb) = cv.split(ycrcb)  # 图像分割, 分别获取y, cr, cb通道图像

        # 高斯滤波, cr 是待滤波的源图像数据, (5,5)是窗口大小, 0 是指根据窗口大小来计算高斯函数标准差
        cr1 = cv.GaussianBlur(cr, (5, 5), 0)  # 对cr通道分量进行高斯滤波
        # 根据OTSU算法求图像阈值, 对图像进行二值化
        _, skin1 = cv.threshold(cr1, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        cv.imshow('skin1', skin1)  # 展示处理后的图片

        # 轮廓查找
        contours, hierarchy = cv.findContours(skin1, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        for item in contours:  # 遍历所有轮廓
            (x, y, w, h) = cv.boundingRect(item)  # 获得最小矩形框架
            if w >= 50 and h >= 50:  # 在较大的框架中查找
                img = skin1[y : y + h, x : x + w]  # 获得矩形轮廓图
                cv.imshow('img', img)  # 展示矩形轮廓图
                cv.rectangle(new_img, (x, y), (x + w, y + h), (255, 0, 0), 2)  # 在new_img中用矩形框出

        cv.imshow("frame", new_img)  # 展示new_img图像

        k = cv.waitKey(1) & 0xFF  # 等待键盘触发
        if k != 255:
            print(f"按键检测到: {chr(k)}")

        if k == ord(' '):  # 按下空格退出
            break
        elif k == ord('a'):  # 按A收集手势"0"图片
            save_image(img, '0', m_0)
            m_0 += 1
        elif k == ord('s'):  # 按S收集手势"1"图片
            save_image(img, '1', m_1)
            m_1 += 1
        elif k == ord('d'):  # 按D收集手势"2"图片
            save_image(img, '2', m_2)
            m_2 += 1
        elif k == ord('q'):  # 按Q收集手势"3"图片
            save_image(img, '3', m_3)
            m_3 += 1
        elif k == ord('w'):  # 按W收集手势"4"图片
            save_image(img, '4', m_4)
            m_4 += 1
        elif k == ord('e'):  # 按E收集手势"5"图片
            save_image(img, '5', m_5)
            m_5 += 1
        elif k == ord('f'):  # 按F收集人脸图片
            save_image(img, 'face', m_f)
            m_f += 1

    cap.release()  # 释放摄像头资源
    cv.destroyAllWindows()  # 释放opencv创建的所有窗口
