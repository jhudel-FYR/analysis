import os
import pandas as pd

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flaskr.framework.exception import InvalidArgument


class XLSXFile():
    FOLDER = 'excel'
    ALLOWED_EXTENSION = ['xlsx', 'xls', 'csv']
    name = ''
    file = None

    def __init__(self, file: FileStorage = None, name: str = ''):
        if file is not None and not self.is_allowed(file.filename):
            raise InvalidArgument('Only xlsx or csv files are allowed')
    
        # TODO: research alternatives to handle if file name has spaces (protocol files)
        # if file.filename != secure_filename(file.filename):
        #     raise InvalidArgument('Unsecure filename provided')

        if name == '':
            self.name = file.filename
            self.file = file
            self.save()
        else:
            self.name = name

    def is_allowed(self, filename: str) -> bool:
        allowed = True
        if '.' not in filename:
            allowed = False

        if filename.rsplit('.', 1)[1].lower() not in self.ALLOWED_EXTENSION:
            allowed = False

        return allowed

    def get_file_save_path(self) -> str:
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.FOLDER, self.name)

    def read(self, sheet: '', userows: bool = False, usecolumns: bool = False):
        self.error_count = 0
        if self.name.endswith('.xlsx'):
            raw = pd.ExcelFile(self.get_file_save_path())
            if sheet == '':
                sheets = raw.sheet_names
            else:
                sheets = [sheet]

            for sheet in sheets:
                sheetvalues = raw.parse(sheet).values
                [rows, columns] = sheetvalues.shape

                if usecolumns:
                    for column in range(columns):
                        if column < 2: #Skip the time column
                            continue
                        if self.is_invalid_line(sheetvalues[:, column]):
                            current_app.logger.warning('invalid line found for column %s', column)
                            continue

                        yield sheetvalues[:, column]

                elif userows:
                    for row in range(rows):
                        yield sheetvalues[row, :]


        elif self.name.endswith('.csv'):
            sheetvalues = pd.read_csv(self.get_file_save_path())

            [rows, columns] = sheetvalues.shape
            if usecolumns:
                for column in range(columns):
                    if column < 2:  # Skip the time column
                        continue
                    if self.is_invalid_line(sheetvalues[:, column]):
                        current_app.logger.warning('invalid line found for column %s', column)
                        continue
                    yield sheetvalues.loc[column]

            elif userows:
                for row in range(rows):
                    nonan = [i for i in list(sheetvalues.loc[row]) if pd.notnull(i)]
                    yield nonan

    def save(self):
        self.file.save(self.get_file_save_path())

    def delete(self):
        os.remove(self.get_file_save_path())

    def is_invalid_line(self, line) -> bool:
        if pd.isnull(line.any()):
            self.error_count += 1
            return True
        return False
