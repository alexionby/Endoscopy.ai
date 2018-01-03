import numpy as np
import cv2
import os

size = 96
step = size // 2

count = 0

os.mkdir('./raw/images')
os.mkdir('./raw/images/main')
os.mkdir('./raw/masks')
os.mkdir('./raw/masks/main')

os.mkdir('./raw/test_images')
os.mkdir('./raw/test_images/main')
os.mkdir('./raw/test_masks')
os.mkdir('./raw/test_masks/main')

print(os.listdir('.'))

for i in os.listdir('./raw/imgs'):

    print(i)

    if i.endswith('.jpg'):

        img = cv2.imread('raw/imgs/' + i, 0)
        mask = cv2.imread('raw/maps/' + i[:-4] + '.tif', 0)

        print(img.shape, mask.shape)

        size_h = img.shape[0] - img.shape[0] % size - 20
        size_w = img.shape[1] - img.shape[1] % size - 20

        print(size_h, size_w)

        for n in range(20, size_h, step):
            for m in range(20, size_w, step):

                local_img = img[ n:n+size, m:m+size ]
                ret, local_mask = cv2.threshold(mask[ n:n+size, m:m+size ], 127, 255, cv2.THRESH_BINARY)

                if cv2.countNonZero(local_mask) > 200 and local_img.shape == (size, size) :

                    #print(i, n*m + m )

                    cv2.imwrite('raw/images/main/' + i[:-4] + '_' + str(n*m + m) + '.jpg', local_img)
                    cv2.imwrite('raw/masks/main/' + i[:-4] + '_' + str(n*m + m) + '.jpg', local_mask)

                    count += 1

print('Done, count:' , count)

count = 0

for i in os.listdir('./raw/test_imgs'):

    print(i)

    if i.endswith('.jpg'):

        img = cv2.imread('raw/test_imgs/' + i, 0)
        mask = cv2.imread('raw/test_maps/' + i[:-4] + '.tif', 0)

        print(img.shape, mask.shape)

        size_h = img.shape[0] - img.shape[0] % size - 20
        size_w = img.shape[1] - img.shape[1] % size - 20

        print(size_h, size_w)

        for n in range(20, size_h, step):
            for m in range(20, size_w, step):

                local_img = img[ n:n+size, m:m+size ]
                ret, local_mask = cv2.threshold(mask[ n:n+size, m:m+size ], 127, 255, cv2.THRESH_BINARY)

                if cv2.countNonZero(local_mask) > 200 and local_img.shape == (size, size) :

                    #print(i, n*m + m )

                    cv2.imwrite('raw/test_images/main/' + i[:-4] + '_' + str(n*m + m) + '.jpg', local_img)
                    cv2.imwrite('raw/test_masks/main/' + i[:-4] + '_' + str(n*m + m) + '.jpg', local_mask)

                    count += 1

print('Done, count:' , count)
