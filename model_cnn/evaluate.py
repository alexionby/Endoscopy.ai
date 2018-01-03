import os
import numpy as np

import cv2
import keras
from keras.models import Model

data_path = 'evals/'

image_rows = 192
image_cols = image_rows

results = []

tile_size = 96
tile_pad  = ( image_rows - tile_size ) // 2

for image_name in os.listdir('./evals'):

    if image_name.endswith('.jpg'):

        img = cv2.imread(os.path.join(data_path, image_name) , 0)
        img = img.astype('float32') / 255.
        
        mask = cv2.imread(os.path.join(data_path, image_name.split('.')[0] + '.tif') , 0)
        mask = mask.astype('float32') / 255.
                                       
        border_size = image_rows

        img_borded = cv2.copyMakeBorder(img, border_size , border_size, border_size, border_size, cv2.BORDER_REFLECT)
        mask_borded = cv2.copyMakeBorder(mask, border_size , border_size, border_size, border_size, cv2.BORDER_REFLECT)
                          
        num_h_blocks = img_borded.shape[0] // tile_size
        num_w_blocks = img_borded.shape[1] // tile_size

        data = np.zeros((num_h_blocks * num_w_blocks,image_rows,image_cols,1))
        y_data = data = np.zeros((num_h_blocks * num_w_blocks,image_rows,image_cols,1))

        for i in range(num_w_blocks - 1):

            for j in range(num_h_blocks - 1):

                k = i * num_h_blocks + j
                l = j * tile_size
                m = i * tile_size

                data[k,:,:,0] = img_borded[l:l+image_rows,m:m+image_cols]
                y_data[k,:,:,0] = mask_borded[l:l+image_rows,m:m+image_cols]

        print(data.shape)
        
        from train import get_unet

        model = get_unet(image_rows, image_cols)
        model.load_weights('weights.h5')
        result = model.evaluate(data, y_data, batch_size=4)
                          
        print(result)
        
        results.append(result)

    np.savetxt('evaluate.txt', np.array(results))