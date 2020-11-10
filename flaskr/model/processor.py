from flask import flash
import pandas as pd
import numpy as np
import time

from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.database.dataset_models.repository import Repository
from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.model.helpers.calcfunctions import get_derivatives, get_percent_difference, get_linear_approx
from flaskr.model.helpers.importfunctions import get_collection
from flaskr.model.helpers.peakfunctions import get_peaks


class Processor(AbstractProcessor):
    def __init__(
            self,
            form: dict,
            dataset_id: str
    ):
        self.dataset_id = dataset_id
        self.form = form
        self.error_wells = []
        self.statistics = pd.DataFrame(columns=['group', 'replicate', '1', '2', '3', '4'])
        self.time = []
        self.control = None
        self.controllist = []
        self.ctlist = []
        self.ctthreshold = {'Ct RFU': [], 'Ct Cycle': []}
        self.covid_data = dict(TP60=0, TN60=0, FP60=0, FN60=0,
                               TP80=0, TN80=0, FP80=0, FN80=0,
                               TP100=0, TN100=0, FP100=0, FN100=0)
        self.positive_test_threshold = [60, 80, 100]

    def execute(self) -> Response:
        timestart = time.time()
        self.measurement_manager = MeasurementManager()
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        covid_analysis = True if dataset.get_experiment() == 'COVID' else False
        thresh = [max(well[1]['RFUs']) / 6. + min(well[1]['RFUs']) for well in enumerate(get_collection(self))]
        thresh = np.mean(thresh)
        wellindex = 0
        for wellindex, well in enumerate(get_collection(self)):

            # build time list from first well
            if wellindex < 2:
                self.time = [n for n in range(len(well.get_rfus()))]

            well['is_valid'] = True
            if covid_analysis:
                [response, well] = self.processCOVIDData(well, thresh)
            [response, well] = self.processData(well)

            if not response.is_success():
                self.error_wells.append(well.get_excelheader())
                well['is_valid'] = False

            self.measurement_manager.add(well)

        self.measurement_manager.save()

        if wellindex == 0:
            flash('Corrupted data, please delete and re-upload this dataset', 'error')

        if len(self.error_wells) > 0 and self.error_wells[0] != '':
            flash('Peaks were not found in wells %s' % str(', '.join(self.error_wells)), 'error')

        return Response(True, str(round(time.time() - timestart, 2)))

    def processCOVIDData(self, well, thresh):
        for lim in self.positive_test_threshold:
            if max(well.get_rfus()) - min(well.get_rfus()) < 10000:
                self.countNegative(well.get_label(), lim)
                return [Response(True, ''), well]
            for idx, rfu in enumerate(well.get_rfus()):
                if rfu > thresh:
                    #TODO: should we approximate and calculate the exact cycle?
                    well['thresholdCycle'] = idx
                    well['thresholdRFU'] = rfu

                    if idx < lim:
                        self.countPositive(well.get_label(), lim)
                    break
            self.countNegative(well.get_label(), lim)

        return [Response(True, ''), well]

    def processData(self, well):
        percentdiffs = [0 for x in range(4)]
        deltact = [0 for x in range(3)]
        inflectiondict = {}
        derivatives = get_derivatives(well)

        for dIndex in derivatives.keys():
            inflectiondict = get_peaks(self,
                                       well=well,
                                       derivativenumber=dIndex,
                                       derivative=derivatives[dIndex],
                                       allpeaks=inflectiondict)
        inflectiondict = dict(sorted(inflectiondict.items()))
        well['inflections'] = [(key, inflectiondict[key]['inflection']) for key in inflectiondict.keys()]
        well['inflectionRFUs'] = [(key, inflectiondict[key]['rfu']) for key in inflectiondict.keys()]

        if self.control is None or well.get_group() != self.control['group']:
            self.control = dict(group=well.get_group(), sample=well.get_sample(),
                                inflections=[item for item in well.get_inflections()])
            self.controllist = []
            self.ctthreshold = {'Ct RFU': [], 'Ct Cycle': []}

        # for all samples that match the control sample, collect controls
        if self.control['sample'] == well.get_sample():
            self.controllist.append([x for x in well.get_inflections()])
            if inflectiondict.get('3'):
                controlCt = {'Ct RFU': inflectiondict['3']['rfu'],
                             'Ct Cycle': inflectiondict['3']['inflection']}
                self.ctlist.append(controlCt)
                deltact = [0, controlCt['Ct Cycle'], controlCt['Ct RFU']]

            # average the control inflections
            #TODO: what if the first control has only 2 inflections and the others have 4? or vice versa?
            for idx, x in enumerate(self.control['inflections']):
                self.control['inflections'][idx] = (str(int(x[0])), np.mean([controlinflection[idx][1]
                                                                             for controlinflection in self.controllist
                                                                             if len(controlinflection) > idx]))
            # average the ct threshold
            if len(self.ctlist) > 0:
                self.ctthreshold['Ct Cycle'] = np.nanmean([x['Ct Cycle'] for x in self.ctlist])
                self.ctthreshold['Ct RFU'] = np.nanmean([x['Ct RFU'] for x in self.ctlist])
            else:
                self.ctthreshold['Ct Cycle'] = 0
                self.ctthreshold['Ct RFU'] = 0

        # get percent differences and delta ct values
        elif self.control['sample'] != well.get_sample():
            percentdiffs = get_percent_difference(self, well['inflections'])
            if not self.form.get('gPCR'):
                deltact = self.getDeltaCt(well)

        # calculate delta ct and percent diffs
        well['deltaCt'] = deltact
        well['percentdiffs'] = percentdiffs

        stats = {'group': well.get_group(),
                 'sample': well.get_sample()}
        for i in range(1, 5):
            stats[str(i)] = inflectiondict.get(str(i))['inflection'] \
                if inflectiondict.get(str(i)) else np.nan

        self.statistics = self.statistics.append([stats], ignore_index=True)

        return [Response(True, ''), well]

    def getDeltaCt(self, well):
        for idx, wellRFU in enumerate(well.get_rfus()):
            if wellRFU > self.ctthreshold['Ct RFU']:
                lineareqn = get_linear_approx(x1=self.time[idx-1],
                                              x2=self.time[idx],
                                              y1=well.get_rfus()[idx-1],
                                              y2=wellRFU)
                ctthreshold = self.getxValueFromLinearApprox(lineareqn)

                deltact = self.ctthreshold['Ct Cycle'] - ctthreshold
                return [deltact, ctthreshold, self.ctthreshold['Ct RFU']]
        return [0, 0]

    def getxValueFromLinearApprox(self, equation):
        slope = equation[0]
        yintercept = equation[1]
        return (self.ctthreshold['Ct RFU'] - yintercept) / slope

    def getStatistics(self):
        results = {}
        if sum(self.covid_data.values()) > 0:
            for lim in self.positive_test_threshold:
                results['COVID-19 test resulted in the following statistics'] = ''
                try:
                    results['Sensitivity for cycle ' + str(lim)] = "{:0.2f}".format(self.covid_data['TP'+str(lim)] /
                                                              (self.covid_data['TP'+str(lim)] + self.covid_data['FN'+str(lim)]))
                except ZeroDivisionError:
                    results['Sensitivity for cycle ' + str(lim)] = 'NaN (zero true positives and false negatives)'
                    pass
                try:
                    results['Specificity for cycle ' + str(lim)] = "{:0.2f}".format(self.covid_data['TN'+str(lim)] /
                                                              (self.covid_data['TN'+str(lim)] + self.covid_data['FP'+str(lim)]))
                except ZeroDivisionError:
                    results['Specificity for cycle ' + str(lim)] = 'NaN (zero true negatives and false positives)'
                    pass
                try:
                    results['F Score for cycle ' + str(lim)] = "{:0.2f}".format(2 * self.covid_data['TN'+str(lim)] /
                                                (2 * self.covid_data['TN'+str(lim)] + self.covid_data['FN'+str(lim)] + self.covid_data['FP'+str(lim)]))
                except ZeroDivisionError:
                    results['F Score for cycle ' + str(lim)] = 'NaN (zero true negatives and false positives)'
                    pass
                results['Overall Accuracy for cycle ' + str(lim)] = "{:0.2f}".format((self.covid_data['TN'+str(lim)] + self.covid_data['TP'+str(lim)]) /
                                                       sum([count for count in self.covid_data.values()]))

            results['Explanation'] = 'Sensitivity is the proportion of actual negatives correctly identified as such. ' + \
                                     'Specificity is the proportion of infected that were correctly identified. ' + \
                                     'Accuracy is a measure of all the correctly identified cases, and the F-Score ' + \
                                     '(an alternative measure of accuracy) gives a measure of the incorrectly classified cases. '

        elif not self.statistics.empty:
            if not len(self.statistics.isna()) == len(self.statistics):
                statistics = {'replicate variation': self.statistics.groupby('replicate').std()
                              [['1', '2', '3', '4']].mean(1).tolist(),
                              'group variation': self.statistics.groupby('group').std()
                              [['1', '2', '3', '4']].mean(1).tolist()}
                results['Average variation for each concentration'] = ', '.join(["{:0.2f}".format(item)
                                                                                 for item in statistics['replicate variation']])
                results['Average variation for each group'] = ', '.join(["{:0.2f}".format(item)
                                                                         for item in statistics['group variation']])
        return results

    # def countPositivesAndNegatives(self, well):
    #     for inf in well.get_inflections():
    #         if inf[0] != '3':
    #             continue
    #         if inf[1] <= 90:
    #             if 'POS' in well.get_label():
    #                 self.covid_data['TP'] += 1
    #             else:
    #                 self.covid_data['FP'] += 1
    #             if 'NFW' in well.get_label():
    #                 flash('Warning: a control (%s) shows sign of contamination.' % well.get_label(), 'error')
    #         elif inf[1] > 90:
    #             if 'POS' in well.get_label():
    #                 self.covid_data['FN'] += 1
    #             else:
    #                 self.covid_data['TN'] += 1

    def countPositive(self, label, lim):
        if 'Pos Ctrl' in label:
            self.covid_data['TP' + str(lim)] += 1
        else:
            self.covid_data['FP' + str(lim)] += 1

    def countNegative(self, label, lim):
        if 'Pos Ctrl' in label:
            self.covid_data['FN' + str(lim)] += 1
        else:
            self.covid_data['TN' + str(lim)] += 1
