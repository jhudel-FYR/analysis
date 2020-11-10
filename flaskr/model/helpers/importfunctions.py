from flask import current_app
from flaskr.framework.model.request.response import Response
from flaskr.database.dataset_models.repository import Repository
from flaskr.database_static.component_models.factory import Factory as ComponentFactory


def get_collection(self):
    dataset_repository = Repository()
    dataset = dataset_repository.get_by_id(self.dataset_id)
    return dataset.get_well_collection()


def get_existing_metadata(self):
    self.form = dict(form=dict())
    self.form = self.dataset.get_metadata()


def update_metadata(self):
    self.dataset['metadata'] = self.form
    self.dataset['experiment'] = self.form['exp_type']
    if self.form.get('base-assay'):
        self.dataset['base'] = True
    if self.dataset.get_version() < float(current_app.config['VERSION']):
        self.dataset['version'] = float(current_app.config['VERSION'])


def save_dataset_component(self, quantity, component_id):
    data = {'dataset_id': self.dataset_get_id(),
            'component_id': component_id,
            'quantity': quantity}
    #TODO: convert all to pM units?
    protocol = self.protocol_factory.create(data)
    self.protocol_manager.add(protocol)


def add_single_component(self, name, unit):
    factory = ComponentFactory()
    model = factory.create({'type': 'Target', 'name': name, 'unit': unit})
    self.component_repository.save(model)


def search_components(self, name, unit):
    component = self.component_repository.search_by_name_and_unit(name, unit)
    if component is not None:
        return Response(True, component['_id'])
    return Response(False, 'Target does not exist in the component library.')
    # TODO: Should the target be automatically added if it isn't found
    # add_component(self, name=name, unit=unit)
    # return Response(True, self.component_repository.search_by_name_and_unit(name, unit)['_id'])
