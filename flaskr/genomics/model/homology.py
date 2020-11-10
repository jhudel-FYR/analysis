import math as m
import numpy as np
import pandas as pd
from io import BytesIO
from flaskr.database_static.primer_models.factory import Factory
from flaskr.database_static.primer_models.repository import Repository


class Homology():
    def __init__(
            self,
    ):
        self.sequence = ''
        self.location = -1
        self.ignore_location = -1
        self.primer = ''
        self.reverse = False
        self.request = None

    def execute(self, request):
        repository = Repository()
        factory = Factory()
        self.request = request

        df = pd.read_csv(self.request.files['hittable'], names=['Query_Num', 'Organism', 'Percentage', 'Base_Pairs',
                                                                'A', 'B', 'C', 'D', 'E', 'F', 'G','H'])

        if self.request.form.get('primer_select') is not None:
            primname = self.request.form.get('primer_select')
            primer = repository.get_by_name(primname).get_sequence()
        else:
            primer = self.request.form.get('primerseq')
            primname = self.request.form.get('primername')
            if repository.get_by_name(primname) is None:
                new_primer = {'name': primname, 'sequence': primer}
                repository.save(factory.create(new_primer))

        wrd_sze = 0
        if self.request.form.get('wrd_sze'):
            wrd_sze = self.request.form['wrd_sze']

        orgs = {"AC_000017.1": "Human Adenovirus", "AE009949.1": "Streptococcus Pneumoniae",
                'BX571856.1': "Staphylococcus Aureus",
                'CP000672.1': 'Haemophilus Influenzae', 'CP015928.1': 'Legionella Pneumophila',
                'CP027540.1': 'Streptococcus Pneumoniae',
                'CP039772.1': 'Mycoplasma Pneumoniae', 'CP040804.1': 'Streptococcus Salivarius',
                'JQ241176.1': 'Human Parainfluenza Virus 4b',
                'KJ556336.1': 'MERS Coronavirus', 'KJ627437.1': 'Human Metapneumovirus',
                'KM190939.1': 'Human Parainfluenza Virus 2',
                'KX639498.1': 'Human ParainfluenzaVvirus 1', 'MH010446.1': 'Pneumocystis Jirovecii',
                'MH798556.1': 'Influenza A',
                'MK969560.1': 'Influenza B', 'NC_000962.3': 'Mycobacterium Tuberculosis',
                'NC_001472.1': 'Human Enterovirus B',
                'NC_001796.2': 'Human Parainfluenza Virus 3', 'NC_001803.1': 'Respiratory Synctyial Virus',
                'NC_002516.2': 'Pseudomonas Aeruginosa',
                'NC_002645.1': 'Human Coronavirus 229E', 'NC_004718.3': 'SARS Coronavirus Tor2',
                'NC_005043.1': 'Chlamydia Pneumoniae',
                'NC_005831.2': 'Human Coronavirus NL63', 'NC_006213.1': 'Human Coronavirus OC43',
                'NC_006577.2': 'Human Coronavirus HKU1',
                'NC_009996.1': 'Human Rhinovirus C', 'NC_018046.1': 'Candida Albicans',
                'NC_018518.1': 'Bordetella Pertussis',
                "NZ_CP035288.1": "Staphylococcus Epidermidis"}

        df = df.drop(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'], 1)

        df['Base_Pairs'] = df['Base_Pairs'].astype(float)
        df['Homology'] = df['Percentage'] * df['Base_Pairs'] / 100.
        df['Homology'] = [m.ceil(df['Homology'][i]) for i in range(0, len(df['Homology']))]
        df['Homology'] = df['Homology'].astype(float)
        df['Primer_Sze'] = len(primer)
        df['Homo_%'] = df['Homology'] / float(len(primer)) * 100.
        df['Organism_Name'] = [orgs[df['Organism'][idx]] for idx, title in enumerate(df['Organism'])]
        df['Prmr_Sq'] = primer
        df['Srch_Sze'] = wrd_sze

        mdf = pd.DataFrame()
        for name in np.unique(df['Organism']):
            tdf = df[df['Organism'] == name]
            mdf = pd.concat([mdf, tdf[tdf['Homo_%'] == np.max(tdf['Homo_%'])].head(1)], sort=False)
        mdf = mdf.drop(['Query_Num', 'Percentage', 'Base_Pairs'], 1)

        tdf = pd.DataFrame()
        for val in mdf['Homo_%']:
            fdf = pd.concat([tdf, mdf[mdf['Homo_%'] > 80.0]], sort=False)

        io = BytesIO()
        output_file = str(primname) + 'homology_results.xlsx'
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        mdf.to_excel(writer, sheet_name='Full_Results', index=False)
        fdf.to_excel(writer, sheet_name='Homologous_Results', index=False)
        writer.book.filename = io
        writer.save()
        io.seek(0)
        return io, primname
