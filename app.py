from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import pickle
import pandas as pd
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from datetime import datetime
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import folium

app = Flask(__name__)

# Configure folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MODEL_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'models')
app.config['TIFF_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'tiff_data')
app.config['PREDICTION_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'predictions')

# Ensure directories exist
os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)
os.makedirs(app.config['TIFF_FOLDER'], exist_ok=True)
os.makedirs(app.config['PREDICTION_FOLDER'], exist_ok=True)

ALLOWED_TIFF_KEYS = [
    "NDVI", "aspect", "elevation", 
    "lulc", "org_carbon", "precip",
    "slope", "soil_pH", "temp"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    models = os.listdir(app.config['MODEL_FOLDER'])
    tiffs = os.listdir(app.config['TIFF_FOLDER'])
    return render_template('dashboard.html', models=models, tiffs=tiffs)

@app.route('/upload_model', methods=['POST'])
def upload_model():
    file = request.files.get('model_file')
    if file and file.filename.endswith('.pkl'):
        filename = secure_filename(f"model_{datetime.now().strftime('%Y%m%d%H%M%S')}.pkl")
        file.save(os.path.join(app.config['MODEL_FOLDER'], filename))
        return jsonify({'status': 'success', 'message': 'Model uploaded successfully', 'filename': filename})
    return jsonify({'status': 'error', 'message': 'Please upload a valid .pkl file'})

@app.route('/upload_tiff', methods=['POST'])
def upload_tiff():
    file = request.files.get('tiff_file')
    tiff_type = request.form.get('tiff_type')
    if file and tiff_type in ALLOWED_TIFF_KEYS:
        filename = secure_filename(f"{tiff_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.tif")
        file.save(os.path.join(app.config['TIFF_FOLDER'], filename))
        return jsonify({'status': 'success', 'message': 'TIFF uploaded successfully', 'filename': filename})
    return jsonify({'status': 'error', 'message': 'Invalid TIFF file or type'})

@app.route('/list_models')
def list_models():
    models = [f for f in os.listdir(app.config['MODEL_FOLDER']) if f.endswith('.pkl')]
    return jsonify({'status': 'success', 'models': models})

@app.route('/list_tiffs')
def list_tiffs():
    tiffs = {}
    for filename in os.listdir(app.config['TIFF_FOLDER']):
        for key in ALLOWED_TIFF_KEYS:
            if filename.startswith(key):
                tiffs[key] = filename
                break
    return jsonify({'status': 'success', 'tiffs': tiffs})

def align_and_resample_tiffs(folder, reference_key="elevation"):
    paths = {key: None for key in ALLOWED_TIFF_KEYS}
    for fname in os.listdir(folder):
        for key in ALLOWED_TIFF_KEYS:
            if fname.startswith(key):
                paths[key] = os.path.join(folder, fname)
    if not paths[reference_key]:
        raise ValueError("Reference TIFF not found")
    with rasterio.open(paths[reference_key]) as ref:
        profile = ref.profile
        height, width = ref.shape
        stack = []
        for key in ALLOWED_TIFF_KEYS:
            path = paths[key]
            if not path: raise ValueError(f"Missing {key} raster")
            with rasterio.open(path) as src:
                arr = np.zeros((height, width), dtype=np.float32)
                reproject(
                    rasterio.band(src, 1), arr,
                    src_transform=src.transform, dst_transform=ref.transform,
                    src_crs=src.crs, dst_crs=ref.crs,
                    resampling=Resampling.bilinear
                )
                arr[arr == ref.nodata] = np.nan
                stack.append(np.nan_to_num(arr, nan=0.0).flatten())
        return pd.DataFrame(np.column_stack(stack), columns=ALLOWED_TIFF_KEYS), profile

@app.route('/predict', methods=['POST'])
def predict():
    try:
        model_name = request.form.get('model_filename')
        if not model_name:
            return jsonify({'status': 'error', 'message': 'No model selected'})
        model_path = os.path.join(app.config['MODEL_FOLDER'], model_name)
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        df, profile = align_and_resample_tiffs(app.config['TIFF_FOLDER'])

        # Ensure column names match the trained model
        df.columns = [c.strip() for c in df.columns]
        df = df.rename(columns={
            'ndvi': 'NDVI',
            'landcover': 'lulc',
            'soil_ph': 'soil_pH'
        })
        print("🔍 Available columns before prediction:", df.columns.tolist())

        prediction = model.predict_proba(df[ALLOWED_TIFF_KEYS])[:, 1]
        prediction_image = prediction.reshape(profile['height'], profile['width'])

        tif_name = f"prediction_{datetime.now().strftime('%Y%m%d%H%M%S')}.tif"
        tif_path = os.path.join(app.config['PREDICTION_FOLDER'], tif_name)
        profile.update(dtype=rasterio.float32, count=1)
        with rasterio.open(tif_path, 'w', **profile) as dst:
            dst.write(prediction_image.astype(rasterio.float32), 1)

        map_name = f"map_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
        map_path = os.path.join(app.config['PREDICTION_FOLDER'], map_name)
        bounds = [[profile['transform'][5] + profile['transform'][4]*profile['height'], profile['transform'][2]],
                  [profile['transform'][5], profile['transform'][2] + profile['transform'][0]*profile['width']]]
        m = folium.Map(location=[sum([b[0] for b in bounds])/2, sum([b[1] for b in bounds])/2], zoom_start=7)
        folium.raster_layers.ImageOverlay(
            image=prediction_image, bounds=bounds,
            colormap=lambda x: (1, 1-x, 0, x), opacity=0.7
        ).add_to(m)
        m.save(map_path)

        return jsonify({
            'status': 'success',
            'prediction_tiff': f'/download_prediction/{tif_name}',
            'map_html': f'/view_map/{map_name}'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/download_prediction/<filename>')
def download_prediction(filename):
    return send_from_directory(app.config['PREDICTION_FOLDER'], filename, as_attachment=True)

@app.route('/view_map/<filename>')
def view_map(filename):
    return send_from_directory(app.config['PREDICTION_FOLDER'], filename)

@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_type = request.form.get('file_type')
    filename = request.form.get('filename')
    folder = app.config['MODEL_FOLDER'] if file_type == 'model' else app.config['TIFF_FOLDER']
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'status': 'success', 'message': f'{filename} deleted'})
    return jsonify({'status': 'error', 'message': 'File not found'})

if __name__ == '__main__':
    app.run(debug=True)
