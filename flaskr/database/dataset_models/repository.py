from flaskr.database.dataset_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'dataset'
    factory = Factory()

    def get_empty(self, id):
        data = self.get_connection().find({'measurement_count': 0})
        emptydataset = None
        if data is not None:
            for dataset in data:
                if dataset.get_id().startswith(id):
                    emptydataset = data
                    break
                emptydataset = dataset

        model = self.factory.create(emptydataset)
        return model
