import numpy as np
from scipy.signal import peak_widths
from flask import current_app

from flaskr.model.helpers.calcfunctions import fit_poly_equation, get_expected_values, square


def get_peaks(self, well, derivativenumber, derivative, allpeaks) -> {}:
    timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
    # For gPCR experiments, we need to skip the first peak on the first dIndex (derivativenumber)
    num_of_peaks = 1 if derivativenumber == 1 and self.form.get('exp_type') in ["gPCR", 'COVID'] else 2
    for i in range(num_of_peaks):
        if derivativenumber == 1:
            if i == 0:
                #first derivative largest peak
                #second phase
                inflectionnumber = 3
            else:
                #first derivative second largest derivative
                #first phase
                inflectionnumber = 1
        else:
            if i == 0:
                #second derivative largest peak
                #start of second phase
                timediff = [(timediff[t] + timediff[t + 1]) / 2 for t in range(len(timediff) - 1)]
                inflectionnumber = 2
            else:
                # second derivative largest trough
                # end of second phase
                inflectionnumber = 4

        maxpeak = list(np.where(derivative == max(derivative)))[0]

        # try to remove initial noise if it is identified as a peak
        if len(maxpeak) == 1 and maxpeak < 3:
            derivative = remove_peak(derivative, peakindex=0, initpeak=True)
            maxpeak = list(np.where(derivative == max(derivative)))[0]

        if not validate_peak(maxpeak, derivative):
            continue

        # get the [width, width height, left_ips, right_ips] from the scipy peak width function
        widths = peak_widths(derivative, maxpeak)
        leftside = int(np.floor(widths[2][0]))
        rightside = np.min([int(np.ceil(widths[3][0])), len(derivative)-1])
        if rightside - leftside < 2:
            current_app.logger.error('Width finding error 2, dataset: %s' % self.dataset_id)
            continue

        # fit a polynomial to the derivative
        polycoefs = fit_poly_equation(self.time[leftside:rightside],
                                      derivative[leftside:rightside])

        # Calculate the inflection point as the maximum of the fit polynomial
        # Calculate the expected RFU value at the inflection point by fitting a new polynomial to the original time/rfus
        # Collect all information into an inflection dictionary
        inflection = -polycoefs[1] / (2 * polycoefs[0])
        expected_rfu = get_expected_values(self, well, -polycoefs[1] / (2 * polycoefs[0]), [leftside, rightside])[0]
        if not validate_results(expected_rfu, well.get_rfus(), inflection):
            continue
        allpeaks[str(inflectionnumber)] = dict(inflection=inflection,
                                               rfu=expected_rfu,
                                               location=maxpeak)

        if derivativenumber == 2 and i == 0:
            inflectionnumber += 1
            derivative = remove_peak(derivative, maxpeak[0], getnegativedata=True)
        else:
            derivative = remove_peak(derivative, maxpeak[0])
    return allpeaks


def remove_peak(data, peakindex, getnegativedata=False, initpeak=False):
    # Finds the lowest trough that occurs immediately before or after the peak
    # replaces the peak with the trough value
    # for 'init peak' remove the initial peak
    trough = data[peakindex]
    if initpeak:
        init = 0
        for idx, i in enumerate(data):
            if idx + 1 == len(data):
                continue
            if data[idx + 1] < i:
                init = idx
            else:
                break
        data[:init] = [data[init] for i in range(init)]
        return data
    for i in range(peakindex, 1, -1):
        if data[i-1] <= data[i]:
            trough = data[i-1]
        else:
            data[i:peakindex] = trough
            break
    if getnegativedata:
        for i in range(peakindex, len(data)-1):
            if data[i+1] <= trough:
                data[:i+1] = trough
                return -data
    return data[:peakindex]


def validate_peak(peak, derivative):
    if len(peak) > 1:
        return False
    if max(derivative) < 7:
        return False
    if peak == 0:
        return False
    if peak >= len(derivative) - 1:
        return False
    return True


def validate_results(expected_rfu, possible_rfus, inflection):
    if inflection < 0 or inflection > len(possible_rfus):
        return False
    if expected_rfu > np.max(possible_rfus):
        return False
    if expected_rfu < 0:
        return False
    rmin = max(0, np.floor(inflection-2))
    rmax = min(len(possible_rfus), np.ceil(inflection + 2))
    possible_range = [item for item in possible_rfus[int(rmin):int(rmax)]]
    if len(possible_range) == 0:
        return False
    if expected_rfu < np.min(possible_range)-50 or expected_rfu > np.max(possible_range) + 50:
        return False
    return True
