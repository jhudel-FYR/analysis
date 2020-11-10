import datetime
import os
from flask import flash, current_app

from flaskr.database.dataset_models.factory import Factory
from flaskr.database.dataset_models.repository import Repository
from flaskr.framework.abstract.abstract_importer import AbstractImporter
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response
from flaskr.model.helpers.calcfunctions import get_regex_response
from flaskr.model.helpers.covidstats import validate_covid_default, run_covid_default
from flaskr.model.helpers.buildfunctions import build_input_dicts, swap_wells, add_remaining_swaps, determine_labelling
from flaskr.model.helpers.importfunctions import get_existing_metadata, update_metadata


def getTime(t):
    time = datetime.datetime.strptime(t[:-4], '%m/%d/%Y %H:%M:%S')
    return time


def get_experiment_length(info):
    start = 0
    end = 0
    for row in info.read(sheet='Run Information', userows=True):
        if row[0] == 'Run Ended':
            end = getTime(row[1])
        if row[0] == 'Run Started':
            start = getTime(row[1])
    if start == 0 or end == 0:
        current_app.logger.error("Error retrieving experiment length")
    return (end - start).total_seconds()


class ImportProcessor(AbstractImporter):
    def __init__(self, request=None):
        self.id = dict(group=0, sample=0, replicate=0, replicate_id=None)
        self.previous = ''
        self.form = request
        self.errorwells = []
        self.swaps = {}
        self.swap_from = {}
        self.swap_to = {}
        self.groupings = {}
        self.covid_results = []
        self.replicates = {}
        self.groups = {}
        if self.form is not None and self.form.get("json"):
            build_input_dicts(self)

    def execute(self, wellindex, well, upload=False) -> Response:
        [well, changed] = determine_labelling(self, well, wellindex)

        # set well status to invalid if reported
        if well.get_excelheader() in self.errorwells:
            changed = True
            well['is_valid'] = False

        # swap wells
        if len(self.swaps) > 0 and \
                well.get_excelheader() in self.swaps or \
                well.get_excelheader() in self.swaps.values():
            well = swap_wells(self, well)
            if well is None:
                changed = False
                upload = False

        if changed or upload:
            self.add_measurement(well)

        return Response(True, '')

    def upload(self, id, official_results) -> Response:
        dataset_repository = Repository()
        if self.dataset is None:
            factory = Factory()
            model = factory.create({'_id': id,
                                    'version': float(current_app.config['VERSION']),
                                    'date': datetime.datetime.strptime(id[:8], '%Y%m%d')})
            dataset_repository.save(model)
            self.dataset = model

        infofile = None
        rfufile = None
        for filename in os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')):
            if filename.endswith('INFO.xlsx'):
                infofile = XLSXFile(name=filename)
            elif filename.endswith('RFU.xlsx'):
                rfufile = XLSXFile(name=filename)

        if infofile.get_file_save_path() is None or rfufile.get_file_save_path() is None:
            return Response(False, 'Unknown error, please upload file again.')

        experiment_length = get_experiment_length(infofile)

        wellindex = 0
        cycle_length = 0
        for info, rfu in zip(infofile.read(sheet='0', userows=True),
                             rfufile.read(sheet='SYBR', usecolumns=True)):
            if cycle_length == 0:
                cycle_length = experiment_length / len(rfu)
            self.execute(wellindex, self.create_well(info, rfu), upload=True)

            wellindex += 1

        add_remaining_swaps(self)
        self.measurement_manager.save()

        if official_results is None:
            infofile.delete()
        rfufile.delete()

        self.dataset['measure_count'] = self.dataset.get_well_collection().get_size()
        self.dataset['cycle_length'] = cycle_length
        dataset_repository.save(self.dataset)

        flash('File imported successfully with %s wells' % self.dataset['measure_count'], 'success')
        flash('Calculated cycle length was %s' % round(cycle_length, 3), 'success')

        self.send_error_messages()
        return Response(True, '')

    def edit_existing(self):
        if self.form.get('testing'):
            get_existing_metadata(self)
        else:
            update_metadata(self)
            # TODO: update how metadata is saved

        for wellindex, well in enumerate(self.dataset.get_well_collection()):
            self.execute(wellindex, well)

            # TODO: uncomment this when plate templates are set up
            if self.form.get('COVID default'):
                validate_covid_default(self, wellindex, well.get_cq())
                run_covid_default(self, wellindex, well)

        add_remaining_swaps(self)

        flash('Updated %s wells' % len(self.measurement_manager.buffer), 'success')
        self.measurement_manager.save()

        self.send_error_messages()
        return Response(True, '')

    def calculate_covid_default(self):
        total = self.dataset.get_well_count()
        for wellindex, well in enumerate(self.dataset.get_well_collection()):
            self.execute(wellindex, well)

            run_covid_default(self, wellindex, well, total_index=total)

        return self.covid_results

    def create_well(self, inforow, rfuvalues):
        concentration = get_regex_response(inforow[5], regextype='concentration')
        if str(inforow[7]) != 'nan':
            cq = float(inforow[7])
        else:
            cq = None

        data = {'dataset_id': self.dataset.get_id(),
                'excelheader': inforow[1],
                'label': str(inforow[5]) + '__' + str(inforow[6]),
                'label_history': ' '.join([label for label in inforow[1:7] if type(label) == str]),
                'concentration': concentration,
                'RFUs': [],
                'Cq': cq
                }

        measurement_model = self.measurement_factory.create(data)
        measurement_model.add_values(rfuvalues)
        return measurement_model

    def send_error_messages(self):
        if len(self.swaps) > 0:
            missing_swaps = ", ".join([item for item in self.swaps.keys()])
            flash('Swaps from wells %s could not occur, either an origin or destination well could not be found.'
                  % missing_swaps, 'error')
