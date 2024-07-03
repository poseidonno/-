import numpy as np
import os
import cv2 as cv
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Flatten
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.utils import to_categorical
from keras import backend
from PIL import Image
backend.set_image_data_format('channels_first')

import tensorflow as tf


# 设置GPU内存动态增长
physical_devices = tf.config.list_physical_devices('GPU')
for device in physical_devices:
    tf.config.experimental.set_memory_growth(device, True)

# 设定随机种子
seed = 7
np.random.seed(seed)

# 读取图片，调整大小(100*100)，转为numpy数组
def pre_pic(picName):
    # 先打开传入的原始图片
    img = Image.open(picName)
    # 使用消除锯齿的方法resize图片
    reIm = img.resize((100,100), Image.LANCZOS)
    # 变成灰度图，转换成矩阵
    im_arr = np.array(reIm.convert("L"))
    return im_arr

# 用pre_pic函数将图片转为numpy数组，并将所有图片的数组合并为一个数组
def get_files(file_dir):
    flag = 0
    for file in os.listdir(file_dir):
        image_file_path = os.path.join(file_dir,file)
        if file == '0':  # 文件名为‘0’表示0
            temp = 0  # 设置标签temp=0
        elif file == '1':  # 文件名为‘1’表示1
            temp = 1  # 设置标签temp=1
        elif file == '2':  # 文件名为‘2’表示2
            temp = 2  # 设置标签temp=2
        elif file == '3':  # 文件名为‘3’表示3
            temp = 3  # 设置标签temp=3
        elif file == '4':  # 文件名为‘4’表示4
            temp = 4  # 设置标签temp=4
        elif file == '5':  # 文件名为‘5’表示5
            temp = 5  # 设置标签temp=5
        elif file == 'face':  # 文件名为‘face’表示人脸
            temp = 6  # 设置标签temp=6
        for image_name in os.listdir(image_file_path):
            image_name_path = os.path.join(image_file_path,image_name)
            img = pre_pic(image_name_path)  # 将图片通过pre_pic函数转为numpy数组，例如img.shape=(100，100)
            if flag == 0:  # 第一次处理
                X_image = img[np.newaxis,:]  # X_image.shape=(1,100,100)
                Y_image = np.array([temp])  # Y_image.shape=(1,)
                flag = 1
            else:  # 第n次处理(n!=1)
            	#将(n-1,100,100)与(1,100,100)合并为(n,100,100)
                X_image = np.vstack((X_image,img[np.newaxis,:]))
                #将(n-1,)与(1,)合并为(n,)
                Y_image = np.hstack((Y_image,np.array([temp])))

    return X_image,Y_image  # X_image为图片数据，Y_image为标签
# 创建、编译模型
def create_model():
    model = Sequential()
    model.add(Conv2D(filters=8, kernel_size=(3,3), strides=(1,1), padding='same', input_shape=(1,100,100), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Conv2D(filters=16, kernel_size=(3,3), strides=(1,1), padding='same', activation='relu'))
    model.add(Dropout(0.5))
    model.add(MaxPooling2D(pool_size=(4,4)))
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(Dense(7, activation='softmax'))  # 输出层，输出为7个类别

    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model


if __name__ == "__main__":
    filetrain = "E:\\Python\\ML\\RecOfgest\\data\\gesture_data"
    print('start')
    X_train, Y_train = get_files(filetrain)
    print(X_train.shape)
    print(Y_train.shape)

    # 修改数据格式
    X_train = X_train.reshape(X_train.shape[0], 1, 100, 100).astype('float32')

    # 格式化数据到0-1之前
    X_train = X_train / 255

    # one-hot编码
    Y_train = to_categorical(Y_train)

    # 创建、编译模型
    model = create_model()

    # 训练模型
    model.fit(X_train, Y_train, epochs=10, batch_size=32, verbose=2)

    # 保存模型
    model.save('my_model.h5')