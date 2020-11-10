import pytest

from flaskr import create_app
from flaskr import db


@pytest.fixture
def app():
    app = create_app({
        'SECRET_KEY': 'test',
        'TESTING': True,
        'DB_NAME': 'test_fyr_dev',
        'DB_HOST': 'localhost',
        'DB_PORT': 27017,
    })
    app.debug = True

    with app.app_context():
        db.init_db()

        yield app

        for collection in db.get_db().list_collection_names():
            db.get_db().drop_collection(collection)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
