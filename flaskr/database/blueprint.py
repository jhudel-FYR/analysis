
from flask import render_template, redirect, url_for, request, flash, Blueprint, \
    send_file, current_app
import zipfile
import pandas as pd
import base64
from io import BytesIO
import os

from flaskr.auth.blueprint import require_access
from flaskr.model.importprocessor import ImportProcessor
from flaskr.database.dataset_models.repository import Repository
from flaskr.database_static.component_models.collection import Collection
from flaskr.database.dataset_models.collection import Collection as DatasetCollection
from flaskr.model.processor import Processor
from flaskr.model.delete_processor import DeleteProcessor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.clinical_data.view_model.writer import Writer as ClinicalWriter
from flaskr.clinical_data.view_model.importprocessor import ImportProcessor as ClinicalImportProcessor
from flaskr.graphing.graphs import Grapher
from flaskr.filewriter.writer import Writer
from flaskr.stats.statscode import Stats
from flaskr.framework.model.Io.xlsx_file import XLSXFile


research_blueprint = Blueprint('research', __name__, template_folder='templates', url_prefix='/research')


admin_login_required = require_access('admin')
user_login_required = require_access('user')
login_required = require_access('guest')


@research_blueprint.route('/')
@login_required
def home():
    dataset_collection = DatasetCollection()

    # clear any previously uploaded xlsx files
    for filename in os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')):
        XLSXFile(name=filename).delete()

    return render_template('home.html', datasets=dataset_collection)


@research_blueprint.route('/delete/<id>', methods=['DELETE'])
@login_required
def delete(id):
    processor = DeleteProcessor()
    response = processor.execute(id)
    if response.is_success():
        flash(response.get_message())
    return redirect(url_for('research.home'))


@research_blueprint.route('/upload', methods=['POST'])
@login_required
def upload():
    validator = ImportValidator(request)

    # validate inputs
    result = validator.execute()
    if not result.is_success():
        flash(result.get_message(), 'error')
        return redirect(url_for('research.home'))

    # upload file to mongo with default values.
    id = result.get_name()
    importer = ImportProcessor()
    found = importer.search(id)
    if found:
        processor = DeleteProcessor()
        response = processor.execute(id)

    if request.form.get('official_results'):
        id = result.get_name()[:9]
        importer = ClinicalImportProcessor()
        result = importer.update_results(id)
        if not result.is_success():
            flash(result.get_message())
            return redirect(url_for('research.home'))

        clinical_writer = ClinicalWriter(writer=None, dataset_id=id)
        memory_file = clinical_writer.output_results(id=id)
        if memory_file is not None:
            return send_file(memory_file,
                             attachment_filename=id[:9] + '_samples.zip',
                             as_attachment=True)
        return redirect(url_for('research.home'))
    else:
        response = importer.upload(id, request.form.get('official_results'))
        if not response.is_success():
            flash(response.get_message(), 'error')
            return redirect(url_for('research.home'))

    return redirect(url_for('.input', id=id))


@research_blueprint.route('/input/<id>', methods=['GET', 'POST'])
@login_required
def input(id):
    types = Collection().get_types()
    components = Collection().get_components()

    if request.method == 'POST':
        importer = ImportProcessor(request=request.form)
        found = importer.search(id)

        if not found:
            flash(id + " not found!", 'error')
            return redirect(url_for('research.home'))

        elif request.form.get("json"):
            response = importer.edit_existing()
            if not response.is_success():
                flash(response.get_message(), 'error')
                return redirect(url_for('research.home'))

        elif request.form.get('COVID default'):
            covid_results = importer.calculate_covid_default()

            memory_file = BytesIO()
            excelwriter = pd.ExcelWriter(memory_file, engine='xlsxwriter')
            writer = Writer(writer=excelwriter, dataset_id=id)
            response = writer.write_covid(covid_dict=covid_results)
            excelwriter.save()
            memory_file.seek(0)

            return send_file(memory_file,
                             attachment_filename='covid_summary' + '_' + id + '.xlsx',
                             as_attachment=True)

        return redirect(url_for('research.analysis', id=id))
    
    dataset_repository = Repository()
    exp = dataset_repository.get_by_id(id)
    wells = exp.get_well_collection()

    return render_template('inputs.html', id=id, types=types, components=components, upload=upload, experiment=exp.data, wells=wells)


