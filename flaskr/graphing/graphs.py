import numpy as np
import seaborn
import time
import io
import base64
import pandas as pd
import scipy.stats as stat
from flask import current_app, flash
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as plt
from flaskr.model.helpers.functions import get_unique_group, get_unique
from flaskr.model.helpers.buildfunctions import get_concentrations
from flaskr.database.dataset_models.repository import Repository
from flaskr.model.helpers.calcfunctions import get_regex_response
from flaskr.model.helpers.covidstats import covid_stats


def removeLegendTitle(plot):
    handles, labels = plot.get_legend_handles_labels()
    plot.legend(handles=handles[1:], labels=labels[1:])
    return plot


def getRegression(df):
    df = df.groupby('replicate').mean()
    linear_regressor = LinearRegression()
    linear_regressor.fit(np.asarray(np.log(df['pMconcentration'])).reshape(-1, 1),
                         np.asarray(df['value']).reshape(-1, 1))
    rvalue = linear_regressor.score(np.asarray(np.log(df['pMconcentration'])).reshape(-1, 1),
                                    np.asarray(df['value']).reshape(-1, 1))
    return [rvalue, linear_regressor]


def validateDF(df):
    return not df.empty


class Grapher:
    def __init__(
            self,
            dataset_id: str,
            customtitle: str = '',
    ):
        self.transparent = False
        self.dataset_id = dataset_id
        self.customtitle = customtitle
        self.time = []
        self.data = {}
        self.graph_urls = {}
        self.colors = ["gray", "dodgerblue", "red", "lightgreen", "magenta", "gold", "cyan", "darkgreen"]
        self.vline = 0
        self.hline = 0
        self.covid_analysis = False
        self.subplots = False
        self.number_of_groups = 0

    def execute(self, features):
        if features is None:
            features = dict()
        self.setGraphSettings(features)

        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        if dataset.get_experiment() == 'COVID':
            self.covid_analysis = True
        df = dataset.get_pd_well_collection()
        df = df[df['is_valid'] == True]

        df = df.drop(columns=['_id', 'dataset_id'])

        rfudf = df.copy()
        for i in range(len(df['RFUs'].iloc[0])):
            self.time.append(i)
        df['DeltaCt'] = [x[0] if len(x) > 0 else 0 for x in df['deltaCt']]
        df['CtThreshold'] = [x[1] if len(x) > 1 else 0 for x in df['deltaCt']]
        df['CtRFU'] = [x[2] if len(x) > 2 else 0 for x in df['deltaCt']]
        for inf in range(4):
            df['Inflection ' + str(inf)] = [dict(x)[str(inf + 1)] if dict(x).get(str(inf + 1)) else 0 for x in
                                            df['inflections']]
            df['RFU of Inflection ' + str(inf)] = [dict(x)[str(inf + 1)] if dict(x).get(str(inf + 1)) else 0 for x in
                                                   df['inflectionRFUs']]
            df['Percent Diff ' + str(inf)] = [x[inf] if len(x) == 4 else 0 for x in df['percentdiffs']]

        df = df.drop(columns=['replicate_id'])

        if features.get('subplots'):
            self.subplots = True

        self.number_of_groups = int(df['group'].max()) + 1
        if self.number_of_groups < 2:
            self.subplots = False

        if features.get('rfus'):
            self.RFUIndividualGraphsByGroup(rfudf, df)
            self.RFUGraphs(rfudf, df, features)

        df = df.drop(columns=['RFU of Inflection ' + str(inf) for inf in range(4)])

        df = pd.melt(df, id_vars=list(df.columns)[:-8],
                     value_vars=list(df.columns)[-8:],
                     var_name='variable',
                     value_name='value')

        if features.get('inflections'):
            self.InflectionGraphByGroup(df[df['variable'].str.startswith('Inflection')])
            self.InflectionGraphsByNumber(df[df['variable'].str.startswith('Inflection')])

        if features.get('curvefits'):
            self.CurveFitByGroup(df[df['variable'].str.startswith('Inflection')])

        if features.get('percentdiffs'):
            self.percentGraphs(df[df['variable'].str.startswith('Percent Diff ')])

        if features.get('ctthresholds'):
            self.CtThresholds(df)

        if features.get('covidstats'):
            covid_stats(rfudf)

        if len(self.graph_urls) < 1:
            self.RFUGraphs(rfudf, df, features)

        return self.graph_urls

    def InflectionGraphByGroup(self, df):
        if self.number_of_groups > 20:
            return

        axis = None

        if self.subplots:
            fig_infn, pos_infn = plt.subplots(self.number_of_groups, 1)

        for group in range(self.number_of_groups):
            subinf = df[(df['group'] == group)]
            if self.subplots:
                axis = pos_infn[group-1]
            indplt = seaborn.swarmplot(x="variable", y="value", hue="label", data=subinf, dodge=True, marker='o',
                                       s=2.6, linewidth=.6, palette=self.colors, ax=axis)
            indplt.set(xticklabels=['I1', 'I2', 'I3', 'I4'])
            indplt = removeLegendTitle(indplt)

            if self.subplots:
                pos_infn[group-1].set_xlabel('')
                pos_infn[group-1].set_ylabel('Cycles')
                pos_infn[group-1].set_title('Group ' + str(group+1) + ' (' + get_unique_group(df['label'], df['group'])[group-1] + ')')
                box = pos_infn[group-1].get_position()
                pos_infn[group-1].legend(bbox_to_anchor=(1, 1))
                pos_infn[group-1].set_position([box.x0, box.y0, box.width, box.height])
            else:
                box = plt.gca().get_position()
                plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
                legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
                try:
                    ax = plt.gca().add_artist(legend1)
                except matplotlib.MatplotlibDeprecationWarning:
                    current_app.logger.error('Matplotlib depreciation warning with dataset: %s' % self.dataset_id)

                plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label)
                            for idx, label in enumerate(get_unique_group(df['label'], df['group']))],
                           bbox_to_anchor=(1, .1), loc='lower left')
                plt.xlabel('')
                plt.ylabel('Cycles')
                self.saveimage(plt, 'Inflections_'+str(group+1))
        if self.subplots:
            fig_infn.tight_layout(rect=[0, 0.03, 1, 0.95])
            self.saveimage(plt, 'Group Inflections', fig=fig_infn, subplot=True)

    def InflectionGraphsByNumber(self, df):
        axis = None
        if self.subplots:
            fig_infn, pos_infn = plt.subplots(2, 2, sharex=True, sharey=True)
            subdict = {1: (0, 0), 2: (0, 1), 3: (1, 0), 4: (1, 1)}

        df.insert(0, 'replicateIndex', int(df['group'].max()) * (df['sample'] - 1) + df['group'] - 1)
        grouplabels = get_unique_group(df['label'], df['group'])
        df.insert(0, 'labelwithoutgroup', [get_regex_response(item, 'concentration') for item in df['label']])

        for inf in range(1, 5):
            if not validateDF(df[df['variable'] == "Inflection " + str(inf-1)]):
                continue
            if self.subplots:
                axis = pos_infn[subdict[inf]]
            indplt = seaborn.swarmplot(x="replicateIndex", y="value", hue="labelwithoutgroup",
                                       data=df[df['variable'] == "Inflection " + str(inf - 1)],
                                       marker='o', s=2.6, linewidth=.6, palette=self.colors, ax=axis)
            indplt = removeLegendTitle(indplt)
            if self.subplots:
                pos_infn[subdict[inf]].set(xticklabels=[str(num % int(df['group'].max()) + 1) for num in np.arange(32)])
                pos_infn[subdict[inf]].set_xlabel('')
                pos_infn[subdict[inf]].set_ylabel('Cycles')
                pos_infn[subdict[inf]].set_title('Inflection ' + str(inf))
            else:
                indplt.set(xticklabels=[str(num % int(df['group'].max()) + 1) for num in np.arange(32)])
                plt.ylabel('Cycles')
                plt.xlabel('Group Number')
                box = plt.gca().get_position()
                plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
                try:
                    legend1 = plt.legend(bbox_to_anchor=(1, 1), loc='upper left')
                    ax = plt.gca().add_artist(legend1)
                except matplotlib.MatplotlibDeprecationWarning:
                    current_app.logger.error('Matplotlib depreciation with dataset: %s' % self.dataset_id)

                plt.legend(['Group  ' + str(idx + 1) + '- ' + str(label)
                            for idx, label in enumerate(grouplabels)],
                           bbox_to_anchor=(1, .1), loc='lower left')
            if not self.subplots:
                self.saveimage(plt, 'Inflection' + str(inf))
        if self.subplots:
            self.saveimage(plt, 'Inflections', fig=fig_infn, subplot=True)

    def RFUIndividualGraphsByGroup(self, df, idf):
        group_handles = []
        group_labels = []
        for group in range(self.number_of_groups):
            rdf = pd.DataFrame(columns=['time', 'rfus', 'replicate', 'index'])
            for idx, row in enumerate(df[df['group'] == group].iterrows()):
                tdf = pd.DataFrame(dict(time=self.time, rfus=row[1]['RFUs'], replicate=row[1]['replicate'],
                                        index=row[0], label=row[1]['label'], group=row[1]['group']))
                rdf = pd.concat([rdf, tdf], sort=False)
            group_labels.append(rdf.iloc[0]['label'])

            if self.number_of_groups < 20:
                plt.figure(0)
                iidf = idf[(idf['group'] == group)]
                if self.covid_analysis:
                    sdf = iidf.drop(iidf[iidf['thresholdRFU'] == 0.0].index.values, axis='index')
                    if validateDF(sdf):
                        plt.scatter(x="thresholdCycle", y="thresholdRFU",
                                    data=sdf, s=10, edgecolor='black',
                                    linewidth=.2)

                else:
                    for i in range(4):
                        sdf = iidf[iidf["RFU of Inflection " + str(i)] > 0]
                        sdf = sdf.drop(sdf[sdf['Inflection ' + str(i)] == 0.0].index.values, axis='index')
                        if validateDF(sdf):
                            plt.scatter(x="Inflection " + str(i), y="RFU of Inflection " + str(i),
                                        label="Inflection " + str(i + 1),
                                        data=sdf, s=10, edgecolor='black',
                                        linewidth=.2)

                color_list = self.setColorList(np.unique(rdf[['label']]))
                snsplot = seaborn.lineplot(x='time', y='rfus', hue='label', units='index', estimator=None,
                                           data=rdf, linewidth=.7, palette=color_list)
                snsplot = removeLegendTitle(snsplot)
                if self.vline > 0:
                    plt.axvline(x=self.vline, color='red')
                if self.hline > 0:
                    plt.axhline(y=self.hline, color='red', linestyle=':')
                plt.ylabel('RFU')
                plt.xlabel('Cycles')
                self.saveimage(plt, 'Individuals_' + str(group+1))

            plt.figure(1)
            color_list = self.setColorList(np.unique(rdf[['label']]))
            snsplot = seaborn.lineplot(x='time', y='rfus', units='index', estimator=None,
                                       data=rdf, linewidth=.7, palette=color_list, label=group)
            [h, l] = snsplot.get_legend_handles_labels()
            group_handles.append(h[-1])

        snsplot.legend(handles=group_handles, labels=group_labels)
        if self.vline > 0:
            plt.axvline(x=self.vline, color='red')
        if self.hline > 0:
            plt.axhline(y=self.hline, color='red', linestyle=':')
        plt.ylabel('RFU')
        plt.xlabel('Cycles')
        self.saveimage(plt, 'Individuals_All')

    def RFUGraphs(self, df, idf, features):
        group_labels = []
        group_handles = []
        for group in range(self.number_of_groups):
            adf = pd.DataFrame(columns=['time', 'averagerfu', 'rfus', 'replicate', 'label', 'group'])  # changed here
            groupdf = df[df['group'] == group]
            if not validateDF(groupdf):
                continue
            group_labels.append(groupdf.iloc[0]['label'])
            for idx, replicate in enumerate(get_unique(groupdf['label'])):
                tdf = groupdf[groupdf['label'] == replicate]
                tdf = pd.DataFrame([x[1]['RFUs'] for x in tdf.iterrows()])
                tdf = pd.DataFrame(data=dict(time=self.time,
                                             averagerfu=tdf.mean(0),
                                             label=replicate,
                                             replicate=idx,
                                             group=group))
                adf = pd.concat([adf, tdf], sort=False)

            if self.number_of_groups < 20:
                plt.figure(0)
                color_list = self.setColorList(np.unique(adf[['label']]))
                grouprfuplot = seaborn.lineplot(x='time', y='averagerfu', hue='label', units='replicate', estimator=None,
                                                data=adf, linewidth=.7, palette=color_list)
                grouprfuplot = removeLegendTitle(grouprfuplot)
                plt.ylabel('RFU')
                plt.xlabel('Cycles')

                if self.covid_analysis:
                    if features.get('cifill'):
                        self.ci_range(idf, group)

                if self.vline > 0:
                    plt.axvline(x=self.vline, color='red')
                if self.hline > 0:
                    plt.axhline(y=self.hline, color='red', linestyle=':')
                self.saveimage(plt, 'Averages_' + str(group+1))

            plt.figure(1)
            allrfuplot = seaborn.lineplot(x='time', y='averagerfu', data=adf, units='replicate', estimator=None,
                                          linewidth=.7, legend="full", label=group_labels[-1])
            allrfuplot = removeLegendTitle(allrfuplot)
            [h, l] = allrfuplot.get_legend_handles_labels()
            group_handles.append(h[-1])

        allrfuplot.legend(handles=group_handles)
        if self.vline > 0:
            plt.axvline(x=self.vline, color='red')
        if self.hline > 0:
            plt.axhline(y=self.hline, color='red', linestyle=':')
        plt.ylabel('RFU')
        plt.xlabel('Cycles')
        self.saveimage(plt, 'Averages_All')

    def percentGraphs(self, df):
        if self.number_of_groups > 20:
            return

        axis = None
        if self.subplots:
            fig_per, pos_per = plt.subplots(self.number_of_groups, 1, sharex=True, sharey=True)

        for group in range(self.number_of_groups):
            subpc = df[df['group'] == group]
            if not validateDF(subpc[subpc['value'] > 0]):
                continue
            if self.subplots:
                axis = pos_per[group-1]
                # subpc = subpc.sort_values(['variable', 'replicate', 'value'])

            indplt = seaborn.swarmplot(x='variable', y="value", hue="label", data=subpc, dodge=True, marker='o',
                                       s=2.6, linewidth=.6, palette=self.colors, ax=axis)
            indplt.set(xticklabels=['PD1', 'PD2', 'PD3', 'PD4'])

            if self.subplots:
                pos_per[group-1].set_xlabel('')
                pos_per[group-1].set_ylabel('% Diff')
                pos_per[group-1].legend().remove()
                pos_per[group-1].set_title('Group ' + str(group+1))
            else:
                box = plt.gca().get_position()
                plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
                plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
                plt.xlabel('')
                plt.ylabel('Percent Difference from Control')
                self.saveimage(plt, 'PercentDiff_' + str(group+1))
        if self.subplots:
            fig_per.tight_layout(rect=[0, 0.03, 1, 0.95])
            self.saveimage(plt, 'Group Percent Diffs', fig=fig_per, subplot=True)

    def CurveFitByGroup(self, df):
        axis = None
        if self.subplots:
            fig_cf, pos_cf = plt.subplots(self.number_of_groups, 1)

        for group in range(self.number_of_groups):
            if self.subplots:
                axis = pos_cf[group-1]

            cdf = df[(df['group'] == group) & df['value'] > 0] #.sort_values(['replicate', 'value'])

            cdf.insert(0, 'recognized',
                       cdf['label'].apply(lambda x: 'True' if get_regex_response(x, 'concentration') else 'False'))
            cdfconcentrations = [get_concentrations(get_regex_response(item, 'concentration')) for item in cdf['label']]
            if len(cdfconcentrations) == 0:
                flash('The concentration cannot be identified for curve fit graphs', 'error')
                break
            cdf.insert(0, 'pMconcentration', cdfconcentrations)
            cdf = cdf[cdf['pMconcentration'] >= .1]

            for inf in range(4):
                infcdf = cdf[cdf['variable'] == "Inflection " + str(inf)]
                pMconcentrationlabels = np.unique(infcdf['pMconcentration'])
                infmeans = infcdf.groupby('pMconcentration')['value'].mean()
                infstds = infcdf.groupby('pMconcentration')['value'].std()
                if not validateDF(infcdf):
                    continue

                curveplt = seaborn.swarmplot(x=pMconcentrationlabels, y=infmeans, marker='o',
                                             s=2.6, linewidth=.6, palette=['black'], ax=axis)
                if self.subplots:
                    source = pos_cf[group-1]
                else:
                    source = plt

                source.errorbar(range(len(infmeans)), infmeans, yerr=infstds, fmt='|', color='grey')

                [rvalue, linear_regressor] = getRegression(infcdf)

                # get rvalue not including the .1pM concentration
                lessrvalue = 'nan'
                if validateDF(infcdf[(infcdf['pMconcentration'] >= 1)]):
                    [lessrvalue, _] = getRegression(infcdf[(infcdf['pMconcentration'] >= 1)])
                    lessrvalue = round(lessrvalue, 5)

                concentrationX = np.unique(infcdf['pMconcentration'])
                Y = linear_regressor.predict(np.log(concentrationX).reshape(-1, 1)).flatten()
                label = 'I' + str(inf + 1) + ': ' + \
                        str(round(float(linear_regressor.coef_[0]), 4)) + 'x + ' + \
                        str(round(float(linear_regressor.intercept_), 4)) + \
                        '. R: ' + str(round(rvalue, 5)) + \
                        '(w/o 100fM R=' + str(lessrvalue) + ')'

                curveplt = seaborn.lineplot(x=np.arange(0, len(concentrationX)), y=Y, label=label,
                                            palette=self.colors, ax=axis)
                if self.subplots:
                    box = pos_cf[group - 1].get_position()
                    pos_cf[group - 1].legend(bbox_to_anchor=(1, 1))
                    pos_cf[group - 1].set_position([box.x0, box.y0, box.width, box.height])
                    pos_cf[group - 1].set_ylabel('Cycles')
                    pos_cf[group - 1].set_xlabel('Log of Concentration (pM)')
                else:
                    plt.ylabel('Cycles')
                    plt.xlabel('Log of Concentration (pM)')
            if not self.subplots:
                self.saveimage(plt, 'CurveFit_' + str(group+1))
        if self.subplots:
            fig_cf.tight_layout(rect=[0, 0.03, 1, 0.95])
            self.saveimage(plt, 'Group Curve Fits', fig=fig_cf, subplot=True)

    def CtThresholds(self, df):
        for group in range(self.number_of_groups):
            idf = df[(df['group'] == group)]
            ctRFU = idf[idf['CtRFU'] > 0]['CtRFU']
            if not validateDF(ctRFU) or len(np.unique(idf['concentration'])) == 1:
                flash('Unique concentration cannot be identified in group %s for ct threshold graphs' % group, 'error')
                continue
            plt.scatter(x='concentration', y='DeltaCt', label=group,
                        data=idf, s=10, edgecolor='black', linewidth=.2)
        plt.legend()
        plt.ylabel('Delta Ct (difference in minutes)')
        plt.xlabel('Concentration')
        self.saveimage(plt, 'DeltaCt')

    def mean_conf_int(self, data, confidence=0.95):
        a = np.array(data)
        n = len(a)
        m, se = np.mean(a), stat.sem(a)
        h = se * stat.t.ppf((1 + confidence) / 2., n - 1)
        return [m, m - h, m + h]

    def ci_range(self, idf, group):
        iidf = idf[(idf['group'] == group)]

        sdf = iidf.drop(iidf[iidf['thresholdRFU'] == 0.0].index.values, axis='index')

        xavg, xmini, xmaxi = self.mean_conf_int(sdf['thresholdCycle'])

        plt.errorbar(xavg, np.mean(sdf['thresholdRFU']), yerr=np.std(sdf['thresholdRFU']),
                     xerr=np.std(sdf['thresholdCycle']), color='black', label='Mean and Std. Dev.')

        plt.axvline(x=xmini, color='red', linestyle=':')
        plt.axvline(x=xmaxi, color='red', linestyle=':')
        plt.axvspan(xmini, xmaxi, alpha=0.15, color='red', label='CI 95%')

        plt.legend()

        # TODO: decide whether to / how to integrate more robust median-based statistics, similar to what's below
        # plt.errorbar(np.median(sdf['thresholdCycle']), np.median(sdf['thresholdRFU']), yerr=stat.median_absolute_deviation(sdf['thresholdRFU']),
        #             xerr=stat.median_absolute_deviation(sdf['thresholdCycle']), color='cyan', label='Median and Abs. Dev.')

    def saveimage(self, plt, title, fig=False, subplot=False):
        if not subplot:
            plt.title(self.dataset_id + '_' + title, fontsize=14)

        else:
            fig.suptitle(self.dataset_id + '_' + title, fontsize=14)

        sio = io.BytesIO()
        plt.savefig(sio, format='png', transparent=self.transparent)
        plt.close()
        self.graph_urls[self.dataset_id + '_' + title + '.png'] = base64.b64encode(sio.getvalue()).decode(
            'utf-8').replace('\n', '')

    def setColorList(self, length):
        color_length = len(length)
        colors = [self.colors[i % len(self.colors)] for i in range(color_length)]
        return colors

    def setGraphSettings(self, features):
        if features.get('transparent'):
            self.transparent = True

        if features.get('vline'):
            self.vline = float(features['vline'])
        if features.get('hline'):
            self.hline = float(features['hline'])

        params = {'legend.fontsize': 5,
                  'legend.loc': 'best',
                  'legend.framealpha': 0.5,
                  'figure.dpi': 250,
                  'legend.handlelength': .8,
                  'legend.markerscale': .4,
                  'legend.labelspacing': .4,
                  'font.size': 8}

        if features.get('white'):
            params.update({
                'scatter.edgecolors': 'white',
                'axes.edgecolor': 'white',
                'axes.facecolor': 'white',
                'axes.labelcolor': 'white',
                'xtick.color': 'white',
                'ytick.color': 'white',
                'figure.facecolor': 'white',
                'text.color': 'white',
                'legend.framealpha': .1})
        else:
            params.update({
                'scatter.edgecolors': 'black',
                'axes.edgecolor': 'black',
                'axes.facecolor': 'white',
                'axes.labelcolor': 'black',
                'xtick.color': 'black',
                'ytick.color': 'black',
                'figure.facecolor': 'white',
                'text.color': 'black'})

        plt.rcParams.update(params)
        seaborn.set_palette(self.colors)
