from flaskr.framework.exception import MissingMeasures
from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.database.protocol_models.collection import Collection as ProtocolCollection
from flaskr.database_static.component_models.collection import Collection as ComponentCollection



class Measurement(AbstractModel):
    component_collection = None

    def __init__(self, dataset_id=None, replicate_id=None, excelheader='', label='', label_history='', concentration='', group=0, sample=0,
                 replicate=0, RFUs=None):
        super().__init__()
        if RFUs is None:
            RFUs = []
        self['dataset_id'] = dataset_id
        self['excelheader'] = excelheader
        self['is_valid'] = True
        self['is_control'] = False
        self['concentration'] = concentration
        self['label'] = label
        self['label_history'] = label_history
        self['group'] = group
        self['sample'] = sample
        self['replicate'] = replicate
        self['replicate_id'] = replicate_id
        self['RFUs'] = RFUs
        self['thresholdCycle'] = 0
        self['thresholdRFU'] = 0
        self['inflections'] = []
        self['inflectionRFUs'] = []
        self['percentdiffs'] = [0 for x in range(4)]
        self['deltaCt'] = [0 for x in range(3)]
        self['Cq'] = None

    def edit_labels(self, labels: dict = None):
        for key in labels.keys():
            if self[key] is not None:
                self[key] = labels[key]

    def add_values(self, measures: dict = None):
        if measures is None:
            raise MissingMeasures('At least one measure is required')

        for value in measures:
            self['RFUs'].append(value)

    def is_valid(self) -> bool:
        return self['is_valid']

    def is_control(self) -> bool:
        return self['is_control']

    def has_output(self) -> bool:
        if len(self['inflections']) == 0:
            return False
        return True

    def get_excelheader(self) -> '':
        return self['excelheader']

    def get_cycle(self) -> float:
        return self['cycle_length']

    def get_label(self) -> '':
        return self['label']

    def get_label_history(self) -> '':
        return self['label_history']

    def get_concentration(self) -> str:
        return self['concentration']

    def get_group(self) -> int:
        return self['group']

    def get_sample(self) -> int:
        return self['sample']

    def get_replicate(self) -> int:
        return self['replicate']

    def get_replicate_id(self) -> int:
        return self['replicate_id']

    def get_inflections(self) -> list:
        return self['inflections']

    def get_inflectionrfus(self) -> list:
        return self['inflectionRFUs']

    def get_delta_ct(self) -> float:
        return self['deltaCt'][0]

    def get_ct_threshold(self) -> float:
        return self['deltaCt'][1]

    def get_percentdiffs(self) -> list:
        return self['percentdiffs']

    def get_rfus(self) -> list:
        return self['RFUs']

    def get_dataset_id(self) -> float:
        return self['dataset_id']

    def get_cq(self) -> float:
        return self['Cq']

    def get_component_collection(self) -> ProtocolCollection:
            if self.component_collection is None:
                self.component_collection = ProtocolCollection()
                self.component_collection.add_filter('replicate_id', self['replicate_id'])
                # for item in self.component_collection:
                    # TODO: get component name/unit from componentcollection
            return self.component_collection

    def get_threshold(self):
        if self['thresholdCycle'] is None:
            return 0
        return self['thresholdCycle']
