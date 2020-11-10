from flaskr.clinical_data.sample_models.sample import Sample
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Sample:
        model = Sample()
        if data is not None:
            model.set_data(data)

        return model
