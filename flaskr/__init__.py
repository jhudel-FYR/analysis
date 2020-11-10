import os
from logging.config import dictConfig
from flask import Flask

from flaskr.database.blueprint import research_blueprint
from flaskr.blueprint import base_blueprint
from flaskr.auth.blueprint import auth_blueprint
from flaskr.database_static.blueprint import comp_blueprint
from flaskr.imageprocessing.blueprint import image_blueprint
from flaskr.genomics.blueprint import genomics_blueprint
from flaskr.clinical_data.blueprint import clinical_blueprint
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.Io.txt_file import TXTFILE
from . import (db, framework)

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'file': {
        'class': 'logging.FileHandler',
        'filename': 'system.log',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
})


def create_app(test_config=None):
    app = Flask(__name__, static_url_path="", instance_relative_config=None)
    app.config.from_mapping(
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'upload'),
        DOWNLOAD_FOLDER=os.path.join(app.instance_path, 'download'),
        IMAGE_FOLDER=os.path.join(app.static_folder, 'images'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # we need several try catch, because each folder it tries to create, it could throw the OSError exception
    # in case folder already exists
    # create the instance folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # create the upload folder
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    try:
        os.makedirs(app.config['DOWNLOAD_FOLDER'])
    except OSError:
        pass

    try:
        os.makedirs(app.config['IMAGE_FOLDER'])
    except OSError:
        pass

    # create specific folders
    try:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], XLSXFile.FOLDER))
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], TXTFILE.FOLDER))
    except OSError:
        pass

    db.init_app(app)
    framework.init_framework(app)

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(comp_blueprint)
    app.register_blueprint(research_blueprint)
    app.register_blueprint(image_blueprint)
    app.register_blueprint(genomics_blueprint)
    app.register_blueprint(clinical_blueprint)
    app.register_blueprint(base_blueprint)

    return app
