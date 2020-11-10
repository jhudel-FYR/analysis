from flaskr.database_static.primer_models.primer import Primer
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Primer:
        model = Primer()
        if data is not None:
            model.set_data(data)

        return model
