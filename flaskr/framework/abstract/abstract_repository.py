from bson import ObjectId

from flaskr import db
from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.framework.exception import MissingCriticalProperty, NoSuchEntityError, InvalidArgument


class AbstractRepository:
    name = None
    factory = None

    def __init__(self):
        if self.factory is None:
            raise MissingCriticalProperty('No factory was set to this repository')

    def get_connection(self):
        if self.name is None:
            raise MissingCriticalProperty('Repository is missing critical property "name"')
        return db.get_db()[self.name]

    def save(self, model: AbstractModel):
        if model.get_id() is None:
            model['_id'] = ObjectId()
            self.get_connection().insert_one(model.get_data())
        elif self.get_connection().find_one({'_id': model.get_id()}) is not None:
            self.get_connection().replace_one({'_id': model.get_id()}, model.get_data())
        else:
            self.get_connection().insert_one(model.get_data())

        return model

    def delete(self, model: AbstractModel):
        if model.get_id() is None:
            return
        self.get_connection().delete_one({'_id': model.get_id()})

    def get_by_id(self, id):
        """Find the document by the id string or ObjectId object"""
        if type(id) is not ObjectId and type(id) is not str:
            raise InvalidArgument('id must be str or bson.ObjectId')

        data = self.get_connection().find_one({'_id': id})
        if data is None:
            return None

        model = self.factory.create(data)
        return model

    def bulk_save(self, models: list):
        if len(models) == 0:
            return

        new_documents = []
        for model in models:
            if model.get_id() is None:
                new_documents.append({**model.get_data(), '_id': ObjectId()})
            else:
                self.get_connection().replace_one({'_id': model.get_id()}, model.get_data())

        if len(new_documents) > 0:
            self.get_connection().insert_many(new_documents)

    def delete_by_filter(self, filter: dict):
        self.get_connection().delete_many(filter)