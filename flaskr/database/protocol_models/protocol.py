
from flaskr.framework.abstract.abstract_model import AbstractModel


class Protocol(AbstractModel):
    def __init__(self, dataset_id=None, component_id=None, quantity=0, base_protocol=None):
        super().__init__()
        self['_id'] = None
        self['dataset_id'] = dataset_id
        self['component_id'] = component_id
        self['quantity'] = quantity
        self['base_protocol'] = base_protocol  # optional. Corresponds to an item in the base_protocol collection

    def get_name(self) -> str:
        return self['name']

    def get_base_protocol(self) -> str:
        return self['base_protocol']




