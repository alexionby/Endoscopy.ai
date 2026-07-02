# Endoscopy.ai

A web application for automatic blood-vessel segmentation and quantitative analysis of endoscopic and retinal images. A U-Net convolutional neural network (Keras/TensorFlow) produces a vessel probability map, which is then post-processed to extract individual vessels, measure their geometry, and report per-vessel and global statistics — all through an interactive browser UI.

## Features

- **U-Net segmentation** of vessels with three pretrained weight sets:
  - `DRIVE.h5` — retinal fundus images (DRIVE dataset)
  - `STARE.h5` — retinal fundus images (STARE dataset)
  - `ENDO.h5` — endoscopic images
- **Tiled inference** — the input image is mirror-padded and split into overlapping 192×192 tiles, so images of arbitrary size can be processed; only the central 96×96 region of each prediction is kept to avoid border artifacts.
- **Vessel post-processing** — thresholding, distance-map construction, Zhang–Suen skeletonization with staircase removal, and tracing of individual vessel centerlines.
- **Quantitative parameters** per vessel and globally: min/max/mean radius, standard deviation, length, vessel density ("brick" area coverage), plus a harmonic (frequency) analysis of the centerline for tortuosity estimation.
- **Interactive canvas UI** — layered view (original image / segmentation mask / traced vessels) with per-layer visibility and opacity controls, manual vessel-segment merging, and result download.
- **Desktop packaging** — the whole app can be frozen into a standalone executable with cx_Freeze.

## Project structure

```
app.py                              # Flask server: routes, vessel merging, inference endpoint
setup.py                            # cx_Freeze build script for a standalone executable
debug.py                            # Offline visualization of traced vessels (matplotlib)
models/                             # Pretrained U-Net weights (DRIVE.h5, STARE.h5, ENDO.h5)
model_cnn/
    train.py                        # U-Net architecture definition (Keras)
    predict_online.py               # Tiled inference: pad → split → predict → stitch
    data.py                         # Training data preparation
parameters/
    eval_parameters.py              # Post-processing: thresholds, distance map, vessel metrics
    skeleton_with_additions.py      # Zhang–Suen skeletonization, staircase removal
templates/                          # Jinja2 templates (index.html, main.html, base.html)
static/
    canvas.js                       # Frontend: canvas rendering, layers, user interaction
    style.css
    images/                         # Uploaded images and generated masks
```

## API endpoints

| Route | Method | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/main` | GET | Main analysis UI |
| `/segm` | POST | Accepts an image and a model id (`1` = DRIVE, `2` = STARE, `3` = ENDO); returns the segmentation mask path, traced vessels, radii, per-vessel parameters, global statistics, and harmonic analysis as JSON |
| `/merge` | POST | Merges user-selected vessel segments by iteratively joining the closest endpoints; returns the merged vessel with recomputed parameters |

## Getting started

### Requirements

The project targets the TensorFlow 1.x / standalone Keras era; recent library versions have breaking changes (`keras.layers.normalization`, `skimage.util.pad`, and `scipy.ndimage.filters` were removed in later releases). A known-good environment:

- Python 3.6–3.7
- `tensorflow` 1.x, `keras` < 2.4
- `numpy`, `scipy`, `scikit-image` < 0.16
- `flask`

```bash
pip install "tensorflow<2" "keras<2.4" "scikit-image<0.16" numpy scipy flask
```

### Run

```bash
python app.py
```

The server starts on `http://localhost:5000/` and opens the page in the default browser automatically.

### Usage

1. Open **/main**, load an image (PNG/JPEG/GIF).
2. Select a model matching the image type (retina or endoscopy).
3. Click **Processing** — the segmentation mask and traced vessels appear as toggleable layers over the original.
4. Inspect per-vessel parameters, merge broken segments if needed, and download the result.

### Build a standalone executable

```bash
python setup.py build
```

cx_Freeze bundles the server, templates, static assets, and model weights into `build/`.

## Roadmap

- [x] Fix axis-rotation bug in vessel alignment
- [ ] Write uploaded files to a stream instead of disk

## References

- [U-Net: Convolutional Networks for Biomedical Image Segmentation](https://arxiv.org/abs/1505.04597)
- [LinkNet: Exploiting Encoder Representations for Efficient Semantic Segmentation](https://arxiv.org/pdf/1707.03718.pdf)
- LinkNet implementations in Keras: [nickhitsai/LinkNet-Keras](https://github.com/nickhitsai/LinkNet-Keras/blob/master/linknet.py), [davidtvs/Keras-LinkNet](https://github.com/davidtvs/Keras-LinkNet/blob/master/models/linknet.py)
- ResNet in Keras: [raghakot/keras-resnet](https://github.com/raghakot/keras-resnet/blob/master/resnet.py), [broadinstitute/keras-resnet](https://github.com/broadinstitute/keras-resnet), [fchollet/deep-learning-models](https://github.com/fchollet/deep-learning-models/blob/master/resnet50.py)
- [Understanding and implementing ResNet/ResNeXt architectures](https://medium.com/@14prakash/understanding-and-implementing-architectures-of-resnet-and-resnext-for-state-of-the-art-image-cf51669e1624)
