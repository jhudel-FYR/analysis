from datetime import datetime

from flaskr.framework.abstract.abstract_model import AbstractModel

REPORT = {'-3': 'Not Yet Tested',
          '-2': 'Invalid',
          '-1': 'Inconclusive',
          '0': 'Not Detected',
          '1': '2019-nCoV detected'}
          # '1': 'Positive 2019-nCoV'}

INTERPRETATION = {'-2': 'Invalid Result',
                  '-1': 'Inconclusive Result',
                  '0': '2019-nCoV not detected',
                  '1': '2019-nCoV detected'}

SPECIMAN = {'NP': 'Nasal Pharyngeal',
            'AN': 'Anterior Nasal Swab',
            None: ''}

STATUS = {'Provider Assigned': 0,
          'Patient Assigned': 1,
          'Sample Returned': 2,
          'Rack Assigned': 3,
          'Experiment Initiated': 4,
          'Test Completed': 5}


class Sample(AbstractModel):
    sample_collection = None

    def __init__(self):
        super().__init__()
        self['_id'] = None
        self['fyr_id'] = None
        self['sample_id1'] = None
        self['id1_type'] = ''
        self['sample_id2'] = None
        self['id2_type'] = ''
        self['report'] = -3
        self['provider_id'] = ''
        self['date_collected'] = None
        self['date_received'] = None
        self['date_tested'] = None
        self['speciman_type'] = None
        self['test_type'] = ''
        self['dataset_id'] = None
        self['targets'] = None  # dict of target name: 0 if negative, 1 if positive
        self['invalid_plate'] = False
        self['status'] = 0
        self['rack_position'] = None
        self['rack_id'] = None

    def get_fyr_id(self) -> str:
        return self['fyr_id']

    def get_sample_id1(self) -> str:
        return self['sample_id1']

    def get_sample_id2(self) -> str:
        return self['sample_id2']

    def get_test_date(self) -> datetime:
        if self['date_tested'] is not None:
            return self['date_tested'].date()
        return self['date_tested']

    def get_date_collected(self) -> datetime:
        if self['date_collected'] is not None:
            return self['date_collected'].date()
        return self['date_collected']

    def get_targets(self) -> str:
        return self['targets']

    def get_report(self) -> str:
        return REPORT[str(self['report'])]

    def get_interpretation(self) -> str:
        return INTERPRETATION[str(self['report'])]

    def get_type(self) -> str:
        return self['test_type']

    def get_speciman_type(self) -> str:
        return SPECIMAN[self['speciman_type']]

    def get_provider(self) -> str:
        return self['provider_id']

    def get_rack(self) -> int:
        return self['rack_id']

    def get_rack_position(self) -> int:
        return self['rack_position']

    def get_status(self) -> str:
        for key in STATUS.keys():
            if STATUS[key] == self['status']:
                return key
        return ''
