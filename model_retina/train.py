import numpy as np
from keras.models import Model
from keras.layers import Input, concatenate, Conv2D, MaxPooling2D, UpSampling2D, Activation, Dropout
from keras.optimizers import Adam, SGD
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger
from keras.layers.normalization import BatchNormalization
from keras import backend as K
from keras.preprocessing.image import ImageDataGenerator

K.set_image_data_format('channels_last')  # TF dimension ordering in this code

img_rows = 96
img_cols = 96

def get_unet(img_rows=img_rows, img_cols=img_cols):

    inputs = Input((img_rows, img_cols, 1))


    conv1 = Conv2D(32, (3, 3), padding='same')(inputs)
    batch1 = BatchNormalization()(conv1)
    relu1 = Activation(activation='relu')(batch1)

    conv1 = Conv2D(32, (3, 3), padding='same')(relu1)
    batch1 = BatchNormalization()(conv1)
    relu1 = Activation(activation='relu')(batch1)

    pool1 = MaxPooling2D(pool_size=(2, 2))(relu1)

    conv2 = Conv2D(64, (3, 3), padding='same')(pool1)
    batch2 = BatchNormalization()(conv2)
    relu2 = Activation(activation='relu')(batch2)

    conv2 = Conv2D(64, (3, 3), padding='same')(relu2)
    batch2 = BatchNormalization()(conv2)
    relu2 = Activation(activation='relu')(batch2)

    pool2 = MaxPooling2D(pool_size=(2, 2))(relu2)

    conv3 = Conv2D(128, (3, 3), padding='same')(pool2)
    batch3 = BatchNormalization()(conv3)
    relu3 = Activation(activation='relu')(batch3)

    conv3 = Conv2D(128, (3, 3), padding='same')(relu3)
    batch3 = BatchNormalization()(conv3)
    relu3 = Activation(activation='relu')(batch3)

    pool3 = MaxPooling2D(pool_size=(2, 2))(relu3)

    conv4 = Conv2D(256, (3, 3), padding='same')(pool3)
    batch4 = BatchNormalization()(conv4)
    relu4 = Activation(activation='relu')(batch4)

    conv4 = Conv2D(256, (3, 3), padding='same')(relu4)
    batch4 = BatchNormalization()(conv4)
    relu4 = Activation(activation='relu')(batch4)

    pool4 = MaxPooling2D(pool_size=(2, 2))(relu4)

    conv5 = Conv2D(512, (3, 3), padding='same')(pool4)
    batch5 = BatchNormalization()(conv5)
    relu5 = Activation(activation='relu')(batch5)

    conv5 = Conv2D(512, (3, 3), padding='same')(relu5)
    batch5 = BatchNormalization()(conv5)
    relu5 = Activation(activation='relu')(batch5)

    up6 = concatenate([UpSampling2D(size=(2, 2))(relu5), relu4], axis=3)

    conv6 = Conv2D(256, (3, 3), padding='same')(up6)
    batch6 = BatchNormalization()(conv6)
    relu6 = Activation(activation='relu')(batch6)

    conv6 = Conv2D(256, (3, 3), padding='same')(relu6)
    batch6 = BatchNormalization()(conv6)
    relu6 = Activation(activation='relu')(batch6)

    up7 = concatenate([UpSampling2D(size=(2, 2))(relu6), relu3], axis=3)

    conv7 = Conv2D(128, (3, 3), padding='same')(up7)
    batch7 = BatchNormalization()(conv7)
    relu7 = Activation(activation='relu')(batch7)

    conv7 = Conv2D(128, (3, 3), padding='same')(relu7)
    batch7 = BatchNormalization()(conv7)
    relu7 = Activation(activation='relu')(batch7)

    up8 = concatenate([UpSampling2D(size=(2, 2))(relu7), relu2], axis=3)

    conv8 = Conv2D(64, (3, 3), padding='same')(up8)
    batch8 = BatchNormalization()(conv8)
    relu8 = Activation(activation='relu')(batch8)

    conv8 = Conv2D(64, (3, 3), padding='same')(relu8)
    batch8 = BatchNormalization()(conv8)
    relu8 = Activation(activation='relu')(batch8)

    up9 = concatenate([UpSampling2D(size=(2, 2))(relu8), relu1], axis=3)

    conv9 = Conv2D(32, (3, 3), padding='same')(up9)
    batch9 = BatchNormalization()(conv9)
    relu9 = Activation(activation='relu')(batch9)

    conv9 = Conv2D(32, (3, 3), padding='same')(relu9)
    batch9 = BatchNormalization()(conv9)
    relu9 = Activation(activation='relu')(batch9)

    conv10 = Conv2D(1, (1, 1))(relu9)
    sigmoid = Activation(activation='sigmoid')(conv10)

    model = Model(inputs=[inputs], outputs=[sigmoid])

    model.compile(optimizer=Adam(lr=0.01), loss='binary_crossentropy', metrics=['accuracy'])

    return model
