from flask import flash

from flaskr.framework.exception import MethodNotImplemented
from flaskr.framework.model.request.response import Response
from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.database.dataset_models.repository import Repository
from flaskr.database_static.component_models.repository import Repository as ComponentRepository
from flaskr.database.protocol_models.factory import Factory as ProtocolFactory
from flaskr.database.protocol_models.manager import Manager as ProtocolManager
from flaskr.model.helpers.importfunctions import save_dataset_component, search_components


class AbstractImporter:
    dataset = None
    measurement_factory = MeasurementFactory()
    measurement_manager = MeasurementManager()
    component_repository = ComponentRepository()
    protocol_factory = ProtocolFactory()
    protocol_manager = ProtocolManager()

    def search(self, name) -> bool:
        dataset_repository = Repository()
        self.dataset = dataset_repository.get_by_id(name)
        if self.dataset is None:
            return False
        if self.dataset.get_well_count() == 0:
            dataset_repository.delete_by_filter({'name': name})
            return False
        return True

    def execute(self, index, well) -> Response:
        raise MethodNotImplemented

    def add_measurement(self, measurement):
        self.measurement_manager.add(measurement)

    def add_components(self, request):
        for key, value in request.form.items():
            if key.startswith('component'):
                component = value.split(' ')
                if len(component) < 4:
                    flash('Missing values', 'error')
                    continue
                name = component[1]
                quantity = component[2]
                unit = component[3]

                componentid = search_components(self, name=name, unit=unit)
                if not componentid.is_success():
                    flash(componentid.get_message())
                    # TODO: can add single component if needed (add_single_component())
                    break
                save_dataset_component(self,
                                       quantity=quantity,
                                       component_id=componentid.get_message())
        self.protocol_manager.save()
