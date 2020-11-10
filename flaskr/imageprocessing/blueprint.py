from flask import render_template, session, redirect, url_for, request, flash, Blueprint
from flaskr.auth.blueprint import login_required
from flaskr.imageprocessing.model.imageprocessor import ImageProcessor
from flaskr.imageprocessing.model.analyzer import Analyzer
from flaskr.imageprocessing.model.editor import Editor

image_blueprint = Blueprint('image', __name__, template_folder='templates', url_prefix='/image')


@image_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return render_template('image_home.html')


@image_blueprint.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.files.get('imagefile'):
        #TODO: add validation
        # TODO: only upload once
        processor = ImageProcessor(request=request)
        response = processor.execute()

        if not response.is_success():
            flash(response.get_message(), 'error')

        return render_template('images.html',
                               name=response.get_name(),
                               id=processor.dataset_id,
                               results=processor.results.values()) #[idx, color, graph]

    return redirect(url_for('image.home'))


@image_blueprint.route('/edit/<name>/<id>', methods=['GET', 'POST'])
@login_required
def edit(name, id):
    if request.method == 'POST':
        # TODO: edit the image labels, delete invalid
        editor = Editor(id)
        response = editor.execute(request)

        if not response.is_success():
            flash(response.get_message(), 'error')
            return redirect(url_for('research.home'))

        flash('Editted successfully', 'success')
        return render_template('images.html',
                               name=name,
                               id=id,
                               results=editor.results.values())
    return render_template('images.html',
                           name=name,
                           id=id,
                           results=dict().values())


@image_blueprint.route('/analysis')
@login_required
def analysis():
    analyzer = Analyzer()
    analyzer.execute()

    return render_template('results.html', results=analyzer.results)
