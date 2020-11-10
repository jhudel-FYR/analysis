
from flaskr.framework.abstract.abstract_model import AbstractModel


class BaseAssay(AbstractModel):

    def __init__(self, dataset_name='', date=None, target=''):
        super().__init__()
        self['_id'] = None
        self['name'] = dataset_name
        self['date'] = date
        self['target'] = target

    def get_name(self) -> str:
        return self['name']

    def get_date(self) -> str:
        return self['date']

    def get_target(self) -> str:
        return self['target']



