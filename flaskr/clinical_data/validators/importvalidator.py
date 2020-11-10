
from flaskr.framework.abstract.abstract_validator import AbstractValidator
from flaskr.framework.model.request.response import Response
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.exception import InvalidArgument


def get_name(fieldname):
    split_name = fieldname.split('_')
    return split_name[0]


class ImportValidator(AbstractValidator):
    def __init__(self, request):
        self.request = request          # flask request
        self.name = ''

    def execute(self) -> Response:
        for file in self.request.files.getlist('files'):
            if file is None or file.filename == '':
                return Response(False, 'A file is required')

            if not file.filename.endswith('.xlsx'):
                if not file.filename.endswith('.csv'):
                    return Response(False, 'The file has an incorrect filetype')
            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                return Response(False,
                                'An invalid file was provided, please make sure you are uploading a .xlsx or .csv file')

            self.name = get_name(file.filename)

        return Response(True, '', self.name)
