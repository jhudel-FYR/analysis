from flaskr.database.dataset_models.repository import Repository
from flaskr.database.measurement_models.repository import Repository as MeasurementRepository
from flaskr.clinical_data.sample_models.repository import Repository as SampleRepository
from flaskr.framework.model.request.response import Response


class DeleteProcessor:
    def execute(self, id) -> Response:
        dataset_repository = Repository()
        measurement_repository = MeasurementRepository()
        sample_repository = SampleRepository()

        dataset = dataset_repository.get_by_id(id)
        if dataset is None:
            dataset = dataset_repository.get_empty(id)

        measurement_repository.delete_by_dataset(dataset)
        sample_repository.delete_by_dataset(dataset)
        dataset_repository.delete(dataset)

        return Response(True, 'Dataset %s removed successfully' % id)
