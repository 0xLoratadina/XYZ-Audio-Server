import os
import io
import numpy as np
import librosa
import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for
from passlib.hash import bcrypt

bp = Blueprint('main', __name__)

def extract_features(audio_bytes, sr=22050, n_mfcc=13):
    audio_buffer = io.BytesIO(audio_bytes)
    y, sr = librosa.load(audio_buffer, sr=sr)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return np.mean(mfccs, axis=1)

def compare_features(features1, features2):
    numerator = np.dot(features1, features2)
    denominator = np.linalg.norm(features1) * np.linalg.norm(features2)
    if denominator == 0:
        return 0
    return numerator / denominator

@bp.route('/register', methods=['GET', 'POST'])
def register():
    db = current_app.config['DB']
    users_table = db.table('users')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('register.html', error="Completa todos los campos.")
        if users_table.search(lambda u: u['username'] == username):
            return render_template('register.html', error="El usuario ya existe.")
        hashed_password = bcrypt.hash(password)
        users_table.insert({"username": username, "password": hashed_password})
        return redirect(url_for('main.login'))
    else:
        return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    db = current_app.config['DB']
    users_table = db.table('users')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('login.html', error="Completa todos los campos.")
        user = users_table.search(lambda u: u['username'] == username)
        if not user:
            return render_template('login.html', error="Usuario o contraseña incorrectos.")
        user_data = user[0]
        hashed_password = user_data['password']
        if bcrypt.verify(password, hashed_password):
            session['user_id'] = username
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos.")
    else:
        return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.login'))

@bp.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    db = current_app.config['DB']
    events = db.all()
    stations = db.table('stations').all()
    return render_template('dashboard.html', events=events, stations=stations)

@bp.route('/add_station', methods=['POST'])
def add_station():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    db = current_app.config['DB']
    stations_table = db.table('stations')
    nombre = request.form.get('nombre')
    frecuencia = request.form.get('frecuencia')
    ciudad = request.form.get('ciudad')
    audio_interface = request.form.get('audio_interface')
    audio_label = request.form.get('audio_label') or ''
    logo_file = request.files.get('logo')
    logo_filename = None
    if logo_file and logo_file.filename != '':
        logo_filename = logo_file.filename
        logos_dir = os.path.join(current_app.root_path, 'static', 'logos')
        if not os.path.exists(logos_dir):
            os.makedirs(logos_dir)
        logo_path = os.path.join(logos_dir, logo_filename)
        logo_file.save(logo_path)
    station = {
        "nombre": nombre,
        "logo": logo_filename,
        "frecuencia": frecuencia,
        "ciudad": ciudad,
        "audio_interface": audio_interface,
        "audio_label": audio_label,
        "estado": "Desconocido",
        "ultima_actualizacion": datetime.datetime.utcnow().isoformat()
    }
    stations_table.insert(station)
    return redirect(url_for('main.dashboard'))

@bp.route('/edit_station/<int:station_id>', methods=['GET', 'POST'])
def edit_station(station_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    db = current_app.config['DB']
    stations_table = db.table('stations')
    station = stations_table.get(doc_id=station_id)
    if not station:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        frecuencia = request.form.get('frecuencia')
        ciudad = request.form.get('ciudad')
        audio_interface = request.form.get('audio_interface')
        audio_label = request.form.get('audio_label') or ''
        logo_file = request.files.get('logo')
        logo_filename = station.get('logo')
        if logo_file and logo_file.filename != '':
            logo_filename = logo_file.filename
            logos_dir = os.path.join(current_app.root_path, 'static', 'logos')
            if not os.path.exists(logos_dir):
                os.makedirs(logos_dir)
            logo_path = os.path.join(logos_dir, logo_filename)
            logo_file.save(logo_path)
        station['nombre'] = nombre
        station['frecuencia'] = frecuencia
        station['ciudad'] = ciudad
        station['audio_interface'] = audio_interface
        station['audio_label'] = audio_label
        station['logo'] = logo_filename
        station['ultima_actualizacion'] = datetime.datetime.utcnow().isoformat()
        stations_table.update(station, doc_ids=[station_id])
        return redirect(url_for('main.dashboard'))
    else:
        return render_template('edit_station.html', station=station, station_id=station_id)

@bp.route('/delete_station/<int:station_id>')
def delete_station(station_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    db = current_app.config['DB']
    stations_table = db.table('stations')
    stations_table.remove(doc_ids=[station_id])
    return redirect(url_for('main.dashboard'))

@bp.route('/update_station/<int:station_id>')
def update_station(station_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    db = current_app.config['DB']
    stations_table = db.table('stations')
    station = stations_table.get(doc_id=station_id)
    if station:
        station['estado'] = "Activo"
        station['ultima_actualizacion'] = datetime.datetime.utcnow().isoformat()
        stations_table.update(station, doc_ids=[station_id])
    return redirect(url_for('main.dashboard'))

@bp.route('/public_listen/<int:station_id>')
def public_listen(station_id):
    db = current_app.config['DB']
    station = db.table('stations').get(doc_id=station_id)
    if not station:
        return redirect(url_for('main.dashboard'))
    return render_template('public_listen.html', station=station)

@bp.route('/upload_audio', methods=['POST'])
def upload_audio():
    db = current_app.config['DB']
    if 'audio' not in request.files:
        return jsonify({"error": "No se encontró el archivo de audio"}), 400
    audio_file = request.files['audio']
    audio_bytes = audio_file.read()
    try:
        features = extract_features(audio_bytes)
    except Exception as e:
        return jsonify({"error": "Error al procesar el archivo de audio", "message": str(e)}), 500
    event = {
        "estacion": "radio1",
        "estado": "on_air",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "detalle": "Audio subido"
    }
    db.insert(event)
    return jsonify({"message": "Audio procesado y evento registrado", "event": event}), 200
