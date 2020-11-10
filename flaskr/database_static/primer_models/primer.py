
from flaskr.framework.abstract.abstract_model import AbstractModel


class Primer(AbstractModel):
    primer_collection = None

    def __init__(self):
        super().__init__()
        self['sequence'] = ''
        self['name'] = ''
        self['set_id'] = ''


    def get_name(self) -> str:
        return self['name']

    def get_sequence(self) -> str:
        return self['sequence']

    def get_set(self) -> str:
        return self['set_id']
