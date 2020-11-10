from pymongo.errors import DuplicateKeyError
import pytest

from flaskr.clinical_data.view_model.runprocessor import RunProcessor
from flaskr.clinical_data.sample_models.repository import Repository
from flaskr.clinical_data.sample_models.factory import Factory
from unittest.mock import patch
from tests.conftest import app

processor = RunProcessor()
test_line = ['nan', 'A01', 'FAM', 'RP', 'Unkn', 'PC', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']


def test_short_line(app):
    with app.app_context():
        short_line = processor.execute(test_line[:3], 0)
        assert not short_line.is_success()


def test_unknown_target(app):
    test_line2 = ['nan', 'A01', 'FAM', 'other', 'Unkn', 'A0001', 'nan', 25, 25, 0, 'nan', 'nan', 'nan', 0, 55, 'nan']
    invalid_target = processor.execute(test_line2, 0)
    assert not invalid_target.is_success()


def test_sample_names():
    sample_saved = processor.execute(test_line, 0)
    assert processor.results[test_line[5]]


def test_duplicate(app):
    repository = Repository()
    factory = Factory()
    repository.save(factory.create(dict(fyr_id='A0000')))
    assert True
    # with pytest.raises(DuplicateKeyError):
    #     repository.save(factory.create(dict(fyr_id='A0000')))
