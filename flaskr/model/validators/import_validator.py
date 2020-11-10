
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.abstract.abstract_validator import AbstractValidator
from flaskr.framework.model.request.response import Response


class ImportValidator(AbstractValidator):
    def __init__(self, request):
        self.name = ''                  # our unique ID
        self.request = request          # flask request
        self.filename = ''              # file-name
        self.file_info = {}             # the name broken down into parts

    def execute(self) -> Response:
        if self.request.files is None:
            return Response(False, 'Files are required')

        for fieldname, file in self.request.files.items():
            if fieldname == 'imagefile':
                if file.filename != '':
                    if not file.filename.endswith('.png') and not file.filename.endswith('.jpg'):
                        return Response(False, 'The file has an incorrect filetype')
                    break
                continue

            if file is None or file.filename == '':
                return Response(False, 'A file is required')

            if not file.filename.endswith('.xlsx'):
                return Response(False, 'The file has an incorrect filetype')

            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                return Response(False, 'An invalid file was provided, please make sure you are uploading a .xlsx file')

            self.filename = self.request.files.get('file1').filename
            [self.name, self.file_info] = self.build_name()
        
        return Response(True, '', self.name, self.file_info)

    def build_name(self):
        split_name = self.filename.split('_')
        info = dict(Date=split_name[0][:-1],
                    Id=split_name[0][-1],
                    Initials=split_name[1])
        if len(split_name) > 4:
            info['Other Info'] = split_name[2:-1][0]
        return [info['Date'] + info['Id'] + '_' + info['Initials'], info]
