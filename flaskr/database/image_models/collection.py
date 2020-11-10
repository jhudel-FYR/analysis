from flaskr.database.image_models.factory import Factory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'image'

    def __init__(self):
        super().__init__(Factory())


