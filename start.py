from flask import Flask, render_template, url_for, request
from flask import jsonify, send_from_directory, make_response
from flask import flash
from werkzeug.utils import secure_filename

import os
import cv2
import numpy as np
import random
import time

import json

from model_retina.predict_online import make_prediction
from parameters.eval_parameters import postprocessing, eval_vessels

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'well_known_secret'

@app.route('/')
def index():
    return render_template('index.html')

"""@app.route('/static/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename, as_attachment=True)"""

@app.route('/main')
def main():

    resp = make_response(render_template('main.html'))
    #uniq_name = str(round(time.time() ))
    #resp.set_cookie('filename', uniq_name)

    return resp

from scipy.spatial import distance

@app.route('/merge', methods = ['POST'])
def merge():

    #print( request.form )
    #print( request.form['vess_a'] )

    #print(json.loads( request.form['vess_a'] ))

    index = request.form['index']

    print(index)

    vess_a = json.loads( request.form['vess_a'] )
    vess_b = json.loads( request.form['vess_b'] )

    rad_a = json.loads( request.form['rad_a'] )
    rad_b = json.loads( request.form['rad_b'] )

    print(vess_a, vess_b)

    distances = [0,0,0,0]

    #list(itertools.product([0,-1],repeat=2))
    distances[0] = distance.euclidean(vess_a[0],vess_b[0])
    distances[1] = distance.euclidean(vess_a[0],vess_b[-1])
    distances[2] = distance.euclidean(vess_a[-1],vess_b[0])
    distances[3] = distance.euclidean(vess_a[-1],vess_b[-1])

    min_distance = distances.index(min(distances))
    vessel = {}
    radius = {}

    if min_distance == 0:
        vessel[index] = vess_a[::-1] + vess_b
        radius[index] = rad_a[::-1] + rad_b
    elif min_distance == 1:
        vessel[index] = vess_b + vess_a
        radius[index] = rad_b + rad_a
    elif min_distance == 2:
        vessel[index] = vess_a + vess_b
        radius[index] = rad_a + rad_b
    else:
        vessel[index] = vess_a + vess_b[::-1]
        radius[index] = rad_a + rad_b[::-1]

    print(vessel, radius)

    plot_params, frequency_params = eval_vessels(vessel)

    #print(request.form['rad_a'])
    #print(request.form['rad_b'])

    print(request.form['params_a'])
    print(request.form['params_b'])

    params_a = json.loads( request.form['params_a'] )
    params_b = json.loads( request.form['params_b'] )

    params = { index : [ float(np.min(radius[index])), float(np.max(radius[index])) , float(np.round(np.mean(radius[index]), 4)), float(np.round( np.std(radius[index]), 4)) , params_a[-1] + params_b[-1] ]}

    print(frequency_params, plot_params, params, radius, vessel, index)
    return jsonify(harmonics=frequency_params, plot_params=plot_params, params=params, radius=radius, vessel=vessel, index=index)

@app.route('/segm', methods = ['POST'])
def segmentation():

    src = request.files['img']
    model = int(request.form['model'])
    filename = request.cookies.get('filename') #request.form['filename'].split('=')[1]

    print(model, src, filename)

    src.save(os.path.join('static/images', filename + '.png') )

    img = cv2.imread(os.path.join('static/images', filename + '.png'), 0)
    print(img.shape)

    if model == 1 :
        prediction = cv2.resize(img, None, fx=3500/img.shape[1], fy=2336/img.shape[0], interpolation = cv2.INTER_CUBIC)
        prediction = make_prediction(img=prediction, weights='DRIVE.h5')
        prediction = cv2.resize(prediction, None, fx=img.shape[1]/3500, fy=img.shape[0]/2336, interpolation = cv2.INTER_AREA)

    if model == 2:
        prediction = cv2.resize(img, None, fx=700/img.shape[1], fy=605/img.shape[0], interpolation = cv2.INTER_AREA)
        prediction = make_prediction(img=prediction, weights='STARE.h5')
        prediction = cv2.resize(prediction, None, fx=img.shape[1]/700, fy=img.shape[0]/605, interpolation = cv2.INTER_CUBIC)

    elif model == 3:
        prediction = make_prediction(img=img, weights='ENDO.h5')

    print(img.shape)

    cv2.imwrite(os.path.join('static/images', filename + '_1.png'), prediction)
    dots_dict, vess_dict, radius_dict, params_dict, global_params, plot_params, frequency_params = postprocessing(prediction)

    print(plot_params, frequency_params, params_dict)

    #print('before jsonify')
    #print(plot_params)

    return jsonify( path=url_for('static', filename='images/' + filename + '.png'), vessels=vess_dict, dots=dots_dict, \
                    parameters=params_dict, radius=radius_dict, \
                    global_params=global_params, \
                    harmonics=frequency_params, plot_params=plot_params)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
