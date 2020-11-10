from flask import flash
import re

from flaskr.database_static.base_protocol_models.factory import Factory
from flaskr.database_static.base_protocol_models.repository import Repository
from flaskr.database_static.component_models.repository import Repository as ComponentRepository
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response
from flaskr.model.helpers.calcfunctions import get_regex_response


class ImportBaseProtocols:
    def execute(self, request) -> Response:
        base_protocol_repository = Repository()
        component_repository = ComponentRepository()
        factory = Factory()

        for f in request.files:
            file = request.files.get(f)
            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                return Response(False, 'An invalid file was provided, please make sure you are uploading a .xlsx file')

        starthere = False
        for count, row in enumerate(xlsx_file.read(sheet='', userows=True)):
            if starthere:
                name = get_regex_response(str(row[1]), 'name')
                unit = get_regex_response(str(row[1]), 'unit')
                component = component_repository.get_by_name(name)
                if component is None or component.get_unit() != unit:
                    flash('%s was not found in the list of possible components' % row[1], 'error')
                    continue
                elif component.get_unit() != unit:
                    flash('%s is not a valid unit for: %s' % (component.get_unit(), component.get_name()), 'error')
                    continue
                else:
                    flash('%s was successfully imported' % row[1], 'success')
                model = factory.create({'name': xlsx_file.file.filename,
                                        'component_id': component.get_id(),
                                        'concentration': float(row[5])})
                base_protocol_repository.save(model)

            if str(row[1]) == 'Reagent':
                starthere = True
            elif str(row[1]) == 'Total Reaction Mix for Full Reaction Volume':
                break

        xlsx_file.delete()

        return Response(True, 'File imported successfully')

