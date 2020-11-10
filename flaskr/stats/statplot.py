import numpy as np
import io
import base64
import re
import pandas as pd

import statsmodels.api as sm
import pylab

import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('Agg')

from flaskr.model.helpers.covidstats import covid_stats


class StatPlotter:
    def __init__(
            self,
            dataset_id: str,
            dataframe: pd.DataFrame,
            features: None
    ):
        self.dataset_id = dataset_id
        self.dataframe = dataframe
        self.stat_urls = {}
        if features is None:
            features = dict()
        self.features = features
        self.inflections = []
        self.title = ''

    def execute(self):
        self.setstatsettings()
        self.setinflections()

        plt.figure()
        groupings = ['']
        if self.features.get('concentration'):
            groupings = np.unique(self.dataframe['concentration'])

        if self.features.get('exp_type') == 'COVID':
            self.covid_graphs()

            # TODO: this replaces a lack of inflection with 250 (generic maximum)
            self.dataframe.fillna(250)

        for key in groupings:
            x = self.dataframe
            if key != '':
                self.title = key
                x = self.dataframe[self.dataframe['concentration'] == str(key)]

            for inflection in self.inflections:
                key = 'I' + str(inflection)
                try:
                    x0 = x[x[key].notna()][key]

                except KeyError:
                    continue
                if len(x0) < 10: #skip very small groups
                    continue
                if self.features.get('allplots') or self.features.get('scatters'):
                    self.scatter(x, key)
                if self.features.get('allplots') or self.features.get('histograms'):
                    self.hist(x0, key)
                    # self.QQ(x0, key)
                if self.features.get('allplots') or self.features.get('violins'):
                    self.violin(x0, key)

            # self.TestPlot(x, key)
        return self.stat_urls

    def TestPlot(self, x, key):
            plt.figure()
            x1, x2, x3, x4 = [x['I'+str(it+1)].to_numpy() for it in np.arange(4)]
            x1, x2, x3, x4 = [np.delete(item, np.where(item == 'nan')) for item in [x1, x2, x3, x4]]
            x1, x2, x3, x4 = [item.astype(float) for item in [x1, x2, x3, x4]]
            plt.violinplot([x1, x2, x3, x4], showextrema=True, showmedians=True, showmeans=True)
            self.saveimage(plt, str(key) +" All Inf Violins")


            plt.figure()
            base = self.dataframe[self.dataframe['concentration'] == '1 nM']
            b1, b2, b3, b4 = [base['I' + str(it + 1)].to_numpy() for it in np.arange(4)]
            b1, b2, b3, b4 = [np.delete(item, np.where(item == 0)) for item in [b1, b2, b3, b4]]
            b1, b2, b3, b4 = [item.astype(float) for item in [b1, b2, b3, b4]]
            for keys in np.unique(self.dataframe['concentration']):
                if keys == '1 nM':
                    continue
                else:
                    x = self.dataframe[self.dataframe['concentration'] == str(keys)]
                    x1, x2, x3, x4 = [x['I' + str(it + 1)].to_numpy() for it in np.arange(4)]
                    x1, x2, x3, x4 = [np.delete(item, np.where(item == 0)) for item in [x1, x2, x3, x4]]
                    x1, x2, x3, x4 = [item.astype(float) for item in [x1, x2, x3, x4]]
                    d1 = x1 - b1
                    d2 = x2 - b2
                    d3 = x3 - b3
                    d4 = x4 - b4
                    plt.violinplot([d1, d2, d3, d4], showextrema=True, showmedians=True, showmeans=True)
                    self.saveimage(plt, str(keys) + " All Inf Differences from nM Violins")

    def scatter(self, data, key, title=None):
        groups = data.groupby('concentration')
        for name, group in groups:
            plt.scatter(np.arange(len(group)), group[key], label=name)
        box = plt.gca().get_position()
        plt.gca().set_position([box.x0, box.y0, box.width * 0.75, box.height])
        plt.legend(bbox_to_anchor=(1, 1), loc='upper left', borderaxespad=0.)
        plt.xlabel('Well Number')
        plt.ylabel('Cycle #')
        if title is not None:
            self.saveimage(plt, str(key) + ' scatter ' + title)
        self.saveimage(plt, str(key) + ' scatter')

    def hist(self, x0, key):
        plt.hist(x0, bins=50, color='blue')
        plt.xlabel('Cycle #')
        plt.ylabel('Count')
        self.saveimage(plt, str(key) + " histogram")

    def violin(self, x0, key):
        plt.violinplot(x0, showextrema=True, showmedians=True, showmeans=True)
        plt.xlabel('Cycle #')
        plt.ylabel('Count')
        self.saveimage(plt, str(key) + " violin")

    def QQ(self, x0, key):
        sm.qqplot(x0, line='45')
        pylab.show()
        self.saveimage(pylab, str(key) + " Q-Q")

    def covid_graphs(self):
        if not self.features.get('allplots') and not self.features.get('customcovid'):
            return

        covid_df = covid_stats(self.dataframe, flash_numbers=False)
        covid_df = self.adjust_COVID_labels(covid_df)
        groups = covid_df.groupby('COVID groups')

        for name, group in groups:
            plt.figure(figsize=(5, 10))
            plt.barh(group['concentration'], group['percent positive_80'],
                     xerr=[group['percent positive_80'] - group['percent positive_60'],
                     group['percent positive_100'] - group['percent positive_80']])
            plt.title(name + ' wells rising before 80 +/- 20 cycle thresholds')
            plt.xlabel('Positive Tests (percent)')
            plt.ylabel('Concentrations')
            plt.grid(which='major', axis='x')
            plt.tight_layout()
            self.saveimage(plt, name + 'percent positive', subplots=True)

            plt.figure(figsize=(5, 10))
            plt.barh(group['concentration'], group['average cycle'],
                     xerr=[group['average cycle'] - group['minimum cycle'],
                     group['maximum cycle'] - group['average cycle']])
            plt.title(name + ' wells - location of exponential increase')
            plt.xlabel('Average Cycle')
            plt.ylabel('Concentrations')
            plt.grid(which='major', axis='x')
            plt.tight_layout()
            self.saveimage(plt, name + 'avg cycle', subplots=True)

        fig, ax = plt.subplots()
        scatter = ax.scatter(covid_df['average cycle'], covid_df['percent positive_80'], s=covid_df['samples'])
        for i, txt in enumerate(covid_df['concentration']):
            ax.annotate(txt, (covid_df['average cycle'][i], covid_df['percent positive_80'][i]))
        ax.legend(*scatter.legend_elements(prop='sizes'), loc="upper right", title="Sizes")
        plt.title('Percent positive results and average cycle')
        plt.xlabel('Average Cycle')
        plt.ylabel('Percent Positive')
        self.saveimage(plt, 'percent positive vs cycle', subplots=True)

    def adjust_COVID_labels(self, df):
        if len(df) == 0:
            return

        new_labels = []
        df = df[df['samples'] > 20]  # minimum of 20 wells in order to include on the plots
        df.loc[df['concentration'] == 'COV-POS', 'concentration'] = 'COVID_POS'
        df.loc[df['concentration'] == 'Pos CV', 'concentration'] = 'COVID_POS'
        df.loc[df['concentration'] == 'COVID-POS', 'concentration'] = 'COVID_POS'

        count_labels = len(np.unique(df['concentration']))
        for label in df['concentration']:
            abbreviated_labels = 'POS'
            if re.search(r'NEG', label.upper()) is not None or \
                    re.search(r'NFW', label.upper()) is not None:
                abbreviated_labels = 'NEG'
            else:
                #TODO: figure out a better way to divide the positive tests into two groups
                if count_labels > 100 and len(label) > 9:
                    abbreviated_labels = 'POS2'

            new_labels.append(abbreviated_labels)
        df.insert(0, 'COVID groups', new_labels)
        return df.reset_index(drop=True)

    def setinflections(self):
        for item in self.features.keys():
            if item.startswith('inflection'):
                self.inflections.append(int(item[-1]))

    def saveimage(self, plt, title, subplots=False):
        if not subplots:
            plt.title(self.title + ' ' + title, fontsize=14)
        sio = io.BytesIO()
        plt.savefig(sio, format='png')
        plt.close()
        self.stat_urls[self.title + ' ' + title + '.png'] = base64.b64encode(sio.getvalue()).decode('utf-8').replace('\n', '')

    def setstatsettings(self):
        params = {
                'scatter.edgecolors': 'black',
                'axes.edgecolor': 'black',
                'axes.facecolor': 'white',
                'axes.labelcolor': 'black',
                'xtick.color': 'black',
                'ytick.color': 'black',
                'figure.facecolor': 'white',
                'text.color': 'black'}

        plt.rcParams.update(params)
