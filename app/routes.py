from flask import Blueprint, render_template, request, jsonify, current_app
import io
import numpy as np
import librosa
import datetime

bp = Blueprint('main', __name__)

def extract_features(audio_bytes, sr=22050, n_mfcc=13):
    """Extrae los MFCC y retorna un vector promedio de características."""
    audio_buffer = io.BytesIO(audio_bytes)
    y, sr = librosa.load(audio_buffer, sr=sr)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    mfccs_mean = np.mean(mfccs, axis=1)
    return mfccs_mean

def compare_features(features1, features2):
    """Calcula la similitud del coseno entre dos vectores de características."""
    numerator = np.dot(features1, features2)
    denominator = np.linalg.norm(features1) * np.linalg.norm(features2)
    if denominator == 0:
        return 0
    similarity = numerator / denominator
    return similarity

def load_reference_pattern():
    """Carga y procesa el patrón de referencia desde 'audio/reference.wav'."""
    try:
        with open('audio/reference.wav', 'rb') as f:
            audio_bytes = f.read()
        features = extract_features(audio_bytes)
        return features
    except Exception as e:
        print("Error al cargar el patrón de referencia:", e)
        return None

@bp.route('/')
def dashboard():
    """Muestra el dashboard con los eventos registrados."""
    db = current_app.config['DB']
    events = db.all()
    return render_template('dashboard.html', events=events)

@bp.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Endpoint para recibir un archivo de audio, procesarlo y registrar un evento."""
    if 'audio' not in request.files:
        return jsonify({"error": "No se encontró el archivo de audio"}), 400
    
    audio_file = request.files['audio']
    audio_bytes = audio_file.read()
    
    try:
        features = extract_features(audio_bytes)
    except Exception as e:
        return jsonify({"error": "Error al procesar el archivo de audio", "message": str(e)}), 500

    ref_features = load_reference_pattern()
    if ref_features is None:
        return jsonify({"error": "Patrón de referencia no disponible"}), 500

    similarity = compare_features(features, ref_features)
    threshold = 0.8  # Umbral

    if similarity < threshold:
        event_status = "interrumpido"
        detail = "El audio no coincide con el patrón de referencia"
    else:
        event_status = "on_air"
        detail = "El audio coincide con el patrón de referencia"

    event = {
        "estacion": "radio1",
        "estado": event_status,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "detalle": detail,
        "similarity": similarity
    }

    db = current_app.config['DB']
    db.insert(event)

    return jsonify({"message": "Audio procesado y evento registrado", "event": event}), 200

@bp.route('/api/status')
def api_status():
    """Endpoint que retorna en formato JSON todos los eventos registrados."""
    db = current_app.config['DB']
    events = db.all()
    return jsonify(events)
