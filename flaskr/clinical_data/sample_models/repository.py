from datetime import datetime

from flaskr.database.dataset import Dataset
from flaskr.clinical_data.sample_models import sample
from flaskr.clinical_data.sample_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'sample'
    factory = Factory()

    def delete_by_name(self, sample: sample):
        if sample.get_name() is None:
            return
        self.delete_by_filter({'name': sample.get_name()})

    def delete_by_dataset(self, dataset: Dataset):
        if dataset.get_id() is None:
            return
        self.delete_by_filter({'dataset_id': dataset.get_id()})

    def get_by_ids(self, id1='', id2=''):
        data = self.get_connection().find({'sample_id1': id1,
                                           'sample_id2': id2})
        if data is None:
            return None

        model = self.factory.create(data)
        return model

    def get_by_fyr_ID(self, id, status=None):
        if status is not None:
            data = self.get_connection().find_one({'fyr_id': id,
                                                   'status': status})
        else:
            data = self.get_connection().find_one({'fyr_id': id})

        if data is None:
            return None

        model = self.factory.create(data)
        return model