from flask import redirect, url_for, request, flash, Blueprint, render_template, send_file
from io import BytesIO
import json
import pandas as pd

from flaskr.auth.blueprint import login_required, current_app
from flaskr.clinical_data.validators.importvalidator import ImportValidator
from flaskr.clinical_data.view_model.importprocessor import ImportProcessor
from flaskr.clinical_data.view_model.clinicalprocessor import ByPasser
from flaskr.clinical_data.view_model.writer import Writer, write_maestro_templates
from flaskr.clinical_data.view_model.writer import Writer as ClinicalWriter
from flaskr.clinical_data.validators.importvalidator import ImportValidator as FileValidator
from flaskr.framework.model.request.rest import response, bad_request, success, not_found, error
from flaskr.clinical_data.sample_models.repository import Repository
from flaskr.clinical_data.sample_models.manager import Manager
from flaskr.clinical_data.sample_models.collection import Collection



clinical_blueprint = Blueprint('clinical', __name__, template_folder='templates', url_prefix='/clinical')


@clinical_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return current_app.send_static_file('index.html')


@clinical_blueprint.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        validator = FileValidator(request)
        result = validator.execute()
        if not result.is_success():
            flash(result.get_message(), 'error')
            return error()

        importer = ImportProcessor()
        result = importer.update_results(result.get_name())
        if not result.is_success():
            flash(result.get_message())
        return success()
    return render_template('research.home')


@clinical_blueprint.route('/download/<id>', methods=['GET', 'POST'])
@login_required
def download(id):
    clinical_writer = ClinicalWriter(writer=None, dataset_id=id)
    zip_file = clinical_writer.output_results(id=id)

    if zip_file is not None:
        return response(json.dumps(zip_file))
    return success()


@clinical_blueprint.route('/assignrack/<id>', methods=['GET', 'POST'])
@login_required
def set_rack(id):
    if request.method == 'POST':
        repository = Repository()
        sample = repository.get_by_fyr_ID(id)
        if sample is None:
            return bad_request('No tube identified with FYR ID: %s ' % id)

        importer = ImportProcessor()
        result = importer.assign_rack(sample=sample,
                                      rack=request.form['rack_id'],
                                      position=request.form['rack_position'])
        if not result.is_success():
            return bad_request(result.get_message())

        return success()
    return success()


@clinical_blueprint.route('/startexperiment/<rack_id>', methods=['GET', 'POST'])
@login_required
def set_experiment(rack_id):
    if request.method == 'POST':
        result = start_experiment(rack_id)
        return success()

        # if result is not None:
        #     return send_file(result,
        #                      'maestro_template.csv')

    return redirect(url_for('research.home'))


@clinical_blueprint.route('/samplelist', methods=['GET', 'POST'])
@login_required
def samplelist():
    validator = ImportValidator(request)
    result = validator.execute()
    if not result.is_success():
        flash(result.get_message(), 'error')
        return redirect(url_for('research.home'))

    importer = ImportProcessor()
    result = importer.init_samples()
    if not result.is_success():
        flash(result.get_message())

    clinical_writer = Writer(writer=None, dataset_id='')
    data = clinical_writer.get_sample_list_for_pdf(importer.provider_id)
    if len(data['samples']) > 0:
        return render_template('samplelist.html',
                               samples=data['samples'],
                               provider='',
                               image='https://analysis.fyrdiagnostics.com/logo/FYR-logo.png')
    return redirect(url_for('research.home'))
    #     return response(json.dumps(data))
    # return success()


@clinical_blueprint.route('/resultbypass', methods=['GET', 'POST'])
@login_required
def ResultBypass():
    validator = ImportValidator(request)
    result = validator.execute()

    if not result.is_success():
        flash(result.get_message(), 'error')
        return redirect(url_for('research.home'))

    bypass = ByPasser()
    result = bypass.execute()

    if not result.is_success():
        flash(result.get_message(), 'error')
        return redirect(url_for('research.home'))

    io = BytesIO()
    excelwriter = pd.ExcelWriter(io, engine='xlsxwriter')
    bypass.fdf.to_excel(excelwriter, startcol=-1)
    excelwriter.save()
    io.seek(0)
    return send_file(io, attachment_filename='results_summary.xlsx', as_attachment=True)


@clinical_blueprint.route('/samples', methods=['GET', 'POST'])
@login_required
def samples():
    collection = Collection()
    if request.method == 'POST':
        for key, value in request.form.items():
            if key == 'status':
                value = int(value)
            collection.add_filter(key, value)
    collection.add_order('provider_id', -1)
    collection.add_order('status', 1)
    collection.add_order('report', -1)
    return response(collection.to_json())


@clinical_blueprint.route('/initsample/<id>', methods=['GET', 'POST'])
@login_required
def initsample(id):
    repository = Repository()
    sample = repository.get_by_fyr_ID(id)
    if sample is None:
        importer = ImportProcessor()
        result = importer.init_sample(id)
        if not result.is_success():
            return bad_request(result.get_message())
        return response(success())
    return bad_request('FYR ID already exists in system')


@clinical_blueprint.route('/checkinsample/<id>', methods=['GET', 'POST'])
@login_required
def checkinsample(id):
    repository = Repository()
    sample = repository.get_by_fyr_ID(id)
    if sample is not None:
        if request.method == 'POST':
            if request.form.get('verification') == 'mismatch':
                # TODO: delete?
                return bad_request('Sample was not checked in. TODO: remove from system?')
            else:
                importer = ImportProcessor()
                if importer.check_in_sample(sample):
                    repository.save(sample)
                    return response(success())
                return bad_request('unknown error checking in sample')
        return response(sample.to_json())
    return bad_request('FYR ID does not exist in system')


@clinical_blueprint.route('/sample/<id>', methods=['GET', 'POST'])
@login_required
def sample(id):
    repository = Repository()
    sample = repository.get_by_fyr_ID(id)
    if sample is None:
        return bad_request('Error, no sample found.')

    if request.method == 'POST':
        for key, value in request.form.items():
            if key in sample.get_data().keys():
                if key == 'status':
                    value = int(value)
                if key == 'sample_id1':
                    # sample is getting patient IDs
                    if sample['status'] == 0:
                        sample['status'] += 1
                if key == 'rack_id':
                    # sample is getting assigned to a rack
                    if sample['status'] == 2:
                        sample['status'] += 1
                sample[key] = value

        repository.save(sample)

    return response(sample.to_json())


def start_experiment(rack_id):
    zip = None
    manager = Manager()
    collection = Collection()
    collection.add_filter('rack_id', rack_id)
    collection.add_order('rack_position', -1)
    positions = []
    fyr_ids = []
    for sample in collection:
        if sample['status'] == 3:
            sample['status'] += 1
            manager.add(sample)
        else:
            current_app.logger.warning('Incomplete sample %s is initialied in an experiment for rack %s'
                                       % (sample.get_fyr_id(), rack_id))
            flash('Incomplete sample %s is initialied in an experiment for rack %s'
                  % (sample.get_fyr_id(), rack_id), 'error')
            continue

        positions.append(sample.get_rack_position())
        fyr_ids.append(sample.get_fyr_id())

    # zip = write_maestro_templates(positions, fyr_ids)
    # TODO: build bio rad 96 plate templates x3 and a cassette list for reference
    # TODO: determine what to do with incomplete racks (fill out half a template?)

    manager.save()
    return zip
