from flaskr.clinical_data.sample_models.sample import Sample
from flaskr.clinical_data.sample_models.repository import Repository


class Manager:
    buffer = []
    buffer_size = 1000

    def add(self, sample: Sample):
        self.buffer.append(sample)
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

    def update(self, sample: Sample):
        repository = Repository()
        repository.save(sample)
        self.buffer.clear()
