from flask import Flask
from tinydb import TinyDB
from config import settings

def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)
    db = TinyDB(app.config['TINIDB_PATH'])
    app.config['DB'] = db
    from app import routes
    app.register_blueprint(routes.bp)
    return app
