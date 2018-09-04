#import cv2
from skimage.io import imsave
from skimage.util import pad, invert
from skimage.morphology import erosion, square
from skimage.draw import circle

import numpy as np
import json

#dev modules
#import time, cv2

from flask import jsonify

from parameters.skeleton_with_additions import zhangSuen, remove_staircases

import scipy
from scipy.signal import savgol_filter
from scipy.signal import argrelextrema
from scipy.ndimage.filters import gaussian_filter1d

global_params = {}

def area_under_brick(src, step=8):
    img = np.copy(src)
    img = pad(img, ((step - img.shape[0]%step, 0), (step - img.shape[1]%step, 0)), mode="reflect") ## possible axes error

    for i in range(0,img.shape[0],step):
        for j in range(0,img.shape[1],step):
            if np.count_nonzero(img[i:(i+step), j:(j+step)]) > 0:
                img[i:(i+step), j:(j+step)] = 255
    
    img = img[:src.shape[0], :src.shape[1]]
    return np.count_nonzero(img)


def count_params(src, step=8):

    bricks_count = 0
    w,h = src.shape

    img = np.copy(src)
    img = pad(img, ( (step - h % step, 0),(step - w % step, 0)), mode="reflect")
    img = np.bitwise_not(img)

    th2 = img.copy()
    th2[ th2 > 205 ] = 255
    th2[ th2 <= 205] = 0
    th2 = invert(th2)

    threshold = np.copy(th2[step - h % step:, step - w % step:])

    for i in range(0,w,step):
        for j in range(0,h,step):
            if np.count_nonzero(th2[i:(i+step), j:(j+step)]) != 0:
                th2[i:(i+step), j:(j+step)] = 255
                bricks_count += 1

    result = th2[:w, :h]
    area_under_brick = np.count_nonzero(result)

    global_params['S'] = area_under_brick
    global_params['NonZero'] = np.count_nonzero(threshold)

    return result, threshold, area_under_brick

def create_map(src, step=10):

    img = np.copy(src)
    dist_map = np.zeros(src.shape)

    color = step
    kernel = square(3)

    while np.count_nonzero(img) > 0:

        temp = np.copy(img)
        img = erosion(img, kernel)
        temp = np.bitwise_or(temp, img)
        dist_map[temp > 0] = color
        color += step

    return np.uint8(dist_map)

def skeletonize(src):

    img = np.copy(src)
    img[ img <= 127] = 0
    img[ img > 127 ] = 1

    img = zhangSuen(img.astype(np.float))
    img = remove_staircases(img)

    global_params['L'] = np.count_nonzero(img)
    return np.uint8(img * 255)


def get_skeleton_map(skeleton, dist_map):
    return np.bitwise_and(dist_map, skeleton)


