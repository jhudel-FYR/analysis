from bson import ObjectId
import datetime

from flaskr.database.measurement_models.collection import Collection as MeasurementCollection
from flaskr.database.measurement_models.dataframe_collection import Collection as DataframeCollection
from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.database.protocol_models.collection import Collection as ProtocolCollection
from flaskr.database_static.component_models.collection import Collection as ComponentCollection


class Dataset(AbstractModel):
    measurement_collection = None
    component_collection = None

    def __init__(self):
        super().__init__()
        self['_id'] = ''
        self['is_valid'] = True
        self['date'] = None
        self['version'] = 2.0
        self['experiment'] = ''
        self['base'] = False
        self['cycle_length'] = 0
        self['metadata'] = dict()
        self['statistics'] = dict()

    def is_valid(self) -> bool:
        if self['is_valid'] is None:
            return self['is_valid']
        return True

    def get_experiment(self) -> []:
        return self['experiment']

    def get_metadata(self) -> []:
        return self['metadata']

    def get_stats(self) -> []:
        return self['statistics']

    def get_version(self) -> float:
        return self['version']

    def get_date(self) -> str:
        if self['date'] is None:
            return str(datetime.datetime.strptime(self['name'][:8], '%Y%m%d'))
        return self['date']

    def get_well_collection(self) -> MeasurementCollection:
        if self.measurement_collection is None:
            self.measurement_collection = MeasurementCollection()
            self.measurement_collection.add_filter('dataset_id', self.get_id())
        return self.measurement_collection

    def get_pd_well_collection(self):
        if self.measurement_collection is None:
            self.measurement_collection = DataframeCollection()
            self.measurement_collection.add_filter('dataset_id', self.get_id())
        return self.measurement_collection.to_df()

    def get_replicate_sets(self):
        if self.measurement_collection is None:
            self.measurement_collection = MeasurementCollection()
            self.measurement_collection.add_filter('dataset_id', self.get_id())
            self.measurement_collection.group_by(field='$replicate_id', group_name="wells", accumulator="$addToSet")
        return self.measurement_collection

    def get_component_collection(self) -> ProtocolCollection:
        if self.component_collection is None:
            self.component_collection = ProtocolCollection()
            self.component_collection.add_filter('dataset_id', self.get_id())
            # for item in self.component_collection:
                # TODO: get component name/unit from componentcollection
        return self.component_collection

    def get_well_count(self) -> int:
        """This should be added after the measures are imported"""
        try:
            return self['measure_count']
        except KeyError:
            return -1

