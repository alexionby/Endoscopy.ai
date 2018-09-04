import json
import numpy as np
import matplotlib.pyplot as plt

import scipy
from scipy.signal import savgol_filter
from scipy.signal import argrelextrema
from scipy.ndimage.filters import gaussian_filter1d


vessel_id = 225

def rotate(pixels):
    pixels = np.array(pixels)
    pixels = (pixels - pixels[0])
    #print(pixels)

    p1 = np.array( [ pixels[-1,0], 0 ] )
    p2 = pixels[-1]

    print(p1, p2)

    angle = -1 * np.sign(p2[1]) * np.sign(p2[0]) * np.arccos( np.dot(p1,p2) / np.sqrt( np.dot(p1,p1) * np.dot(p2,p2) ) )
    angle = angle #+ 0.1

    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, s], [-s, c]])

    return pixels.dot(R).T

with open("debug/{}.txt".format(vessel_id)) as f:
    data = f.readline().split("\"~\"")
    orig_vessel = json.loads(data[0])
    orig_vessel = np.array(orig_vessel)

    print(orig_vessel[:5], orig_vessel[-5:])

    y_ = json.loads(data[1])
    params = json.loads(data[2])
    x_ = json.loads(data[3])

plt.plot(orig_vessel[:,1], orig_vessel[:, 0] * (-1))
plt.show()

print(orig_vessel.shape)
rotated_vessel = rotate(orig_vessel)

angle = -0.1
c, s = np.cos(angle), np.sin(angle)
R = np.array([[c, s], [-s, c]])
rotated_vessel = rotated_vessel.T.dot(R).T

print(rotated_vessel.shape)

plt.plot(rotated_vessel[0], rotated_vessel[1])
plt.show()

yhat = savgol_filter(rotated_vessel[1], 21, 3, mode='nearest')

plt.plot(rotated_vessel[0], yhat)
plt.show()

yhat = gaussian_filter1d(yhat, 1)

indexes = len(np.concatenate( (argrelextrema(yhat,np.less)[0] , argrelextrema(yhat, np.greater)[0] ) , axis=0 ))

print(indexes)

plt.plot(rotated_vessel[0], yhat)
plt.show()