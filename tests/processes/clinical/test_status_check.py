from flaskr.clinical_data.sample_models.repository import Repository
from flaskr.clinical_data.sample_models.factory import Factory
from flaskr.clinical_data.view_model.importprocessor import ImportProcessor

importer = ImportProcessor()
repository = Repository()
factory = Factory()


def test_initialize_sample(client):
    short_name = importer.init_sample(id='test')
    assert not short_name.is_success()
    new_sample = importer.init_sample(id='A0000')
    assert new_sample.is_success()


def test_check_in(client):
    assert not importer.check_in_sample(factory.create(dict(fyr_id='A0000')))
    test_sample2 = factory.create(dict(fyr_id='A0000'))
    test_sample2['provider_id'] = 'test'
    test_sample2['sample_id1'] = 'test'
    test_sample2['status'] = 1
    repository.save(test_sample2)
    assert importer.check_in_sample(test_sample2)


def test_assign_rack(client):
    test_sample = factory.create(dict(fyr_id='A0001',
                                      status=0))
    assert not importer.assign_rack(test_sample, 1, 1).is_success()
    test_sample = factory.create(dict(fyr_id='A0001',
                                      status=1))
    assert not importer.assign_rack(test_sample, 1, 1).is_success()
    # test_sample = factory.create(dict(fyr_id='A0000',
    #                                   status=2,
    #                                   rack_id='1'))
    # assert not importer.assign_rack(test_sample, 1, 1).is_success()
    test_sample = factory.create(dict(fyr_id='A0001',
                                      status=2))
    assert importer.assign_rack(test_sample, 1, 1).is_success()


def test_add_results(client):
    repository.save(factory.create(dict(fyr_id='A0000',
                                        status=4)))
    result = dict(FYRID='A0000',
                  Report=0,
                  Targets=dict())
    assert importer.add_test_results('A0000', result)
    importer.manager.save()
    sample = repository.get_by_fyr_ID('A0000')
    assert sample['status'] == 5
    assert sample['date_tested'] is not None


def test_status_check_on_add_results(client):
    result = dict(FYRID='A0000',
                  Report=0,
                  Targets=dict())
    repository.save(factory.create(dict(fyr_id='A0000',
                                        status=5)))
    assert not importer.add_test_results('A0000', result)


def test_dont_add_control_results(app, client):
    repository.save(factory.create(dict(fyr_id='PC',
                                        status=3)))
    result = dict(FYRID='PC',
                  Report=0,
                  Targets=dict())
    assert not importer.add_test_results('PC', result)


# def test_add_results_to_incomplete_sample(app, client):
#     result = dict(FYRID='A0001',
#                   Report=0,
#                   Targets=dict())
#     test_sample = factory.create(dict(fyr_id='A0001',
#                                       status=2))
#     repository.save(test_sample)
#     assert not importer.add_test_results('A0001', result)