def extract_vessels(skeleton, binary_image, filename='vessels.json', step=10):

    print(skeleton.shape, binary_image.shape)

    img = np.copy(skeleton)
    thr = np.copy(binary_image)

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

    print("Before loop")

    while i < img.shape[0] - 1:

        j = 1
        continue_i = False

        while j < img.shape[1] - 1:

            if np.count_nonzero( img[i-1:i+2, j-1:j+2] ) == 2 and img[i,j] > 0 :

                points = [[int(i),int(j)]]
                points_value = [int(img[i,j] // step)]

                img[i,j] = 0

                k,n = np.nonzero(img[i-1:i+2, j-1:j+2])
                k = k[0] + i - 1
                n = n[0] + j - 1

                while np.count_nonzero( img[ k-1:k+2, n-1:n+2] ) == 2:

                    points.append([int(k), int(n) ])
                    points_value.append( int( img[k,n] // step ) )

                    img[k,n] = 0
                    pad_k,pad_n = np.nonzero( img[k-1:k+2, n-1:n+2] )
                    k = pad_k[0] + k - 1
                    n = pad_n[0] + n - 1

                if np.count_nonzero( img[ k-1:k+2, n-1:n+2] ) == 1:
                    img[k,n] = 0
                else:
                    img[k-1:k+2,n-1:n+2] = 0
                    dots_dict[branch_count] = [int(k),int(n)]
                    branch_count += 1

                if k < i or (k == i and n < j):
                    i,j = 0,0

                if len(points) > 5:

                    temp = np.zeros(img.shape, dtype=np.uint8)
                    temp_points = np.array(points_value)
                    max_rad = np.max(temp_points)

                    for x,y in points:
                        rr, cc = circle(x, y, max_rad + 1, shape=temp.shape)
                        temp[rr, cc] = 255 

                    area = np.count_nonzero( np.bitwise_and(thr, thr, where=temp.astype(np.bool)))

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

    print("After loop")

    global_params['N'] = branch_count

    """
    with open('dots.json', 'w') as fp:
        json.dump(dots_dict, fp)

    with open('vessels.json', 'w') as fp:
        json.dump(vess_dict, fp)

    with open('radius.json', 'w') as fp:
        json.dump(radius_dict, fp)

    with open('params.json', 'w') as fp:
        json.dump(params_dict, fp)
    """

    return dots_dict, vess_dict, radius_dict, params_dict


def eval_vessel(vessel, index=None):

    arr = rotate(vessel)
    rotated_arr = arr.copy()

    params,yhat = get_params(arr)
    harmonics = get_harmony(arr)

    # reopen in case of debug
    """

    if index:
        with open('debug/' + str(index) + '.txt', 'w') as outfile:
            json.dump(vessel, outfile)
            json.dump("~", outfile)
            json.dump(rotated_arr.tolist() , outfile)
            json.dump("~", outfile)
            json.dump(params, outfile)
            json.dump("~", outfile)
            json.dump(yhat.tolist() , outfile)
    """

    return params, harmonics

def eval_vessels(vessels):

    params_dict = {}
    harmonics_dict = {}

    for k in vessels:
        params, harmonics = eval_vessel(vessels[k], k)
        params_dict[k] = params
        harmonics_dict[k] = harmonics

    return params_dict, harmonics_dict


def rotate(pixels):
    pixels = np.array(pixels)
    pixels = (pixels - pixels[0])

    p1 = np.array( [ pixels[-1,0], 0 ] )
    p2 = pixels[-1]

    try:
        angle = -1 * np.sign(p2[0]) * np.sign(p2[1]) * np.arccos( float(np.dot(p1,p2)) / pow( float(np.dot(p1,p1)) * float(np.dot(p2,p2)) , 0.5 ) )
    except ZeroDivisionError:
        angle = -1 * np.sign(p2[0]) * np.sign(p2[1]) * np.arccos( float(np.dot(p1,p2)) / 1e-6 )
    print("alt_angle: ", angle)

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


def get_params(arr, rotation_number=3):

    yhat = arr[1].copy()

    max_indexes = []
    for angle in np.arange(-0.05 * rotation_number, 0.05 * (rotation_number+1), 0.05):
        c, s = np.cos(angle), np.sin(angle)
        R = np.array([[c, s], [-s, c]])
        rotated_vessel = arr.T.dot(R).T
        rotated_y = savgol_filter(rotated_vessel[1], 21, 3, mode='nearest')
        rotated_y = gaussian_filter1d(rotated_y, 1)
        peaks = np.concatenate( (argrelextrema(rotated_y,np.less)[0] , argrelextrema(rotated_y, np.greater)[0] ) , axis=0 )
        max_indexes.append(len(peaks))
        #if len(peaks) > max_indexes:
        #    max_indexes = len(peaks)

    print(max_indexes)
    max_indexes = max(max_indexes)

    yhat = savgol_filter(yhat, 21, 3, mode='nearest')
    yhat = gaussian_filter1d(yhat, 1)
    indexes = np.concatenate( (argrelextrema(yhat,np.less)[0] , argrelextrema(yhat, np.greater)[0] ) , axis=0 )
    np.trapz( np.absolute(yhat), dx=1.0, axis=-1)
    scipy.integrate.simps( np.absolute(yhat) )

    return {
            #'len': len(arr[0]),
            #'bend_count': len(argrelextrema(yhat, np.less)[0]) + len(argrelextrema(yhat, np.greater)[0]),
            'bend_count': max_indexes,
            'area_under_curve': float( np.nan_to_num(scipy.integrate.simps( np.absolute(yhat) ) ) ),
            'mean_abs_peaks': float( np.nan_to_num( np.mean(np.abs( yhat[indexes])))),
            'max_amplitude': float( np.nan_to_num(np.max(yhat))),
            'min_amplitude': float( np.nan_to_num(np.min(yhat))),
            'std_amplitude': float( np.nan_to_num(np.std(np.abs(yhat)))),
            'mean_peaks': float( np.nan_to_num(np.mean( yhat[indexes] ))),
            'std_peaks': float( np.nan_to_num(np.std( yhat[indexes] ))),
             } , yhat

def postprocessing(img):

    result_1 = count_params(img)
    result_2 = create_map(result_1[1], step=10)
    result_3 = skeletonize(result_1[1])
    result_4 = get_skeleton_map(result_2.copy(), result_3.copy())

    """
    if True:
        imsave('segmented.jpg', result_1[1])
        imsave('map.jpg', result_2)
        imsave('skeleton.jpg', result_3)
        imsave('skeleton_map.jpg', result_4)
    """

    dots_dict, vess_dict, radius_dict, params_dict = extract_vessels(result_4, result_1[1], step=10)

    global_params['S'] = area_under_brick(result_3.copy())

    try:
        global_params['lo'] = global_params['L']/global_params['S']
    except ZeroDivisionError:
        global_params['lo'] = global_params['L']/1e-6

    try:
        global_params['B'] = global_params['N']/global_params['L']
    except ZeroDivisionError:
        global_params['B'] = global_params['N']/1e-6

    try:
        global_params['Si'] = global_params['lo']/global_params['B']
    except ZeroDivisionError:
        global_params['Si'] = global_params['lo']/1e-6

    """
    with open('global_params.json', 'w') as fp:
        json.dump(global_params, fp)
    """

    plot_params, frequency_params =  eval_vessels(vess_dict)

    return dots_dict, vess_dict, radius_dict, params_dict, global_params, plot_params, frequency_params
