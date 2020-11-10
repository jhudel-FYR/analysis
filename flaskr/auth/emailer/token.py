from itsdangerous import URLSafeTimedSerializer

from flask import current_app

from flaskr.auth.auth_database.repository import Repository


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token):
    user_repository = Repository()
    user = user_repository.get_by_token(token)
    return user
