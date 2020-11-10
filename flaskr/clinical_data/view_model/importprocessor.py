from datetime import datetime
import os
from flask import current_app, flash

from flaskr.framework.abstract.abstract_importer import AbstractImporter
from flaskr.framework.model.request.response import Response
from flaskr.clinical_data.sample_models.sample import Sample
from flaskr.clinical_data.sample_models.repository import Repository
from flaskr.clinical_data.sample_models.collection import Collection
from flaskr.clinical_data.sample_models.factory import Factory
from flaskr.clinical_data.sample_models.manager import Manager
from flaskr.clinical_data.view_model.runprocessor import RunProcessor
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.clinical_data.sample_models.collection import Collection as SampleCollection


class ImportProcessor(AbstractImporter):
    def __init__(self):
        self.repository = Repository()
        self.manager = Manager()
        self.factory = Factory()
        self.dataset_id = None
        self.date_collected = datetime.today()
        self.date_received = datetime.today()
        self.date_tested = datetime.today()
        self.type = ''
        self.result_ids = []
        self.invalid_plate = False
        self.id1_type = None
        self.id2_type = None
        self.provider_id = ''

    def update_results(self, id) -> Response:
        self.dataset_id = id
        self.type = 'FYR Diagnostics SARS-nCoV-19 Diagnostics Panel'
        processor = RunProcessor()

        infofile = None
        for filename in os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')):
            if filename.endswith('INFO.xlsx'):
                infofile = XLSXFile(name=filename)
            else:
                XLSXFile(name=filename).delete()

        if infofile is None:
            return Response(False, 'File was not found')

        for index, row in enumerate(infofile.read(sheet='0', userows=True)):
            response = processor.execute(row, index)
            if processor.cdc_test:
                self.type = 'CDC 2019-nCoV Real-Time RT-PCR Diagnostic Panel'
            if not response.is_success():
                self.invalid_plate = True
                flash(response.get_message(), 'error')

        for sample_id, sample_values in processor.results.items():
            self.add_test_results(sample_id, sample_values)

        self.manager.save()

        infofile.delete()
        return Response(True, '')

    def add_test_results(self, sample_id, result):
        # Don't save the NFW, 0cps, or PC samples
        if sample_id.strip() in ['NTC', 'NFW', 'PC', '0cp', '0cps']:
            return False

        sample = self.repository.get_by_fyr_ID(result['FYRID'])
        if sample is None:
            if result['FYRID'].startswith('Z0000'):
                # testing data
                sample = self.factory.create(dict(fyr_id=result['FYRID'] + '.' + self.dataset_id,
                                                  sample_id1='test',
                                                  id1_type='test',
                                                  sample_id2='test',
                                                  id2_type='test',
                                                  provider_id='test',
                                                  date_collected=datetime.today(),
                                                  date_received=datetime.today()))
            else:
                current_app.logger.warning(
                    'Sample %s has a status that is not ready for test results' % result['FYRID'])
                return False
        # if sample['status'] < 4:
        #     flash('Sample %s has a status that is not ready for test results' % result['FYRID'], 'error')
            # current_app.logger.warning('Sample %s has a status that is not ready for test results' % result['FYRID'])
            # return False
        if sample['status'] > 4:
            # flash('Test results have already been recorded for sample %s' % result['FYRID'], 'error')
            current_app.logger.warning('Test results have already been recorded for sample %s' % result['FYRID'])
            return False
        sample['date_tested'] = datetime.today()
        sample['report'] = result['Report']
        sample['dataset_id'] = self.dataset_id
        sample['targets'] = result['Targets']
        sample['invalid_plate'] = self.invalid_plate
        sample['test_type'] = self.type
        sample['status'] = 5
        self.manager.add(sample)
        return True

    def init_sample(self, id) -> Response:
        if len(id) == 5:
            sample = self.factory.create(dict(fyr_id=id))
            self.repository.save(sample)
            return Response(True, '')
        else:
            return Response(False, 'Please check the ID, it looks too short')

    def check_in_sample(self, sample) -> bool:
        if sample.get_status() == 'Patient Assigned':
            sample['status'] += 1
            sample['date_received'] = datetime.today()
            return True
        return False

    def assign_rack(self, sample, rack, position) -> Response:
        if sample['status'] < 2:
            return Response(False, 'Sample has not been checked in yet.')

        if sample['rack_position'] is not None and str(sample['rack_position']) != '0':
            if sample['rack_id'] is not None and str(sample['rack_position']) != '0':
                return Response(False, 'Sample was already assigned to a rack.')

        sample['rack_id'] = rack
        sample['rack_position'] = position
        sample['status'] = 3
        self.repository.save(sample)
        return Response(True, '')

    def init_samples(self):
        reported_sample_file = None

        for filename in os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')):
            if filename.endswith('.xlsx'):
                reported_sample_file = XLSXFile(name=filename)

        if reported_sample_file is None:
            return Response(False, 'File was not uploaded')


        self.provider_id = 'Unknown'
        sample_start = False
        for index, row in enumerate(reported_sample_file.read(sheet='', userows=True)):
            row = [str(item) for item in row]
            if len(row) < 3:
                continue
            if sample_start:
                self.add_sample_IDs(row)
            if row[2].startswith('Provider ID'):
                self.provider_id = row[3]
            if row[0].startswith('Date of Delivery'):
                self.date_collected = datetime.strptime(row[1], '%Y%m%d')
            if row[0] == 'FYR Tube ID':
                self.id1_type = 'Primary'
                self.id2_type = 'Secondary'
                sample_start = True
        self.manager.save()

        reported_sample_file.delete()
        return Response(True, self.provider_id)

    def add_sample_IDs(self, row):
        # When tube is initialized, there should be an entry found, else flash error
        if self.repository.get_by_fyr_ID(row[0], status=0) is not None:
            # TODO: dont do this in production
            self.repository.delete_by_filter({'fyr_id': row[0]})
            flash('A tube already exists with fyr id %s' % row[0], 'error')
        sample = self.factory.create(dict(fyr_id=row[0],
                                          sample_id1=row[1],
                                          id1_type=self.id1_type,
                                          sample_id2=row[2],
                                          id2_type=self.id2_type,
                                          provider_id=self.provider_id,
                                          date_collected=self.date_collected,
                                          date_received=datetime.today(),
                                          speciman_type=row[3]))
        self.manager.add(sample)

    def init_tube(self, fyr_id):
        tube = self.factory.create(dict(fyr_id=fyr_id))
        self.manager.add(tube)
