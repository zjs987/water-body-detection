from tensorflow.keras.initializers import RandomNormal
from tensorflow.keras.layers import *
from tensorflow.keras.models import *

from nets.vgg16 import VGG16
from nets.resnet50 import ResNet50

#这段代码定义了一个 U-Net 模型，用于图像分割。U-Net 模型由下采样和上采样两个部分组成，中间连接的是对应尺寸的特征层。
# 这里的 backbone 可以选择 VGG16 或者 ResNet50。  在代码中，首先根据输入的参数选择不同的 backbone，
# 获取其输出的五个有效特征层 feat1, feat2, feat3, feat4, feat5。然后使用 up-sampling 和 skip-connection 的方式，
# 将这几个特征层进行组合，并对每个组合结果进行卷积操作，最终输出一个二分类的分割结果。
# 其中 channels = [64, 128, 256, 512] 定义了每一层的通道数，P1~P5_up 是各层的变量名，Concatenate(axis=3)
# 表示在通道维度上进行拼接，Conv2D 函数表示卷积操作，UpSampling2D 表示上采样操作，Activation 表示激活函数，
# Model 表示模型输入和输出的关系。
def Unet(input_shape=(256,256,3), num_classes=3, backbone = "vgg"):
    inputs = Input(input_shape)
    #-------------------------------#
    #   获得五个有效特征层
    #   feat1   512,512,64
    #   feat2   256,256,128
    #   feat3   128,128,256
    #   feat4   64,64,512
    #   feat5   32,32,512
    #-------------------------------#
    if backbone == "vgg":
        feat1, feat2, feat3, feat4, feat5 = VGG16(inputs) 
    elif backbone == "resnet50":
        feat1, feat2, feat3, feat4, feat5 = ResNet50(inputs) 
    else:
        raise ValueError('Unsupported backbone - `{}`, Use vgg, resnet50.'.format(backbone))
      
    channels = [64, 128, 256, 512]

    # 32, 32, 512 -> 64, 64, 512
    P5_up = UpSampling2D(size=(2, 2))(feat5)
    # 64, 64, 512 + 64, 64, 512 -> 64, 64, 1024
    P4 = Concatenate(axis=3)([feat4, P5_up])
    # 64, 64, 1024 -> 64, 64, 512
    P4 = Conv2D(channels[3], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P4)
    P4 = Conv2D(channels[3], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P4)

    # 64, 64, 512 -> 128, 128, 512
    P4_up = UpSampling2D(size=(2, 2))(P4)
    # 128, 128, 256 + 128, 128, 512 -> 128, 128, 768
    P3 = Concatenate(axis=3)([feat3, P4_up])
    # 128, 128, 768 -> 128, 128, 256
    P3 = Conv2D(channels[2], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P3)
    P3 = Conv2D(channels[2], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P3)

    # 128, 128, 256 -> 256, 256, 256
    P3_up = UpSampling2D(size=(2, 2))(P3)
    # 256, 256, 256 + 256, 256, 128 -> 256, 256, 384
    P2 = Concatenate(axis=3)([feat2, P3_up])
    # 256, 256, 384 -> 256, 256, 128
    P2 = Conv2D(channels[1], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P2)
    P2 = Conv2D(channels[1], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P2)

    # 256, 256, 128 -> 512, 512, 128
    P2_up = UpSampling2D(size=(2, 2))(P2)
    # 512, 512, 128 + 512, 512, 64 -> 512, 512, 192
    P1 = Concatenate(axis=3)([feat1, P2_up])
    # 512, 512, 192 -> 512, 512, 64
    P1 = Conv2D(channels[0], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P1)
    P1 = Conv2D(channels[0], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(P1)

    if backbone == "vgg":
        # 512, 512, 64 -> 512, 512, num_classes
        P1 = Conv2D(num_classes, 1, activation="softmax")(P1)
    elif backbone == "resnet50":
        ResNet50_up = UpSampling2D(size=(2, 2))(P1)
        # 512, 512, 192 -> 512, 512, 64
        ResNet50_up = Conv2D(channels[0], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(ResNet50_up)
        ResNet50_up = Conv2D(channels[0], 3, activation='relu', padding='same', kernel_initializer = RandomNormal(stddev=0.02))(ResNet50_up)

        P1 = Conv2D(num_classes, 1, activation="softmax")(ResNet50_up)
    else:
        raise ValueError('Unsupported backbone - `{}`, Use vgg, resnet50.'.format(backbone))
        
    model = Model(inputs=inputs, outputs=P1)
    return model
