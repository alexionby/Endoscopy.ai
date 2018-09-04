from __future__ import print_function

import os
import numpy as np

from skimage.io import imsave, imread

data_path_images = 'raw/images/main'
data_path_masks = 'raw/masks/main'

image_rows = 96
image_cols = 96

def create_train_data():

    images = os.listdir(data_path_masks)
    total = len(images)

    imgs = np.ndarray((total, image_rows, image_cols), dtype=np.uint8)
    imgs_mask = np.ndarray((total, image_rows, image_cols), dtype=np.uint8)

    i = 0
    print('-'*30)
    print('Creating training images...')
    print('-'*30)
    for image_name in images:

        image_mask_name = image_name

        img = imread(os.path.join(data_path_images, image_name), as_grey=True)
        img_mask = imread(os.path.join(data_path_masks, image_mask_name), as_grey=True)

        img = np.array([img])
        img_mask = np.array([img_mask])

        imgs[i] = img
        imgs_mask[i] = img_mask

        if i % 100 == 0:
            print('Done: {0}/{1} images'.format(i, total))
        i += 1
    print('Loading done.')

    np.save('imgs_train.npy', imgs)
    np.save('imgs_mask_train.npy', imgs_mask)
    print('Saving to .npy files done.')

def load_train_data():
    imgs_train = np.load('imgs_train.npy')
    imgs_mask_train = np.load('imgs_mask_train.npy')
    return imgs_train, imgs_mask_train

if __name__ == '__main__':
    create_train_data()
