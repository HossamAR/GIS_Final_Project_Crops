# Smart Crop Advisor

This is a web-based Crop Recommendation System using a machine learning model and a Leaflet map for GIS visualization.

## 📦 Features

- Web form to input soil and climate values (NPK, pH, temperature, etc.)
- Live crop prediction using a pre-trained XGBoost model
- Interactive map using Leaflet (centered on Turkey)
- Easily deployable to Render or run locally

---

## 🚀 How to Run (Locally)

### 1. Install Python 3.9+ and pip

Make sure you have Python installed:
```bash
python --version
```

### 2. Clone or Download this Project

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the app

```bash
python app.py
```

Then open your browser at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🌐 Deployment on Render

1. Upload the project to GitHub
2. Go to [https://render.com](https://render.com) and create a new Web Service
3. Choose your GitHub repo
4. Use the following settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add `xgboost` to `requirements.txt` if not already included
6. Press **Deploy**

---

## 📁 File Structure

- `app.py` — Main Flask app
- `templates/index.html` — Frontend (form + map)
- `uploads/xgb_model.pkl` — Pre-trained model
- `requirements.txt` — Python dependencies
- `Procfile` — Command to run the app on Render

---

## 🧠 Credits

Developed by Hossam AR for a GIS Final Project at Karabük University.