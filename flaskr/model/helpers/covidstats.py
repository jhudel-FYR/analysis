from flask import flash
import numpy as np
import pandas as pd


def covid_stats(df, flash_numbers=True):
    statdf = {'concentration': [],
              'samples': [],
              'percent positive_60': [],
              'percent positive_80': [],
              'percent positive_100': [],
              'average cycle': [],
              'minimum cycle': [],
              'maximum cycle': []}

    df = df[df['is_valid'] == True]
    df = I3_replaces_empty_thresholds(df)
    if flash_numbers:
        flash('The following results are also contained in the _summary.xlsx file in the zip download.')
    for conc in np.unique(df['concentration']):
        tmpdf = df[df['thresholdCycle'] != 0]
        tmpdf = tmpdf[tmpdf['concentration'] == conc]
        if tmpdf.empty:
            if flash_numbers:
                flash("no samples of " + conc + " amplified", 'error')
            continue
        statdf['concentration'].append(conc)
        statdf['samples'].append(len(tmpdf))
        statdf['average cycle'].append(np.mean(tmpdf['thresholdCycle']))
        statdf['minimum cycle'].append(min(tmpdf['thresholdCycle']))
        statdf['maximum cycle'].append(max(tmpdf['thresholdCycle']))
        if flash_numbers:
            flash(str(np.mean(tmpdf['thresholdCycle'])) + " cycles is the average for samples of " + conc, 'success')
            flash(str(min(tmpdf['thresholdCycle'])) + " cycles is the minimum for samples of " + conc, 'success')
            flash(str(max(tmpdf['thresholdCycle'])) + " cycles is the maximum for samples of " + conc, 'success')

        for i in [60, 80, 100]:
            tpos = len(tmpdf[tmpdf['thresholdCycle'] < i])
            statdf['percent positive_' + str(i)].append(round(tpos / len(df[df['concentration'] == conc]) * 100, 2))
            if flash_numbers:
                flash(str(tpos) + "/" + str(len(df[df['concentration'] == conc])) +
                      " of " + conc + " samples tested positive with the cutoff at " + str(i), 'success')
        if flash_numbers:
            flash("-----------------------------------------------------------------------------------------------------------------------------------", 'success')
    return pd.DataFrame.from_dict(statdf)


def I3_replaces_empty_thresholds(df):
    df.insert(0, 'inflection3', [dict(x)[str(2)] if (len(x) > 0 and type(x[0]) == list and dict(x).get(str(2)))
                                 else np.nan for x in df['inflections']])
    mask = df['thresholdCycle'].isnull()
    df = df.fillna(250)
    df['thresholdCycle'] = df['thresholdCycle'].mask(mask, df['inflection3'])
    return df


def validate_covid_default(self, wellindex, cq_value):
    negative_result = False

    if str(cq_value) == 'nan':
        ct_value = None
        negative_result = True
    else:
        cq_value = float(cq_value)

    # check negative controls
    if 8 <= wellindex < 12:
        if not negative_result:
            flash('Well %s, a negative control, showed up positive at %s cycles' % (info[1], ct_value), 'error')
        return False

    # check positive controls
    elif 92 <= wellindex < 96:
        if negative_result:
            flash('Well %s, a positive control, is negative' % info[1], 'error')
            return False

    # check beta actin
    elif wellindex % 4 == 3:
        if negative_result:
            flash('Well %s, Beta Actin, is negative' % info[1], 'error')
        return False

    return True


def run_covid_default(self, wellindex, well, total_index):
    negative_result = 'N'

    if wellindex % 4 == 0:
        if wellindex == 0:
            self.sample_number = 0
            self.covid_results = []
        self.sample_dict = dict(SampleNumber=self.sample_number,
                                SampleID=well.get_label().split('__')[0],
                                Egene=negative_result,
                                RdRP=negative_result,
                                Ngene=negative_result,
                                ACT=negative_result,
                                Summary=negative_result)
        self.sample_number += 1
        self.positive_count = 0

    # check E
    if wellindex % 4 == 0:
        check_sample(self, 'Egene', well)

    # check R
    if wellindex % 4 == 1:
        check_sample(self, 'Ngene', well)

    # check N
    if wellindex % 4 == 2:
        check_sample(self, 'RdRP', well)

    # check B
    if wellindex % 4 == 3:
        check_sample(self, 'ACT', well)

        self.sample_dict['Summary'] = negative_result if self.positive_count == 0 else self.positive_count

        if wellindex == total_index - 1 or 'PC' in self.sample_dict['SampleID'].split(' '):
            self.sample_dict['Summary'] = 'Invalid'
            if self.positive_count == 3:
                self.sample_dict['Summary'] = 'Valid'

        elif wellindex == 11:
            self.sample_dict['Summary'] = 'Invalid'
            if self.positive_count == 0:
                self.sample_dict['Summary'] = 'Valid'

        self.covid_results.append(self.sample_dict)
    return


def check_sample(self, name, well):
    negative_result = 'N'
    if well.get_cq() is None:
        self.sample_dict[name] = negative_result
    elif well.get_cq() < 60:
        self.sample_dict[name] = float(well.get_cq())
        if name != 'ACT':
            self.positive_count += 1
    return
