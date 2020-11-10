
from flaskr.framework.abstract.abstract_validator import AbstractValidator
from flaskr.framework.model.request.response import Response


class ImportValidator(AbstractValidator):
    def __init__(self, request):
        self.request = request          # flask request

    def execute(self) -> Response:
        if self.request.files is None:
            return Response(False, 'Files are required')

        for fieldname, file in self.request.files.items():
            if fieldname == 'fastafile':
                if file is None or file.filename == '':
                    return Response(False, 'A file is required')

            elif fieldname == 'primer_list' and not self.request.form.get('default_primers'):
                if file is None or file.filename == '':
                    return Response(False, 'A file is required')

        return Response(True, '')
