from flask import flash, current_app

from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.framework.model.request.response import Response


def get_cdc_name(name):
    if name == 'N1':
        return '2019 nCoV_N1'
    elif name == 'N2':
        return '2019 nCoV_N2'
    elif name == 'E':
        return 'E gene'
    elif name == 'R':
        return 'RdRp'
    elif name == 'B':
        return 'Beta-Actin'
    else:
        return name


class RunProcessor(AbstractProcessor):
    def __init__(self):
        self.row = None
        self.positive_count = 0
        self.results = []
        self.results = dict()
        self.ct_threshold = 30
        self.target_count = 3
        self.cdc_test = False
        self.sample_count = 0

    def execute(self, row, index) -> Response:
        if len(row) < 5:
            current_app.logger.warning('Invalid row length %s' % str(len(row)))
            return Response(False, 'Invalid row length %s' % str(len(row)))

        self.row = row
        self.sample_id = str(row[5])
        if self.sample_id == 'Z0000':
            self.sample_id = self.sample_id + '-' + str(self.sample_count)

        # CDC test values:
        if index == 0:
            if self.row[3] in ['N1', 'N2', 'RP']:
                self.cdc_test = True
                self.ct_threshold = 40
            else:
                current_app.logger.warning('Invalid entry in INFO row: %s (expecting N1, N2, or RP)' % self.row[3])
                return Response(False, 'Invalid entry in INFO row: %s (expecting N1, N2, or RP)' % self.row[3])

        if self.results.get(self.sample_id) is None:
            self.results[self.sample_id] = dict(FYRID=self.sample_id,
                                                Report=-3,
                                                Targets=dict())

        self.check_sample(self.row[3])

        if len(self.results[self.sample_id]['Targets']) == self.target_count:
            if 'PC' in self.sample_id.strip():
                for target_name, target_ct in self.results[self.sample_id]['Targets'].items():
                    if target_ct == 0:
                        return Response(False, 'Positive control target %s did not return positive' % target_name)
            elif 'NFW' in self.sample_id.strip() or 'NTC' in self.sample_id.strip():
                for target_name, target_ct in self.results[self.sample_id]['Targets'].items():
                    if 0 < target_ct < self.ct_threshold:
                        return Response(False, 'Negative control target %s returned positive' % target_name)

            else:
                self.sample_count += 1
                if not self.get_interpretation():
                    return Response(False, 'Incorrect number of targets in sample %s, '
                                           'please verify that this plate is valid' % self.sample_id)

        elif str(row[5]) != 'Z0000' and len(self.results[self.sample_id]['Targets']) > self.target_count:
            return Response(False, 'A sample with more than %s targets was found, please check your file.'
                            % self.target_count)

        return Response(True, '')

    def check_sample(self, name):
        if self.results[self.sample_id]['Targets'].get(name):
            flash('%s target has duplicates in sample %s' % (name, self.sample_id), 'error')
        if float(self.row[7]) < self.ct_threshold:
            self.results[self.sample_id]['Targets'][get_cdc_name(name)] = round(self.row[7], 2)
        else:
            self.results[self.sample_id]['Targets'][get_cdc_name(name)] = 0
        return

    def get_interpretation(self):
        pos_extraction = False
        pos_target_count = 0

        if len(self.results[self.sample_id]['Targets'].items()) != self.target_count:
            return False

        for target_name, target_ct in self.results[self.sample_id]['Targets'].items():
            if 0 < target_ct < self.ct_threshold:
                if target_name in ['B', 'RP']:
                    pos_extraction = True
                else:
                    pos_target_count += 1

        if pos_target_count == self.target_count - 1:
            self.results[self.sample_id]['Report'] = 1
        elif 0 < pos_target_count < self.target_count - 1:
            if self.cdc_test:
                self.results[self.sample_id]['Report'] = -1
            else:
                self.results[self.sample_id]['Report'] = 1
        elif pos_target_count == 0 and pos_extraction:
            self.results[self.sample_id]['Report'] = 0
        else:
            self.results[self.sample_id]['Report'] = -2

        return True
