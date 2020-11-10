
from flaskr.framework.abstract.abstract_model import AbstractModel


class BaseProtocol(AbstractModel):
    base_protocol_collection = None

    def __init__(self):
        super().__init__()
        self['_id'] = None
        self['name'] = ''
        self['component_id'] = ''
        self['concentration'] = 0
        self['version'] = 0 #TODO: is this going to be unique?

    def get_name(self) -> str:
        return self['name']

    def get_version(self) -> float:
        return self['version']

