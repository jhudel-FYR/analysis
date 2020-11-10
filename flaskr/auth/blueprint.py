
import re
from functools import wraps
from flask import render_template, session, redirect, url_for, request, flash, Blueprint, current_app
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.auth.create_user import check_entries, create_user
from flaskr.auth.auth_database.repository import Repository
from flaskr.framework.model.request.response import Response
from flaskr.auth.emailer.token import confirm_token
from flaskr.auth.emailer.email import send_email

auth_blueprint = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

ACCESS = {
    'unconfirmed': 0,
    'guest': 1,
    'user': 2,
    'admin': 3
}


@auth_blueprint.route('', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        response = check(username, password)
        if not response.is_success():
            error = response.get_message()
        if error is None:
            login_user(username)
            return redirect(url_for('research.home'))

        flash(error, 'error')

    return render_template('login.html')


@auth_blueprint.route('/logout')
def logout():
    session.clear()
    session['user_logged_in'] = False
    return redirect(url_for('auth.login'))


def require_access(access_level: str = ACCESS['guest']):
    def _outer(view):
        @wraps(view)
        def _inner(**kwargs):
            if 'user_logged_in' not in session:
                return redirect(url_for('auth.login'))

            if not session['user_logged_in']:
                return redirect(url_for('auth.login'))

            if not session.get('username'):
                return redirect(url_for('auth.login'))

            user_repository = Repository()
            user = user_repository.get_by_username(session['username'])

            if user is None:
                return redirect(url_for('auth.login'))

            if not user.is_allowed(ACCESS[access_level]):
                flash('You do not have access to that page (yet), '
                      'please contact the admin if this is in error.', 'error')
                return render_template('login.html')

            return view(**kwargs)
        return _inner
    return _outer


admin_login_required = require_access('admin')
user_login_required = require_access('user')
login_required = require_access('guest')


def check(user: str, password: str) -> Response:
    user_repository = Repository()
    user = user_repository.get_by_username(user)

    if user is None:
        return Response(False, 'No account with that username was found')

    if check_password_hash(user.get_password(), password):
        return Response(True, user.is_admin())

    return Response(False, 'Invalid credentials provided')


def edit_user(email, username, oldpassword, newpassword) -> Response:
    user_repository = Repository()

    user = user_repository.get_by_email(email=email)
    if user is None:
        return Response(False, 'No user found with given email.')

    if not check_password_hash(user.get_password(), oldpassword):
        return Response(False, 'Old password could not be validated. Please try again.')

    user['username'] = username
    user['password'] = generate_password_hash(newpassword)
    user_repository.save(user)
    return Response(True, '')


def login_user(username):
    session.clear()
    session['user_logged_in'] = True
    session['username'] = username


@auth_blueprint.route('/edit', methods=['GET', 'POST'])
@user_login_required
def edit():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        oldpassword = request.form['oldpassword']
        newpassword = request.form['newpassword']
        response = check_entries(email, username, oldpassword)
        if not response.is_success():
            flash(response.get_message(), 'error')
            return render_template('edit.html')

        response = edit_user(email, username, oldpassword, newpassword)
        if not response.is_success():
            flash(response.get_message(), 'error')
            return render_template('edit.html')

        session.clear()
        session['user_logged_in'] = False

        flash('User edited!', 'success')
        return redirect(url_for('research.home'))

    return render_template('edit.html')


@auth_blueprint.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        email = request.form['email']
        permission = 0
        token = uuid4().hex

        # regex_email = re.search(r'\b@fyrdiagnostics\.com\b', email)
        # if regex_email is None:
        #     flash('Only FYR employees may register at this time.', 'error')
        #     return redirect(url_for('base.home'))

        response = create_user(email=email,
                               username=request.form['username'],
                               password=request.form['password'],
                               permission=permission,
                               organization=request.form['organization'],
                               token=token)
        if not response.is_success():
            flash(response.get_message(), 'error')
            return redirect(url_for('auth.login'))

        send_email(current_app,
                   recipients=[email],
                   subject='FYR Diagnostics Platform Registration',
                   html=render_template('confirm.html',
                                        name=request.form['username'],
                                        token=token,
                                        url="http://localhost:5000" if current_app.config.get('DEBUG') else 'https://analysis.fyrdiagnostics.com/'))

        send_email(current_app,
                   recipients=[current_app.config['SES_EMAIL_SOURCE']],
                   subject='Pending Registration Request',
                   html=render_template('request.html',
                                        email=request.form['email'],
                                        username=request.form['username'],
                                        status='admin' if request.form.get('admin') else 'user'))

        flash('We just sent an email to %s!' % email, 'success')
        flash('If you don\'t see a message in your inbox, check your spam or junk mail folder.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('create.html')


@auth_blueprint.route('/confirm/<token>', methods=['GET', 'POST'])
def confirm(token):
    user = confirm_token(token)
    if user is None:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    if user.is_allowed(ACCESS['guest']):
        flash('Account is already confirmed.', 'success')

    else:
        user['permission'] = ACCESS['guest']
        user_repository = Repository()
        user_repository.save(user)
        flash('You have confirmed your email. Thanks!', 'success')

    login_user(user.get_username())
    return redirect(url_for('research.home'))