@research_blueprint.route('/analysis/<id>', methods=['GET', 'POST'])
@login_required
def analysis(id, form=dict()):
    if request.method == 'POST':
        importer = ImportProcessor(id)
        importer.add_components(request)

    processor = Processor(form=form, dataset_id=id)
    response = processor.execute()
    if not response.is_success():
        flash('%s' % response.get_message(), 'error')
        current_app.logger.error("Error from processor with id %s " % id)
        return redirect(url_for('research.home'))

    results = processor.getStatistics()
    flash('Processed successfully in %s seconds' % response.get_message(), 'timing')
    return render_template('analysis.html', id=id, results=results)


@research_blueprint.route('/graphs/<id>/download', methods=['GET', 'POST'], endpoint='zip_download')
@research_blueprint.route('/graphs/<id>', methods=['GET', 'POST'])
@user_login_required
def graphs(id, features=None):
    if request.method == 'POST':
        features = request.form
    graphs = Grapher(dataset_id=id) \
        .execute(features=features)

    if request.form.get('valid'):
        dataset_repository = Repository()
        model = dataset_repository.get_by_id(id)
        model['is_valid'] = False
        dataset_repository.save(model)
        # TODO: this doesn't mark all wells as invalid, just the dataset

    if len(graphs) == 0:
        flash('Something went wrong with graphing', 'error')
        return redirect(url_for('research.analysis', id=id))

    if request.form.get('showmetadata'):
        dataset_repository = Repository()
        model = dataset_repository.get_by_id(id)
        for key in model.get_metadata():
            info = ": ".join([key, model.get_metadata()[key]])
            flash(info, 'information')

    if request.endpoint == 'research.zip_download':
        memory_file = download_graphs(id=id, graphs=graphs)
        return send_file(memory_file,
                         attachment_filename='output' + '_' + id + '.zip',
                         as_attachment=True)
    else:
        return render_template('graphs.html',
                               id=id,
                               graphs=graphs.values(),
                               features=request.form.to_dict())


def download_graphs(id, graphs):
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:

        for itemtitle in graphs.keys():
            data = zipfile.ZipInfo()
            data.filename = itemtitle
            zf.writestr(data, base64.decodebytes(graphs[itemtitle].encode('ascii')))

        io = BytesIO()
        title = id + '_output.xlsx'
        excelwriter = pd.ExcelWriter(title, engine='xlsxwriter')
        excelwriter.book.filename = io
        writer = Writer(writer=excelwriter, dataset_id=id)
        response = writer.writebook()
        if not response.is_success():
            current_app.logger.error("Error with excel writing information for id %s " % id)
            return render_template('analysis.html', id=id)
        excelwriter.save()
        io.seek(0)

        data = zipfile.ZipInfo()
        data.filename = title
        zf.writestr(data, io.getvalue())

    memory_file.seek(0)
    return memory_file


def download(id, function='', data=None):
    io = BytesIO()
    excelwriter = pd.ExcelWriter(io, engine='xlsxwriter')
    writer = Writer(writer=excelwriter, dataset_id=id)

    if function == 'write data':
        response = writer.writebook()
    elif function == 'write stats':
        response = writer.write_stats()

    if not response.is_success():
        current_app.logger.error("Error with excel writing information for id %s " % id)
        return render_template('analysis.html', id=id)

    excelwriter.save()
    io.seek(0)
    return io


@research_blueprint.route('/stats', methods=['GET', 'POST'])
@user_login_required
def stats():
    if request.method == 'POST':
        statclass = Stats()
        statclass.execute(request=request)

        return render_template('stats.html',
                               id='',
                               graphs=statclass.stat_urls.values(),
                               features=request.form.to_dict())

    return render_template('stats.html',
                           id='',
                           graphs=dict(),
                           features=dict())
