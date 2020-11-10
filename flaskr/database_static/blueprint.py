
from flaskr.auth.blueprint import login_required
from flask import render_template, request, flash, Blueprint
from flaskr.database_static.componentprocessor import ImportComponents
from flaskr.database_static.baseassayprocessor import ImportBaseAssays
from flaskr.database_static.baseprotocolprocessor import ImportBaseProtocols
from flaskr.database_static.data_fix import DataFix


comp_blueprint = Blueprint('comp', __name__, template_folder='templates')


@comp_blueprint.route('/components', methods=['GET', 'POST'])
@login_required
def import_components():
    if request.method == 'POST':
        importer = ImportComponents()
        response = importer.execute(request)
        if not response.is_success():
            flash(response.get_message(), 'error')
        else:
            flash(response.get_message(), 'success')
    return render_template('componentimport.html')


@comp_blueprint.route('/baseassays', methods=['GET', 'POST'])
@login_required
def import_base_assays():
    if request.method == 'POST':
        importer = ImportBaseAssays()
        response = importer.execute(request)
        if not response.is_success():
            flash(response.get_message(), 'error')
        else:
            flash(response.get_message(), 'success')
    return render_template('componentimport.html')


@comp_blueprint.route('/baseprotocols', methods=['GET', 'POST'])
@login_required
def import_base_protocols():
    if request.method == 'POST':
        importer = ImportBaseProtocols()
        response = importer.execute(request)
        if not response.is_success():
            flash(response.get_message(), 'error')
        else:
            flash(response.get_message(), 'success')
    return render_template('componentimport.html')


@comp_blueprint.route('/datafix', methods=['GET', 'POST'])
@login_required
def data_fix():
    if request.method == 'POST':
        importer = DataFix()
        response = importer.execute(request)
        if not response.is_success():
            flash(response.get_message(), 'error')
        else:
            flash(response.get_message(), 'success')

    return render_template('datafix.html')


