import unittest
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.model.helpers.covidstats import validate_covid_default, run_covid_default


class covid_test:
    test_data = '../../data/99991231a_XX_TEST_INFO.xlsx'
    test_info = XLSXFile(name=test_data)
    covid_results = []

    def test_validation(self):
        for wellindex, info in enumerate(self.test_info.read(sheet='0', userows=True)):
            if not validate_covid_default(self, wellindex, info):
                assert False
        assert True

    def test_identification(self):
        for wellindex, info in enumerate(self.test_info.read(sheet='0', userows=True)):
            run_covid_default(self, wellindex, info)
            if self.covid_results[-1]['summary'] != 'N':
                if wellindex == 94:
                    assert True
                else:
                    assert False
        assert True
