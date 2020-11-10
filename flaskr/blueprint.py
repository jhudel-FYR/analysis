from flask import Blueprint, redirect, url_for

from flaskr.auth.blueprint import login_required, current_app

base_blueprint = Blueprint('base', __name__, template_folder='templates')


@base_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return redirect(url_for('research.home'))
  

@base_blueprint.route('/home', methods=['GET', 'POST'])
@login_required
def svelte():
    return current_app.send_static_file('index.html')
