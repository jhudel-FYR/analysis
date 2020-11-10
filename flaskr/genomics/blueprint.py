from flask import send_file, current_app
import os

from flaskr.genomics.validators.import_validator import ImportValidator
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flaskr.auth.blueprint import login_required
from flaskr.genomics.model.searcher import Searcher
from flaskr.genomics.model.blastn import Blaster
from flaskr.genomics.model.homology import Homology
from flaskr.genomics.model.designer import Designer
from flaskr.database_static.primer_models.collection import Collection

genomics_blueprint = Blueprint('genomics', __name__, template_folder='templates', url_prefix='/genomics')


@genomics_blueprint.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    collection = Collection()
    return render_template('genomics_home.html', primers=collection)


@genomics_blueprint.route('/sequence_search', methods=['GET', 'POST'])
@login_required
def sequence_search():
    if request.method == "POST":
        validator = ImportValidator(request)
        response = validator.execute()
        if not response.is_success():
            flash(response.get_message(), 'error')
            return redirect(url_for('genomics.home'))

        processor = Searcher()
        results = processor.execute(request)

        if results is None:
            return redirect(url_for('genomics.home'))

        try:
            output_filename = os.path.join(current_app.config['DOWNLOAD_FOLDER'], 'results.txt')
            with open(output_filename, 'w') as f:
                for item in results:
                    f.write('%s\n' % item)
            return send_file(output_filename,
                             attachment_filename='results.txt',
                             as_attachment=True)
        except Exception as e:
            flash(str(e), 'error')

        return redirect(url_for('genomics.home'))

    return redirect(url_for('genomics.home'))


@genomics_blueprint.route('/cross_reactivity', methods=['GET', 'POST'])
@login_required
def cross_reactivity():
    if request.method == "POST":
        processor = Blaster()
        results = processor.execute(request)

        if results is None:
            return redirect(url_for('genomics.home'))

        try:
            return send_file(results,
                             attachment_filename='results.zip',
                             as_attachment=True)

        except Exception as e:
            flash(str(e), 'error')

        return redirect(url_for('genomics.home'))

    return redirect(url_for('genomics.home'))


@genomics_blueprint.route('/design', methods=['GET', 'POST'])
@login_required
def design():
    if request.method == 'POST':
        validator = ImportValidator(request)
        response = validator.execute()
        if not response.is_success():
            flash(response.get_message(), 'error')
            return render_template('design.html')

        designer = Designer()
        response = designer.execute(request)
        if not response.is_success():
            flash(response.get_message(), 'error')
            return render_template('design.html')

        return render_template('design.html',
                               results=designer.primer_sequences,
                               topstrand=designer.sequence,
                               bottomstrand=designer.complement)

    return render_template('design.html')


@genomics_blueprint.route('/BLAST_analyzer', methods=['GET', 'POST'])
@login_required
def BLAST_analyzer():
    if request.method == "POST":
        processor = Homology()
        results, primname = processor.execute(request)

        if results is None:
            return redirect(url_for('genomics.home'))

        try:
            return send_file(results,
                             attachment_filename= str(primname) + '_BLAST_homology.xlsx',
                             as_attachment=True)
        except Exception as e:
            flash(str(e), 'error')

    return redirect(url_for('genomics.home'))