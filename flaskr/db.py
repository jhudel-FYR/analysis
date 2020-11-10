from pymongo import MongoClient
import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        client = MongoClient(current_app.config['DB_HOST'],
                             int(current_app.config['DB_PORT']))[current_app.config['DB_NAME']]
        g.db = client
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        g.db = None


def init_db():
    get_db()


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Connected to mongo')


@click.command('close-db')
@with_appcontext
def close_db_command():
    close_db()
    click.echo('Disconnected from mongo')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
