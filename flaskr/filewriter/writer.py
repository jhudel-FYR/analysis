import pandas as pd
import numpy as np
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
        self.rowshift = 0
        self.columnshift = 0

    def write_covid(self, covid_dict):
        df = pd.DataFrame.from_dict(covid_dict)

        df.to_excel(self.writer, sheet_name='summary', index=False)
        self.stats_excel_formatting('summary', df)

        return Response(True, '')

    def write_stats(self):
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        df = dataset.get_pd_well_collection()

        df = covid_stats(df)

        df.to_excel(self.writer, sheet_name='summary', index=False)
        self.stats_excel_formatting('summary', df)

        return Response(True, '')

    def stats_excel_formatting(self, sheetname, df):
        worksheet = self.writer.sheets[sheetname]
        for idx, column in enumerate(df.columns):
            lengths = [len(x) for x in df.loc[:, column].astype('str')]
            lengths.append(len(column))
            maxlength = max(lengths)
            worksheet.set_column(idx, idx + 1, maxlength + 3)

    def writebook(self):
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        cycle = dataset['cycle_length']
        df = dataset.get_pd_well_collection()
        df = self.build_dataframe(df, cycle)
        number_of_groups = df['group'].max()
        if str(number_of_groups) == 'nan':
            number_of_groups = len(df)
        number_of_groups = int(number_of_groups) + 1


        # write individual variables of interest
        startindex = int(np.where(df.columns.str.startswith('Inflection '))[0][0])
        variablesofinterest = 4 * 3
        variablecolumns = [startindex + n for n in range(variablesofinterest)]
        variablecolumns.insert(0, 6)
        for group in range(number_of_groups):
            self.write_to_sheet('Inflections', df[(df['group'] == group)], variablecolumns)
            self.rowshift += df[(df['group'] == group)].shape[0] + 4

        # write averages of variables of interest
        self.rowshift = 0
        adf = self.build_averages(df)
        variablecolumns.pop(0)
        startindex = variablesofinterest + list(np.where(df.columns.str.startswith('Inflection ')))[0][0]
        for group in range(number_of_groups):
            columns = [n for n in variablecolumns]
            gdf = adf[(adf['group'] == group)]
            if len(gdf) == 0: continue
            # TODO: use this when control work is finished
            # control = gdf[gdf['is_control'] == 'True']
            control = gdf[gdf['replicate'] == gdf['replicate'].min()]
            for inf in range(4):
                columns.append(startindex+inf)
                inf_label = 'Inflection ' + str(inf + 1)
                if len(gdf) == 0 or len(control) == 0:
                    continue
                gdf.insert(int(startindex+inf), 'Difference from control ' + str(inf + 1), gdf[inf_label] - float(control[inf_label].mean()))
            gdf = gdf.iloc[:, columns]

            gdf.to_excel(self.writer, sheet_name='Averages', startrow=self.rowshift)
            self.excel_formatting('Averages', gdf, 0)
            self.rowshift += gdf.shape[0] + 4

        # write inflection and percent differences in matrices
        self.rowshift = 0
        for group in range(number_of_groups):
            gdf = adf[(adf['group'] == group)]
            pdf = adf[(adf['group'] == group)]
            for inf in range(4):
                no_control = False
                columns = []
                inf_label = 'Inflection ' + str(inf + 1)
                if len(gdf[inf_label]) == 0:
                    continue
                pcnt_label = 'Percent Diff ' + str(inf + 1)
                columns.append(6)
                for replicateA in gdf['replicate'].unique():
                    columns.append(len(gdf.columns))
                    rowA = gdf[gdf['replicate'] == replicateA]
                    if len(rowA) > 1:
                        no_control = True
                        break
                    gdf.insert(len(gdf.columns), str(len(columns) - 2) + ' ' + inf_label,
                               [label - float(rowA[inf_label]) if replicateB <= replicateA else 'nan'
                                for label, replicateB in zip(gdf[inf_label], gdf['replicate'])])
                    pdf.insert(len(pdf.columns), str(len(columns) - 2) + ' ' + pcnt_label,
                               [label - float(rowA[pcnt_label]) if replicateB >= replicateA else 'nan'
                                for label, replicateB in zip(pdf[pcnt_label], pdf['replicate'])])
                if not no_control:
                    spacedifferencematrices = (len(columns)+4) * inf
                    self.write_to_sheet('Inf Differences', gdf, columns, spacedifferencematrices)
                    self.write_to_sheet('Percent Differences', pdf, columns, spacedifferencematrices)
            self.rowshift += gdf.shape[0] + 4

        # write individual ct values
        self.rowshift = 0
        df.insert(0, 'Ct threshold', [x[1] for x in df['deltaCt']])
        df.insert(0, 'delta Ct', [x[0] for x in df['deltaCt']])
        variablecolumns = []
        for item in ['label', 'group', 'sample', 'Ct threshold', 'delta Ct']:
            variablecolumns.append(int(np.where(df.columns == item)[0]))
        for group in range(number_of_groups):
            self.write_to_sheet('Ct Thresholds', df[(df['group'] == group)], variablecolumns)
            self.rowshift += df[(df['group'] == group)].shape[0] + 4

        return Response(True, '')

    def build_dataframe(self, df, cycle):
        for i in range(len(df['RFUs'][0])):
            self.time.append(cycle)
        for inf in range(4):
            df['Inflection ' + str(inf + 1)] = [dict(x)[str(inf+1)] if dict(x).get(str(inf + 1)) else 0 for x in
                                        df['inflections']]
        for inf in range(4):
            df['Inflection RFU ' + str(inf + 1)] = [dict(x)[str(inf+1)] if dict(x).get(str(inf + 1)) else 0 for x in df['inflectionRFUs']]
        for inf in range(4):
            df['Percent Diff ' + str(inf + 1)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]
        return df

    def write_to_sheet(self, sheetname, df, columns, shiftcolumn=0):
        df = df.iloc[:, columns]
        df.to_excel(self.writer, sheet_name=sheetname,
                    startrow=self.rowshift, startcol=shiftcolumn)
        self.excel_formatting(sheetname, df, shiftcolumn)

    def excel_formatting(self, sheetname, df, startcolumn):
        worksheet = self.writer.sheets[sheetname]
        for idx, column in enumerate(df.columns):
            lengths = [len(x) for x in df.loc[:, column].astype('str')]
            lengths.append(len(column))
            maxlength = max(lengths)
            worksheet.set_column(startcolumn+idx, startcolumn+idx+1, maxlength)
        if sheetname == 'Ct Thresholds':
            worksheet.set_column(0, 0, 10)
            worksheet.set_column(1, 1, 30)
        elif sheetname != 'Inflections':
            worksheet.set_column(0, 0, 30)
        else:
            worksheet.set_column(0, 0, 10)

    def build_averages(self, df):
        adf = pd.DataFrame(columns=df.columns.tolist())
        sample_count = df['replicate'].max()
        if str(sample_count) == 'nan':
            sample_count = len(df['replicate'])
        for replicate in range(int(sample_count)+1):
            gdf = df[(df['replicate'] == replicate)].groupby('label').mean()
            adf = pd.concat([adf, gdf], sort=False)
        return adf
