from flaskr.database_static.base_protocol_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'base_protocol'
    factory = Factory()


