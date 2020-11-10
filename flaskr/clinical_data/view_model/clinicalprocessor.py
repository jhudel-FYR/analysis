from flask import current_app
import os
import pandas as pd
import numpy as np

from flaskr.framework.model.request.response import Response
from flaskr.framework.model.Io.xlsx_file import XLSXFile


class ByPasser():
    def __init__(self):
        self.fdf = pd.DataFrame(columns=['FYR ID', 'Biological Set Name', 'N1', 'N2', 'RP', 'Result', 'Target Count',
                                         'Added to NUC', 'Reported', 'Initials'])

    def execute(self) -> Response:
        infofile = None
        for filename in os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')):
            if filename.endswith('INFO.xlsx'):
                infofile = XLSXFile(name=filename).get_file_save_path()

        if infofile is None:
            return Response(False, 'The file was not uploaded correctly')

        df = pd.read_excel(infofile)
        df['Sample'] = df['Sample'].str.upper()
        df['Sample'] = df['Sample'].replace('NTC', 'NFW', regex=True)
        df['Sample'] = df['Sample'].replace('POS', 'PC', regex=True)
        self.fdf['FYR ID'] = np.unique(df['Sample'].replace(np.nan, '', regex=True))
        self.fdf['Target Count'] = [0 for i in range(len(self.fdf['FYR ID']))]

        for x in range(len(df.index)):
            for y in range(len(self.fdf.index)):
                if self.fdf['FYR ID'].iloc[y] == df['Sample'].iloc[x]:
                    self.fdf['Biological Set Name'].iloc[y] = df['Biological Set Name'].iloc[x]
                    if df['Target'].iloc[x] == 'N1':
                        self.fdf['N1'].iloc[y] = df['Cq'].iloc[x]
                        if float(df['Cq'].iloc[x]) < 40 and df['Cq'].iloc[x] != 0.:
                            self.fdf['Target Count'].iloc[y] += 1
                    if df['Target'].iloc[x] == 'N2':
                        self.fdf['N2'].iloc[y] = df['Cq'].iloc[x]
                        if float(df['Cq'].iloc[x]) < 40 and df['Cq'].iloc[x] != 0.:
                            self.fdf['Target Count'].iloc[y] += 1
                    if df['Target'].iloc[x] == 'RP':
                        self.fdf['RP'].iloc[y] = df['Cq'].iloc[x]
                        if float(df['Cq'].iloc[x]) < 40 and df['Cq'].iloc[x] != 0.:
                            self.fdf['Target Count'].iloc[y] += 1

        for i in range(len(self.fdf.index)):
            if self.fdf['FYR ID'].iloc[i] == 'PC':
                if self.fdf['Target Count'].iloc[i] < 3:
                    self.fdf['Result'] = 'Invalid PC'
                    break
                else:
                    self.fdf['Result'].iloc[i] = 'PC Valid'
            elif self.fdf['FYR ID'].iloc[i] == 'NFW':
                if self.fdf['Target Count'].iloc[i] > 0:
                    self.fdf['Result'] = 'Invalid NFW'
                    break
                else:
                    self.fdf['Result'].iloc[i] = 'NTC Valid'
            elif not np.isnan(self.fdf['RP'].iloc[i]) and self.fdf['RP'].iloc[i] < 40. and self.fdf['RP'].iloc[i] != 0.:
                if self.fdf['FYR ID'].iloc[i] != 'NFW' and self.fdf['FYR ID'].iloc[i] != 'PC':
                    if not np.isnan(self.fdf['N1'].iloc[i]) and self.fdf['N1'].iloc[i] < 40. and self.fdf['N1'].iloc[i] != 0.:
                        if not np.isnan(self.fdf['N2'].iloc[i]) and self.fdf['N2'].iloc[i] < 40. and self.fdf['N2'].iloc[i] != 0.:
                            self.fdf['Result'].iloc[i] = 'Detected'
                        else:
                            self.fdf['Result'].iloc[i] = 'Inconclusive'
                    elif not np.isnan(self.fdf['N2'].iloc[i]) and self.fdf['N2'].iloc[i] < 40. and self.fdf['N2'].iloc[i] != 0.:
                        self.fdf['Result'].iloc[i] = 'Inconclusive'
                    else:
                        self.fdf['Result'].iloc[i] = 'Not Detected'

            elif not np.isnan(self.fdf['N1'].iloc[i]) and not np.isnan(self.fdf['N2'].iloc[i]) and self.fdf['N1'].iloc[i] < 40. and self.fdf['N2'].iloc[i] < 40. :
                self.fdf['Result'].iloc[i] = 'Detected'
            elif not np.isnan(self.fdf['N1'].iloc[i]) and self.fdf['N1'].iloc[i] < 40. or not np.isnan(self.fdf['N2'].iloc[i]) and self.fdf['N2'].iloc[i] < 40. :
                self.fdf['Result'].iloc[i] = 'Inconclusive'
            else:
                self.fdf['Result'].iloc[i] = 'Invalid'

        self.fdf = self.fdf.drop(columns=['Target Count'])
        self.fdf['N1'] = self.fdf['N1'].replace(np.nan, 'NA', regex=True)
        self.fdf['N2'] = self.fdf['N2'].replace(np.nan, 'NA', regex=True)
        self.fdf['RP'] = self.fdf['RP'].replace(np.nan, 'NA', regex=True)
        self.fdf = self.fdf.rename(columns={'FYR ID': 'Case #', 'Biological Set Name': 'Req #'})
        self.fdf = self.fdf.sort_values(by=['Result'])

        for filename in os.listdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'excel')):
            XLSXFile(name=filename).delete()

        return Response(True, '')
