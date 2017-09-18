import cv2
import numpy as np

from numba import jit, void

import sys
import time

@jit
def neighbours(x,y,img):
    "Return 8-neighbours of image point P1(x,y), in a clockwise order"
    x_1, y_1, x1, y1 = x-1, y-1, x+1, y+1
    return [ img[x_1][y], img[x_1][y1], img[x][y1], img[x1][y1],     # P2,P3,P4,P5
                img[x1][y], img[x1][y_1], img[x][y_1], img[x_1][y_1] ]    # P6,P7,P8,P9

@jit
def transitions(neighbours):
    "No. of 0,1 patterns (transitions from 0 to 1) in the ordered sequence"
    n = neighbours + neighbours[0:1]      # P2, P3, ... , P8, P9, P2
    neighbours_sum = 0

    for i in range(len(neighbours)):

        neighbours_sum += n[i+1] - n[i]*n[i+1]

    return neighbours_sum

"""
def transitions(neighbours):
    "No. of 0,1 patterns (transitions from 0 to 1) in the ordered sequence"
    n = neighbours + neighbours[0:1]      # P2, P3, ... , P8, P9, P2
    return sum( (n1, n2) == (0, 1) for n1, n2 in zip(n, n[1:]) )  # (P2,P3), (P3,P4), ... , (P8,P9), (P9,P2)
"""

def zhangSuen(image):
    "the Zhang-Suen Thinning Algorithm"
    Image_Thinned = image.copy()  # deepcopy to protect the original image
    changing1 = changing2 = 1        #  the points to be removed (set as 0)

    Image_Thinned[:,-1] = 0
    Image_Thinned[:,0] = 0
    Image_Thinned[0,:] = 0
    Image_Thinned[-1,:] = 0

    while changing1 or changing2:   #  iterates until no further changes occur in the image

        start = time.time()

        # Step 1
        changing1 = []
        rows, columns = Image_Thinned.shape               # x for rows, y for columns
        #for x in range(1, rows - 1):                     # No. of  rows
        #    for y in range(1, columns - 1):            # No. of columns
        nonzero = np.nonzero(Image_Thinned)

        for x,y in zip(nonzero[0], nonzero[1]):
            P2,P3,P4,P5,P6,P7,P8,P9 = n = neighbours(x, y, Image_Thinned)
            if (Image_Thinned[x][y] == 1  and    # Condition 0: Point P1 in the object regions
                2 <= sum(n) <= 6   and    # Condition 1: 2<= N(P1) <= 6
                transitions(n) == 1 and    # Condition 2: S(P1)=1
                P2 * P4 * P6 == 0  and    # Condition 3
                P4 * P6 * P8 == 0):         # Condition 4
                changing1.append((x,y))

        for x, y in changing1:
            Image_Thinned[x][y] = 0

        # Step 2
        changing2 = []
        #for x in range(1, rows - 1):
        #    for y in range(1, columns - 1):
        for x,y in zip(nonzero[0], nonzero[1]):
            P2,P3,P4,P5,P6,P7,P8,P9 = n = neighbours(x, y, Image_Thinned)
            if (Image_Thinned[x][y] == 1   and        # Condition 0
                2 <= sum(n) <= 6  and       # Condition 1
                transitions(n) == 1 and      # Condition 2
                P2 * P4 * P8 == 0 and       # Condition 3
                P2 * P6 * P8 == 0):            # Condition 4
                changing2.append((x,y))

        for x, y in changing2:
            Image_Thinned[x][y] = 0

        print('iteration', time.time() - start )
        cv2.imwrite('test.jpg', np.uint8(Image_Thinned * 255) )

    return Image_Thinned

def yokoi_connectivity(img, point):

    i,j = point

    N = []

    N.append(img[i, j + 1] != 0 )
    N.append(img[i - 1, j + 1] != 0 )
    N.append(img[i - 1, j] != 0 )
    N.append(img[i - 1, j - 1] != 0 )
    N.append(img[i, j - 1] != 0)
    N.append(img[i + 1, j - 1] != 0 )
    N.append(img[i + 1, j] != 0 )
    N.append(img[i + 1, j + 1] != 0 )

    ret = 0

    for n in range(1,8,2):

        n1 = (n + 1) % 8
        n2 = (n + 2) % 8

        ret += N[n] - N[n] * N[n1] * N[n2]

    return ret


def num_zero_pixel_neighbours(img, point):

    ret = 0
    i,j = point

    for i_it in range(i-1,i+2):
        for j_it in range(j-1, j+2):


            if i_it != i or j_it != j :

                if img[i_it, j_it] == 0 :

                    ret += 1

    return ret

def boundary_smooth(orig_img):

    img = np.copy(orig_img)

    points = []

    for i in range(1,img.shape[0] - 1):

        for j in range(1,img.shape[1] - 1):

            if img[i,j] == 0:

                if num_zero_pixel_neighbours(img, (i,j)) <= 2 and yokoi_connectivity(img, (i,j)) < 2 :
                    points.append((i,j))

    for i,j in points:

        img[i,j] = 1


    return img


def match(img, points, values):

    m = True

    for i in range(len(points)):

        if values[i] == 2:

            continue

        if values[i] != points[i]:

            return False

    return m


