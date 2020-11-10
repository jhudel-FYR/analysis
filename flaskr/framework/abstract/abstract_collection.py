import json
from datetime import datetime
import pymongo
from bson import ObjectId

from flaskr import db
from flaskr.framework.abstract.abstract_factory import AbstractFactory
from flaskr.framework.exception import MissingCriticalProperty


class AbstractCollection:
    name = None

    def __init__(self, factory: AbstractFactory):
        self.filters = {}
        self.pipeline = []
        self.order = []
        self.cursor = None
        self.size = None
        self.factory = factory
        self.select = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model

    def add_filter(self, column, value, condition='$eq', logical='$and'):
        """conditions should be added as mongo operators @see https://docs.mongodb.com/manual/reference/operator/query/"""
        if condition is '$eq':
            filter = {column: value}
        else:
            filter = {column: {condition: value}}
        if logical in self.filters:
            self.filters[logical].append(filter)
        else:
            self.filters[logical] = [filter]
        self.size = None

    def group_by(self, field, group_name, accumulator, fields_to_keep='$$ROOT'):
        # PLEASE tell me there's a cleaner way to do this!
        # What I want:
        
        # aggregation = {
        #     '$GROUP': {
        #         "_id": field,
        #         [group_name]: {
        #             [accumulator]: fields_to_keep
        #         }
        #     }
        # }

        # What I got:
        deepest = {}
        deepest[accumulator] = fields_to_keep
        middle = dict(_id = field)
        middle[group_name] = deepest
        aggregation = {
            '$group': middle
        }

        self.pipeline.append(aggregation)

    def add_order(self, field, direction=pymongo.ASCENDING):
        if direction is not pymongo.DESCENDING:
            direction = pymongo.ASCENDING
        self.order.append((field, direction))

    def reset_order(self):
        self.order.clear()

    def get_size(self):
        """Return collection size with filters"""
        if self.size is None:
            self.size = self.find().count()
        return self.size

    def get_connection(self):
        if self.name is None:
            raise MissingCriticalProperty('"name" property not found')
        return db.get_db()[self.name]

    def find(self):
        if len(self.pipeline) > 0:
            self.pipeline = [{'$match': self.filters}] + self.pipeline
            cursor = self.get_connection().aggregate(self.pipeline)
        else:
            cursor = self.get_connection().find(self.filters, self.select)
        if len(self.order) > 0:
            cursor.sort(self.order)

        return cursor

    def add_select(self, column):
        if self.select is None:
            self.select = []
        self.select.append(column)

    def to_json(self):
        result = []
        for model in self:
            data = model.get_data()
            # convert object ids to strings
            for dataKey, dataValue in data.items():
                if type(dataValue) in [ObjectId, datetime]:
                    data[dataKey] = str(dataValue)
            result.append(model.get_data())
        return json.dumps(result)
