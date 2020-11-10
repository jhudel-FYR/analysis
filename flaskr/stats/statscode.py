import pandas as pd
from datetime import date
from flask import flash
import numpy as np
import time
import scipy.stats as stats
from scipy.stats import kstest, shapiro

from flaskr.database.base_assay_model.collection import Collection as BaseAssayCollection
from flaskr.database.dataset_models.repository import Repository as DatasetRepository
from flaskr.database.dataset_models.collection import Collection as DatasetCollection
from flaskr.database.measurement_models.collection import Collection as MeasurementCollection
from flaskr.database.measurement_models.repository import Repository as MeasurementRepository
from flaskr.model.helpers.calcfunctions import get_regex_response
from flaskr.stats.statplot import StatPlotter


class Stats:
    def __init__(self, id=''):
        self.dataset_ids = []
        self.current_dataset = id
        self.stat_urls = {}
        self.dataframe = None

    def execute(self, request):
        dataset_collection = DatasetCollection()
        repository_instance = DatasetRepository()

        if self.current_dataset != '':
            self.dataset_ids.append(self.current_dataset)

        if request.form.get('base') == 'base':
            base_assay_collection = BaseAssayCollection()
            for assay in base_assay_collection:
                if assay.get_target() == request.form.get('tar_type'):
                    self.dataset_ids.append(assay.get_name())
                else:
                    continue
            dataset_collection.add_filter('base', True)
            # TODO: want to filter by dataset ids from the base assay collection as well

        if request.form.get('exp_type') is not None:
            dataset_collection.add_filter('experiment', request.form.get('exp_type'))

        for idx, item in enumerate(dataset_collection):
            if item.get_version() <= 2.2:
                continue
            self.dataset_ids.append(item.get_id())

        self.dataframe = pd.DataFrame()
        for idx, id in enumerate(self.dataset_ids):
            if id == '':
                continue
            dataset = repository_instance.get_by_id(id)
            if dataset is None or not dataset.is_valid():
                continue

            measurement_collection = MeasurementCollection()
            measurement_collection.add_filter('dataset_id', id)
            dataset_df = pd.DataFrame(list(measurement_collection.find()))
            dataset_df.drop(columns=['RFUs'])
            dataset_df = dataset_df[dataset_df['is_valid'] == True]

            for inf in range(4):
                dataset_df['I' + str(inf)] = [dict(x)[str(inf + 1)] if (len(x) > 0 and type(x[0]) == list and dict(x).get(str(inf + 1)))
                                              else np.nan for x in dataset_df['inflections']]

            self.dataframe = pd.concat([self.dataframe, dataset_df], sort=False)

        if len(self.dataframe) == 0:
            return

        # self.dataset_stats()
        # self.correct_datasets()

        self.save_csv(request.form.get("csv"))

        plotter = StatPlotter(dataframe=self.dataframe,
                              dataset_id=self.current_dataset,
                              features=request.form)
        plotter.execute()
        self.stat_urls = plotter.stat_urls

        return

    def save_csv(self, csvcheckbox):
        if csvcheckbox:
            file_name = r"DataExport_" + str(date.today()) + ".csv"
            self.dataframe.to_csv(file_name)

    def dataset_stats(self):
        df = self.dataframe.dropna()
        df = df[df['is_valid'] == True]

        # p value larger than .05 -> we can assume normal
        # p value less than .05 -> can't assume normal

        for concentration in np.unique(df['concentration']):
            observed = df[df['concentration'] == concentration]
            if len(observed) > 3:
                chi = stats.chisquare(f_obs=observed['I3'])
                ks_statistic, p_value = kstest(observed['I3'], 'norm')
                shapiro_results = shapiro(observed['I3'])
                print(concentration, '(', len(observed), 'observations), shapiro: ', shapiro_results, chi)

        df = self.dataframe.dropna()
        chi = stats.chisquare(f_obs=df['I3'])
        ks_statistic, p_value = kstest(df['I3'], 'norm')
        shapiro_results = shapiro(df['I3'])
        print(len(self.dataframe), len(df), 'shapiro: ', shapiro_results, chi)

    def covid_analysis(self):
        df = self.dataframe
        for iter in [60., 80., 100.]:
            test_neg = df[df['I3'] >= iter]
            test_pos = df[df['I3'] < iter]
            neg = df[df['concentration'].str.endswith(tuple(['NEG', '0uL', 'NFW']))]
            neg_labels = [item for item in np.unique(neg[['concentration']])]
            pos = df[~df['concentration'].isin(neg_labels)]
            f_neg = pos[pos['I3'] > iter]
            f_pos = neg[neg['I3'] < iter]
            t_neg = neg[neg['I3'] > iter]
            t_pos = pos[pos['I3'] < iter]
            sens = len(t_pos) / float(test_pos.shape[0])
            spec = len(t_neg) / float(test_neg.shape[0])
            accuracy = (len(t_neg) + len(t_pos)) / len(df)
            fscore = 2*len(t_neg) / (2*len(t_neg) + len(f_neg) + len(f_pos))
            flash('for a Ct value of ' + str(iter) + 'cycles', 'success')
            flash('COVID-19 results from %s wells' % len(df))
            flash('Sensitivity = %s ' % round(sens, 4), 'success')
            flash('Specificity = %s ' % round(spec, 4), 'success')
            flash('Accuracy = %s ' % round(accuracy, 4), 'success')
            flash('F-Score = %s ' % round(fscore, 4), 'success')
        return sens, spec

    def correct_datasets(self):
        for concentration in np.unique(self.dataframe['concentration']):
            reduceddf = self.dataframe[self.dataframe['concentration'] == concentration]
            if concentration != 'unknown':
                continue

            prevrow = ''
            for idx, row in reduceddf.iterrows():
                if row['label'] == prevrow:
                    continue
                conc = get_regex_response(row['label'], regextype='concentration')
                measurement_repository = MeasurementRepository()
                model = measurement_repository.get_by_id(row['_id'])
                prevrow = row['label']
                model['concentration'] = conc
                measurement_repository.save(model)

        wrongdf = self.dataframe[self.dataframe['label'].str.endswith('CLas')]
        dataset_repository = DatasetRepository()
        previd = ''
        for did in np.unique(wrongdf['dataset_id']):
            if previd == did:
                continue
            previd = did
            dataset = dataset_repository.get_by_id(did)
            dataset['experiment'] = 'gPCR'
            dataset_repository.save(dataset)



