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

from model_cnn.predict_online import make_prediction
from parameters.eval_parameters import postprocessing, eval_vessels

from scipy.spatial import distance

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'well_known_secret'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def main():

    resp = make_response(render_template('main.html'))
    #uniq_name = str(round(time.time() ))
    #resp.set_cookie('filename', uniq_name)

    return resp

@app.route('/merge', methods=['POST'])
def merge():

    vessels = Flask.json_decoder().decode(request.form['vessels'])
    rads = Flask.json_decoder().decode(request.form['rads'])
    params = Flask.json_decoder().decode(request.form['params'])

    while len(vessels.keys()) > 1:

        border_dots = np.zeros((len(vessels.keys()), 2, 2))

        for key in vessels:

            min_dist = np.inf

            for i in [0,-1]:

                point_1 = vessels[key][i]

                for sec_key in vessels:

                    if key != sec_key:

                        for j in [0,-1]:

                            point_2 = vessels[sec_key][j]

                            if distance.euclidean(point_1,point_2) < min_dist:

                                min_dist = distance.euclidean(point_1, point_2)
                                closest_parts = [key,i,sec_key,j, min_dist]

            if closest_parts[1] == -1 and closest_parts[3] == -1:
                vessels[key] = vessels[key] + vessels[sec_key][::-1]
                rads[key] = rads[key] + rads[sec_key][::-1]

            if closest_parts[1] == 0 and closest_parts[3] == 0:
                vessels[key] = vessels[key][::-1] + vessels[sec_key]
                rads[key] = rads[key][::-1] + rads[sec_key]

            if closest_parts[1] == -1 and closest_parts[3] == 0:
                vessels[key] = vessels[key] + vessels[sec_key]
                rads[key] = rads[key] + rads[sec_key]

            if closest_parts[1] == 0 and closest_parts[3] == -1:
                vessels[key] = vessels[sec_key] + vessels[key]
                rads[key] = rads[sec_key] + rads[key]

            params[key] = [ float(param) for param in [ np.min(rads[key]) , np.max(rads[key]) , np.mean(rads[key]) , \
                                                        np.std(rads[key]) , len(vessels[key]) ]]

            del vessels[sec_key]
            del rads[sec_key]
            del params[sec_key]

            break

        continue

    plot_params, frequency_params = eval_vessels(vessels)
    return jsonify(harmonics=frequency_params[key], plot_params=plot_params[key], \
                   params=params[key], radius=rads[key], vessel=vessels[key])


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

    print('response sended')

    return jsonify( path=url_for('static', filename='images/' + filename + '.png'), \
                    path_segm=url_for('static', filename='images/' + filename + '_1.png'), \
                    vessels=vess_dict, dots=dots_dict, \
                    parameters=params_dict, radius=radius_dict, \
                    global_params=global_params, \
                    harmonics=frequency_params, plot_params=plot_params)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
