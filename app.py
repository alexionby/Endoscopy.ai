from flask import Flask, render_template, url_for, request
from flask import jsonify, send_from_directory, make_response

import os
import json
import secrets
import time
import webbrowser

import numpy as np
from skimage import io

from scipy.spatial import distance
from scipy.interpolate import LinearNDInterpolator

from model_cnn.predict_online import make_prediction
from parameters.eval_parameters import postprocessing, eval_vessel

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def main_page():
    return render_template("main.html")

@app.route('/merge', methods=['POST'])
def merge():

    vessels = Flask.json_decoder().decode(request.form['vessels'])
    rads    = Flask.json_decoder().decode(request.form['rads'])
    params  = Flask.json_decoder().decode(request.form['params'])

    while len(vessels.keys()) > 1:
        keys = list(map(str, sorted(map(int, vessels.keys()))))
        for key in keys:
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
            
            key = closest_parts[0]
            sec_key = closest_parts[2]

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

            print("from merge func: ", key, len(vessels[key]))

            params[key] = [ float(param) for param in [ np.min(rads[key]) , np.max(rads[key]) , np.mean(rads[key]) , \
                                                        np.std(rads[key]) , params[key][4] + params[sec_key][4] ]]

            print(params)
            print(key, sec_key)

            del vessels[sec_key]
            del rads[sec_key]
            del params[sec_key]
            break

        continue

    plot_params, frequency_params = eval_vessel(vessels[key], key)
    return jsonify(harmonics=frequency_params, plot_params=plot_params, \
                   params=params[key], radius=rads[key], vessel=vessels[key])


@app.route('/segm', methods = ['POST'])
def segmentation():

    src      = request.files['img']
    model    = request.form['model']
    filename = request.cookies.get('filename')

    src.save(os.path.join('static/images', filename + '.png') )
    img = np.uint8(io.imread(os.path.join('static/images', filename + '.png'), as_gray=True) * 255)

    if model == "1":
        prediction = make_prediction(img=img, weights='DRIVE.h5')
    elif model == "2":
        prediction = make_prediction(img=img, weights='STARE.h5')
    elif model == "3":
        prediction = make_prediction(img=img, weights='ENDO.h5')
    else:
        print("Model was not selected!")
        return None

    io.imsave(os.path.join('static/images', filename + '_1.png'), prediction)
    dots_dict, vess_dict, radius_dict, params_dict, global_params, plot_params, frequency_params = postprocessing(prediction)

    print('processing was finished')

    return jsonify( path=url_for('static', filename='images/' + filename + '.png'), \
                    path_segm=url_for('static', filename='images/' + filename + '_1.png'), \
                    vessels=vess_dict, dots=dots_dict, \
                    parameters=params_dict, radius=radius_dict, \
                    global_params=global_params, \
                    harmonics=frequency_params, plot_params=plot_params)


def main():

    url = 'http://localhost:5000/'
    webbrowser.open_new_tab(url)
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
