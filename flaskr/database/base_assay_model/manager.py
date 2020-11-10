
from flaskr.database.base_assay_model.base_assay import BaseAssay
from flaskr.database.base_assay_model.repository import Repository


class Manager:
    buffer = []
    buffer_size = 1000

    def add(self, protocol: BaseAssay):
        self.buffer.append(protocol)
        if len(self.buffer) >= self.buffer_size:
            self.save()
            self.buffer.clear()

    def save(self):
        counter = 0
        batch = []
        repository = Repository()
        for model in self.buffer:
            if counter > self.buffer_size:
                repository.bulk_save(batch)

            batch.append(model)
            counter += 1

        repository.bulk_save(batch)
        self.buffer.clear()

    def update(self, measurement: BaseAssay):
        repository = Repository()
        repository.save(measurement)
        self.buffer.clear()