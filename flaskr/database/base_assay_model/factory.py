from flaskr.database.base_assay_model.base_assay import BaseAssay
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> BaseAssay:
        model = BaseAssay()
        if data is not None:
            model.set_data(data)

        return model
