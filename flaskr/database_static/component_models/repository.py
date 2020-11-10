from flaskr.database_static.component_models import component
from flaskr.database_static.component_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'component'
    factory = Factory()

    def delete_by_name(self, component: component):
        if component.get_name() or component.get_unit() is None:
            return
        self.delete_by_filter({'name': component.get_name(),
                               'unit': component.get_unit()})

    def search_by_name_and_unit(self, name: str, unit: str):
        data = self.get_connection().find_one({'name': name, 'unit': unit})
        if data is None:
            return None
        model = self.factory.create(data)
        return model

    def get_by_name(self, name: str, unit=None):
        if unit is not None:
            data = self.get_connection().find_one({'name': name, 'unit': unit})
        else:
            data = self.get_connection().find_one({'name': name})
        if data is None:
            return None
        model = self.factory.create(data)
        return model
