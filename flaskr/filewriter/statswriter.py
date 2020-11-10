import pandas as pd
from flaskr.framework.model.request.response import Response

from flaskr.database.dataset_models.repository import Repository
from flaskr.model.helpers.covidstats import covid_stats


class Writer:
    def __init__(self,
                 writer,
                 dataset_id: str):
        self.writer = writer
        self.dataset_id = dataset_id
        self.time = []
        self.workbook = None

    def writebook(self):
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()

        df = covid_stats(df)

        df.to_excel(self.writer, sheet_name='summary', index=False)
        self.excel_formatting('summary', df)

        return Response(True, '')

    def excel_formatting(self, sheetname, df):
        worksheet = self.writer.sheets[sheetname]
        for idx, column in enumerate(df.columns):
            lengths = [len(x) for x in df.loc[:, column].astype('str')]
            lengths.append(len(column))
            maxlength = max(lengths)
            worksheet.set_column(idx, idx + 1, maxlength + 3)