def match_templates(img, point, k):

    p1,p2 = point

    li = []

    for i in range(-2,3,1):

        for j in range(-2,3,1):

            li.append(img[p1 + i,p2 + j])


    #print(li)

    # 0 = zero
    # 1 = one
    # 2 = don't care


    # DOWN

    values = [    0, 0, 1, 0, 0,
                  0, 0, 1, 0, 0,
                  0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0,
                  2, 0, 0, 0, 2 ]

    if match(img, li, values):

        return True

    if k >= 2:

        values[1] = 1

        if match(img, li, values):

            return True

    if k >= 3:

        values[1] = 0
        values[3] = 1

        if match(img, li, values):

            return True

    if k >= 4:

        values[3] = 0
        values[1] = values[6] = 1

        if match(img, li, values):

            return True


    if k >= 5:

        values[1] = values[6] = 0
        values[3] = values[8] = 1

        if match(img, li, values):

            return True


    """
    if k >= 5:

        values[1] = 1
        values[2] = values[7] = 1
        values[6] = 0
        values[3] = 1

        #print(li, values)

        if match(img, li, values):

            return True
    """


    #UP

    values = [  2, 0, 0, 0, 2,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 1, 0, 0,
                0, 0, 1, 0, 0 ]

    if match(img, li, values):

        return True

    if k >= 2:

        values[21] = 1

        if match(img, li, values):

            return True

    if k >= 3:

        values[21] = 0
        values[23] = 1

        if match(img, li, values):

            return True

    if k >= 4:

        values[23] = 0
        values[16] = values[21] = 1

        if match(img, li, values):

            return True


    if k >= 5:

        values[16] = values[21] = 0
        values[18] = values[23] = 1

        if match(img, li, values):

            return True

    """
    if k >= 5:

        values[16] = 0
        values[21] = 1
        values[18] = 0
        values[22] = 1
        values[23] = 1
        values[17] = 1

        if match(img, li, values):

            return True
    """


    #LEFT


    values = [  0, 0, 0, 0, 2,
                0, 0, 0, 0, 0,
                1, 1, 0, 0, 0,
                0, 0, 0, 0, 0,
                0, 0, 0, 0, 2 ]

    if match(img, li, values):
        print(1)
        return True

    if k >= 2:

        values[5] = 1

        if match(img, li, values):

            return True

    if k >= 3:

        values[5] = 0
        values[15] = 1

        if match(img, li, values):

            return True

    if k >= 4:

        values[15] = 0
        values[5] = values[6] = 1

        if match(img, li, values):

            return True


    if k >= 5:

        values[5] = values[6] = 0
        values[15] = values[16] = 1

        if match(img, li, values):

            return True


    #RIGHT
    values = [  2, 0, 0, 0, 0, #3-4
                0, 0, 0, 0, 0, #8-9
                0, 0, 0, 1, 1, #13-14
                0, 0, 0, 0, 0, #18-19
                2, 0, 0, 0, 0 ] #23-24

    if match(img, li, values):

        return True

    if k >= 2:

        values[9] = 1

        if match(img, li, values):

            return True

    if k >= 3:

        values[9] = 0
        values[19] = 1

        if match(img, li, values):

            return True

    if k >= 4:

        values[19] = 0
        values[8] = values[9] = 1

        if match(img, li, values):

            return True


    if k >= 5:

        values[8] = values[9] = 0
        values[18] = values[19] = 1

        if match(img, li, values):

            return True



#Stentiford’s Acute Angle Emphasis

def acute_angle_emphasis(orig_img):

    img = np.copy(orig_img)

    for k in range(5, 0, -2):

        #print(k)

        points = []

        for i in range(2,img.shape[0] - 2):

            for j in range(2,img.shape[1] - 2):

                if img[i,j] == 0:

                    if match_templates(img, (i,j), k):

                        img[i,j] = 2

                        points.append((i,j))

            #print("{0} %".format(np.round(i/img.shape[0] * 100, 2)) , end='\r')

        if len(points) > 0 :

            for i,j in points:

                img[i,j] = 1
        else:
            break

    return img


def remove_staircases(orig_img):

    img = cv2.copyMakeBorder(orig_img, 1,1,1,1, cv2.BORDER_CONSTANT, 0)

    for k in range(2):

        points = []

        for i in range(1, img.shape[0] - 1) :

            for j in range(1, img.shape[1] - 1) :

                if not img[i,j] :
                    continue

                e = bool(   img[i + 1,j ])
                ne = bool(  img[i + 1, j - 1])
                n = bool(   img[i, j - 1])
                nw = bool(  img[i - 1, j - 1])
                w = bool(   img[i - 1, j ])
                sw = bool(  img[i - 1, j + 1])
                s = bool(   img[i, j + 1])
                se = bool(  img[i + 1, j + 1])

                #if i == 0 :

                if k == 0:

                    #print(e,ne,n,nw,w,sw,s,se)

                    if (n and
                                      ((e and not ne and not sw and (not w or not s)) or
                                       (w and not nw and not se and (not e or not s)))) :

                        points.append([i,j])

                else:

                    if (s and
		                         ((e and not se and not nw and (not w or not n)) or
		                          (w and not sw and not ne and (not e or not n)))) :

                        points.append([i,j])

        for i,j in points:

            img[i,j] = 0

    return img[1:-1,1:-1]

def find_k_connect_points(img, connections=4):

    points = np.copy(img)

    for i in range(1, img.shape[0] - 1) :

        for j in range(1, img.shape[1] - 1) :

            k = img[i-1:i+2, j - 1: j + 2]

            if cv2.countNonZero(k) >= connections and k[1,1] > 0 :

                cv2.circle(points,(j,i), 0, 0, -1)
