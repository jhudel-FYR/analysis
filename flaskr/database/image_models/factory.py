from flaskr.database.image_models.images import Image
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Image:
        model = Image()
        if data is not None:
            model.set_data(data)

        return model
