from bson import ObjectId

from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.framework.exception import MissingMeasures


class Image(AbstractModel):
    def __init__(self):
        super().__init__()
        self['dataset_id'] = None
        self['dataset_name'] = ''
        self['_id'] = None
        self['image'] = None
        self['class'] = ''
        self['training'] = False
        self['date'] = None
        self['label'] = ''

    def get_dataset_id(self) -> ObjectId:
        return self['dataset_id']

    def get_dataset_name(self) -> str:
        return self['dataset_name']

    def get_image(self) -> []:
        return self['image']

    def get_class(self) -> str:
        return self['class']

    def get_label(self) -> str:
        return self['label']

    def get_date(self) -> str:
        return self['date']

    def is_training(self) -> bool:
        return self['training']

