import cv2
import numpy as np
import json
import time

from flask import jsonify

from parameters.skeleton_with_additions import zhangSuen, remove_staircases

global_params = {}

def count_params(src, step=8):

    bricks_count = 0

    img = np.copy(src)
    img = cv2.copyMakeBorder(img, step - img.shape[1]%step, 0, step - img.shape[0]%step, 0, cv2.BORDER_REFLECT)
    img = cv2.bitwise_not(img)

    #th2 = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
    #        cv2.THRESH_BINARY_INV,35,2)

    ret, th2 = cv2.threshold(img, 255-50, 255, cv2.THRESH_BINARY_INV)

    print(th2.shape)
    threshold = np.copy(th2[step - src.shape[1]%step:, step - src.shape[0]%step:])

    for i in range(0,img.shape[0],step):
        for j in range(0,img.shape[1],step):
            if cv2.countNonZero(th2[i:(i+step), j:(j+step)]) != 0:
                th2[i:(i+step), j:(j+step)] = 255
                bricks_count += 1

    result = th2[:src.shape[0], :src.shape[1]]

    area_under_brick = cv2.countNonZero(result)

    global_params['S'] = area_under_brick
    global_params['NonZero'] = cv2.countNonZero(threshold)

    return result, threshold, area_under_brick

def create_map(src, step=10):

    img = np.copy(src)
    dist_map = np.zeros(src.shape)

    counter = 0
    color = step

    while cv2.countNonZero(img) > 0:

        temp = np.copy(img)
        kernel = np.ones((3,3),np.uint8)
        img = cv2.erode(img, kernel, iterations = 1)

        temp = cv2.bitwise_or(temp,img)
        temp[ temp > 0 ] = color
        color += step

        dist_map += temp

        counter +=1

    return dist_map

def skeletonize(src):

    img = np.copy(src)
    img_shape = img.shape[::-1]

    print(1)

    img = cv2.pyrDown(img)
    img = cv2.pyrUp(img)

    print(2)

    img = cv2.resize(img,img_shape, interpolation = cv2.INTER_CUBIC)

    print(3)

    ret, img_b = cv2.threshold(img, 127,255, cv2.THRESH_BINARY)
    img_b = img_b / 255.0
    print('*' * 30)

    #img_b = boundary_smooth(img_b)
    #print('*' * 30)

    img_b = zhangSuen(img_b)
    print('*' * 30)

    img_b = remove_staircases(img_b)
    print('*' * 30)

    global_params['L'] = cv2.countNonZero(img_b)

    return np.uint8(img_b * 255)

def get_skeleton_map(skeleton, dist_map):

    print(skeleton.shape)
    print(dist_map.shape)

    return np.uint8(cv2.bitwise_and(dist_map,dist_map, mask=skeleton))


