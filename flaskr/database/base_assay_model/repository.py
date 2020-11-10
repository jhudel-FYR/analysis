from flaskr.database.base_assay_model.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'base_assay'
    factory = Factory()

