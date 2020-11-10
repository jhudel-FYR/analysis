import copy
import os
from bson import ObjectId
from flask import flash

from flaskr.framework.model.request.response import Response
from flaskr.database.dataset_models.collection import Collection as DatasetCollection
from flaskr.database.dataset_models.repository import Repository as DatasetRepository
from flaskr.database.dataset_models.factory import Factory as DatasetFactory
from flaskr.database.measurement_models.repository import Repository as WellRepository
from flaskr.database.measurement_models.collection import Collection as WellCollection


class DataFix:
    def execute(self, request) -> Response:
        dataset_repository = DatasetRepository()
        dataset_collection = DatasetCollection()
        well_repository = WellRepository()
        well_collection = WellCollection()
        factory = DatasetFactory()

        for well in well_collection:
            if well['replicate'] is None:
                well['replicate'] = well['triplicate']
                well['replicate_id'] = well['triplicate_id']
            well_repository.save(well)

        # folder = '/mnt/c/Users/c4sei/FYR Diagnostics/FYR-Database - Documents/FYR Lab Experiments - Montec'
        # files = []
        # names = []
        # for r, d, f in os.walk(folder):
        #     for file in f:
        #         if 'RFU.xlsx' in file:
        #             files.append(os.path.join(r, file))
        #             names.append(file[:12])

        # for name in names:
        #     if dataset_repository.get_by_id(name) is None:
        #         #TODO: upload here
        #         break

        # for dataset in dataset_collection:
        #     dataset_id = None
        #     if type(dataset.get_id()) is str and len(dataset.get_id()) < 18:
        #         dataset_repository.delete(dataset)
            # for idx, name in enumerate(names):
            #     if dataset.get_id() == name:
            #         print(name)
            #         raw = pd.ExcelFile(files[idx])
            #         sheetvalues = raw.parse('SYBR').values
            #         first_rfu = sheetvalues[0, 2]
            #         well_collection = WellCollection()
            #         well_collection.add_filter('excelheader', "A01")
            #         for item in well_collection:
            #             if item.get_rfus()[0] == first_rfu:
            #                 dataset_id = item.get_dataset_id()
            #                 print(dataset_id)
            #                 break
            #         if dataset_id is None:
            #             continue
            #         newdataset = copy.deepcopy(dataset.get_data())
            #         newdataset['_id'] = dataset_id
            #         dataset_repository.save(factory.create(newdataset))
            #         dataset_repository.delete(dataset)
            #         print('success: ', name)
            #         break

        return Response(True, 'File imported successfully')

