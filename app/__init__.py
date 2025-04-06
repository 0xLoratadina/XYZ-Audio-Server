import json
from flask import Flask
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from config import settings


class PrettyJSONStorage(JSONStorage):
    def write(self, data):
        self._handle.seek(0)
        json.dump(
            data,
            self._handle,
            indent=2,
            sort_keys=True,
            ensure_ascii=False
        )
        self._handle.truncate()
        self._handle.flush()


def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)

    db = TinyDB(app.config['TINIDB_PATH'], storage=PrettyJSONStorage)
    app.config['DB'] = db

    from app import routes
    app.register_blueprint(routes.bp)
    return app