def extract_vessels(skeleton, binary_image, filename='vessels.json', step=10):

    img = np.copy(skeleton)
    thr = np.copy(binary_image)

    vess_img = np.zeros(img.shape, dtype=np.uint8)
    dots_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)

    #img = np.lib.pad(img, ((1,1),(1,1),(0,0)), 'constant')

    img[:,-1] = 0
    img[:,0] = 0
    img[0,:] = 0
    img[-1,:] = 0

    vess_dict = {}
    dots_dict = {}
    params_dict = {}
    radius_dict = {}

    m = 0
    branch_count = 0

    i,j = 1,1

    while i < img.shape[0] - 1:

        j = 1
        continue_i = False

        while j < img.shape[1] - 1:

            if cv2.countNonZero( img[i-1:i+2, j-1:j+2] ) == 2 and img[i,j] > 0 :

                points = [[int(i),int(j)]]
                points_value = [int(img[i,j] // step)]

                img[i,j] = 0

                k,n = np.nonzero(img[i-1:i+2, j-1:j+2])
                k = k[0] + i - 1
                n = n[0] + j - 1

                while cv2.countNonZero( img[ k-1:k+2, n-1:n+2] ) == 2:

                    points.append([int(k), int(n) ])
                    points_value.append( int( img[k,n] // step ) )

                    img[k,n] = 0
                    pad_k,pad_n = np.nonzero( img[k-1:k+2, n-1:n+2] )
                    k = pad_k[0] + k - 1
                    n = pad_n[0] + n - 1

                #img[k,n] = 0

                if cv2.countNonZero( img[ k-1:k+2, n-1:n+2] ) == 1:
                    img[k,n] = 0
                else:
                    img[k-1:k+2,n-1:n+2] = 0
                    dots_dict[branch_count] = [int(k),int(n)]
                    branch_count += 1

                if k < i or (k == i and n < j):
                    i,j = k,n

                if len(points) > 5:

                    temp = np.zeros(img.shape, dtype=np.uint8)
                    temp_points = np.array(points_value)
                    max_rad = np.max(temp_points)

                    for x,y in points:
                        cv2.circle(temp, (y,x), max_rad, 255, -1)

                    area = cv2.countNonZero( cv2.bitwise_and(thr,thr,mask=temp) )

                    params = [float(np.min(temp_points)), float(np.max(temp_points)), float(np.round(np.mean(temp_points), 2) ), float(np.round(np.std(temp_points),2) ) , float(area)]

                    params_dict[m] = params
                    vess_dict[m] = points
                    radius_dict[m] = points_value

                    m += 1

                img[i,j] = 0

                continue_i = True
                continue

            j += 1

        if continue_i:
            continue

        i += 1

    global_params['N'] = branch_count

    with open('dots.json', 'w') as fp:
        json.dump(dots_dict, fp)

    with open('vessels.json', 'w') as fp:
        json.dump(vess_dict, fp)

    with open('radius.json', 'w') as fp:
        json.dump(radius_dict, fp)

    with open('params.json', 'w') as fp:
        json.dump(params_dict, fp)

    return dots_dict, vess_dict, radius_dict, params_dict


import pandas as pd
import scipy
from scipy.signal import savgol_filter
from scipy.signal import argrelextrema

def eval_vessels(vessels):

    params_dict = {}
    harmonics_dict = {}

    for k in vessels:
        #print('Сосуд номер: ', k)
        arr = rotate(vessels[k])
        params, yhat = get_params(arr, index = k)

        harmonics = get_harmony(arr) #[:,:10]

        params_dict[k] = params
        harmonics_dict[k] = harmonics

    return params_dict, harmonics_dict


def rotate(pixels):
    pixels = np.array(pixels)
    pixels = (pixels - pixels[0])

    p1 = np.array( [ pixels[-1,0], 0 ] )
    p2 = pixels[-1]

    angle = -1 * np.sign(p2[1]) * np.arccos( np.dot(p1,p2) / np.sqrt( np.dot(p1,p1) * np.dot(p2,p2) ) )

    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, s], [-s, c]])

    return pixels.dot(R).T


def get_harmony(arr):

    w = scipy.fftpack.rfft(arr[1])
    f = scipy.fftpack.rfftfreq( len(arr[0]) , abs(arr[0,0] - arr[0,-1])/len(arr[0]))

    spectrum = w**2

    x_real = [f[0]]
    y_real = [spectrum[0]]

    for i,j in zip( f[2:-3:2], spectrum[2:-3:2] ) :

        x_real.append(i)
        y_real.append(j)

    x_real.append(f[-1])
    y_real.append(spectrum[-1])

    x_real = list(map( lambda x: float(np.nan_to_num(x)), x_real[:10]))
    y_real = list(map( lambda x: float(np.nan_to_num(x)), y_real[:10]))

    return [x_real, y_real]


def get_params(arr, index=0):

    yhat = savgol_filter(arr[1], 21, 3, mode='nearest')

    indexes = np.concatenate( (argrelextrema(yhat,np.less)[0] , argrelextrema(yhat, np.greater)[0] ) , axis=0 )

    np.trapz( np.absolute(yhat), dx=1.0, axis=-1)
    scipy.integrate.simps( np.absolute(yhat) )

    return {
            #'len': len(arr[0]),
            'bend_count': len(argrelextrema(yhat, np.less)[0]) + len(argrelextrema(yhat, np.greater)[0]),
            'area_under_curve': float( np.nan_to_num(scipy.integrate.simps( np.absolute(yhat) ) ) ),
            'mean_abs_peaks': float( np.nan_to_num( np.mean(np.abs( yhat[indexes])))),
            'max_amplitude': float( np.nan_to_num(np.max(yhat))),
            'min_amplitude': float( np.nan_to_num(np.min(yhat))),
            'std_amplitude': float( np.nan_to_num(np.std(np.abs(yhat)))),
            'mean_peaks': float( np.nan_to_num(np.mean( yhat[indexes] ))),
            'std_peaks': float( np.nan_to_num(np.std( yhat[indexes] ))),
             } , yhat

def postprocessing(img):

    print(img.shape, img.dtype)

    result = count_params(img)

    cv2.imwrite('skeleton.jpg', result[1])

    step = 2

    result_2 = create_map(result[1], step=step)

    cv2.imwrite('skeleton_map.jpg', result_2)

    start = time.time()

    print('start')
    result_3 = skeletonize(result[1])
    print('done')

    print(time.time() - start)

    print(result_3.shape)
    print(result_2.shape)

    result_4 = get_skeleton_map(result_3, result_2)

    print(result_4.dtype, result[1].dtype)

    dots_dict, vess_dict, radius_dict, params_dict = extract_vessels(result_4, result[1], step=step)

    global_params['lo'] = global_params['L']/global_params['S']
    global_params['B'] = global_params['N']/global_params['L']
    global_params['Si'] = global_params['lo']/global_params['B']

    with open('global_params.json', 'w') as fp:
        json.dump(global_params, fp)

    plot_params, frequency_params =  eval_vessels(vess_dict)

    return dots_dict, vess_dict, radius_dict, params_dict, global_params, plot_params, frequency_params
