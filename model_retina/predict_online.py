import os
import numpy as np

import cv2
import keras
from keras.models import Model

from model_retina.train import get_unet

image_rows = 192
image_cols = image_rows

batch_size = 64

tile_size = 96
tile_pad  = ( image_rows - tile_size ) // 2

def make_prediction(image_name=None, img=None, weights='DRIVE.h5'):

    if image_name is not None:
        if image_name.endswith('.png') or image_name.endswith('.PNG') :
            img = cv2.imread(os.path.join(data_path, image_name) , 0)
        else:
            return

    elif img is not None:
        img = img
    else:
        return

    img = img.astype('float32') / 255.

    border_size = image_rows

    img_borded = cv2.copyMakeBorder(img, border_size , border_size, border_size, border_size, cv2.BORDER_REFLECT)

    num_h_blocks = img_borded.shape[0] // tile_size
    num_w_blocks = img_borded.shape[1] // tile_size

    data = np.zeros((num_h_blocks * num_w_blocks,image_rows,image_cols,1))

    for i in range(num_w_blocks - 1):

        for j in range(num_h_blocks - 1):

            k = i * num_h_blocks + j
            l = j * tile_size
            m = i * tile_size

            data[k,:,:,0] = img_borded[l:l+image_rows,m:m+image_cols]

    print(data.shape)

    model = get_unet(image_rows, image_cols)
    model.load_weights('model_retina/' + weights)

    result = model.predict(data,batch_size=batch_size,verbose=1)

    res = np.zeros(img_borded.shape, dtype=np.uint8)

    for i in range(num_w_blocks - 1):

        for j in range(num_h_blocks - 1):

            k = i * num_h_blocks + j
            l = j * tile_size
            m = i * tile_size

            block = result[k,:,:,0]
            block = np.uint8(block * 255)

            res[l + tile_pad : l+image_rows - tile_pad, m + tile_pad : m+image_cols - tile_pad] = block[ tile_pad:-tile_pad,  tile_pad:-tile_pad]

    res = res[image_rows:res.shape[0]-image_rows, image_cols:res.shape[1] - image_rows]
    return res

#cv2.imwrite('res_' + image_name[:-4] + '.tif', res)
