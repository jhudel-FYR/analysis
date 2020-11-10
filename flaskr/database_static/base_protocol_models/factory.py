from flaskr.database_static.base_protocol_models.baseprotocol import BaseProtocol
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> BaseProtocol:
        model = BaseProtocol()
        if data is not None:
            model.set_data(data)

        return model
