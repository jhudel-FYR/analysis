from flaskr.database.base_assay_model.factory import Factory
from flaskr.database.base_assay_model.repository import Repository
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response


class ImportBaseAssays:
    def execute(self, request) -> Response:
        assay_repository = Repository()
        factory = Factory()

        for f in request.files:
            file = request.files.get(f)
            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                return Response(False, 'An invalid file was provided, please make sure you are uploading a .xlsx file')

        for row in xlsx_file.read(sheet='', userows=True):
            model = factory.create({'name': row[1],
                                    'date': row[1][:8],
                                    'target': row[2]})
            assay_repository.save(model)

        xlsx_file.delete()

        return Response(True, 'File imported successfully')
