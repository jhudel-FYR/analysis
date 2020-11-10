from itertools import groupby
from flask import flash, current_app
import re
from Bio.SeqUtils import MeltingTemp as mt

from flaskr.framework.model.Io.txt_file import TXTFILE
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.request.response import Response

PRIMER_NAME = {'0': 'F',
               '1': 'IR',
               '2': 'C',
               '3': 'IF',
               '4': 'R'}


class Designer():
    def __init__(
            self,
    ):
        self.results = []
        self.sequence = ''
        self.complement = ''
        self.request = None
        self.primer = None
        self.primer_starts = {'0': [], '1': [], '2': [], '3': [], '4': []}
        self.primer_ends = {'0': [], '1': [], '2': [], '3': [], '4': []}
        self.primer_combos = []
        self.primer_sequences = []
        self.startidx = 0

    def execute(self, request) -> Response:
        self.request = request

        text_file = []
        try:
            text_file = TXTFILE(self.request.files['sequence'])
        except InvalidArgument:
            return Response(False, 'An invalid file was provided, please make sure you are uploading a .txt file')

        for name, sequence in text_file.read():
            if len(sequence) == 0:
                continue
            if type(sequence) == str:
                self.sequence = sequence
            else:
                self.sequence = sequence[0]

            self.sequence = self.sequence.upper()

            try:
                re.match("[AaTtGgCc]*", self.sequence)
            except TypeError:
                flash('invalid sequence format, please check your primer sequence and try again', 'error')
                current_app.logger.error("invalid sequence, please check primer sequence %s and try again" % name)
                break

            self.get_reverse()

            forward_list = self.get_possible('0')
            for fi, forward in enumerate(forward_list):
                forward_start = self.primer_starts['0'][fi]
                forward_end = self.primer_ends['0'][fi]
                primer_combo = [[forward_start, forward_end]]

                self.startidx = forward_end
                record_total_possible = []
                for p_idx in PRIMER_NAME.keys():
                    if PRIMER_NAME[p_idx] == 'F':
                        continue
                    self.primer_starts[p_idx] = []
                    self.primer_ends[p_idx] = []
                    possible = self.get_possible(p_idx)
                    record_total_possible.append(len(possible))
                    if len(possible) > 0:
                        for possible_idx, possible_start in enumerate(self.primer_starts[p_idx]):
                            if possible_start not in [i[0] for combo in self.primer_combos for i in combo]:
                                primer_combo.append([possible_start, self.primer_ends[p_idx][possible_idx]])
                                self.startidx = self.primer_ends[p_idx][possible_idx]
                                break
                if len(primer_combo) == 5:
                    self.primer_combos.append(primer_combo)
                    for idx, possible_count in enumerate(record_total_possible):
                        flash('Primer %s has %s possibilities for Forward # %s starting at %s'
                              % (PRIMER_NAME[str(idx+1)], possible_count, fi, self.primer_starts['0'][fi]))
                    flash('------------------------')

        text_file.delete()
        self.get_combinations()

        return Response(True, '')

    def get_form_name(self, type):
        return list(type)[0]

    def get_distance(self, start_value, primer_index, name):
        form_name = self.get_form_name(name) + '_spacing'
        min_f_spacing = int(self.request.form[form_name + str(primer_index)].split('-')[0])
        max_f_spacing = int(self.request.form[form_name + str(primer_index)].split('-')[1])
        if start_value < min_f_spacing: start_value = min_f_spacing
        if start_value > max_f_spacing: start_value = max_f_spacing
        return start_value

    def get_reverse(self):
        self.complement = self.sequence.replace('A', '%%').replace('T', 'A').replace('%%', 'T')
        self.complement = self.complement.replace('G', '%%').replace('C', 'G').replace('%%', 'C')

    def get_possible(self, primer_index):
        min_length = int(self.request.form['length' + primer_index].split('-')[0])
        max_length = int(self.request.form['length' + primer_index].split('-')[1])
        possibilities = []
        for idx in range(self.startidx, len(self.sequence)):
            for endidx in range(idx + min_length, idx + max_length):
                if endidx >= len(self.sequence):
                    break
                self.primer = self.sequence[idx:endidx]
                if PRIMER_NAME[str(primer_index)] in ['IR', 'B']:
                    self.primer = self.complement[idx:endidx]
                if not self.check_conditions(primer_index):
                    continue
                possibilities.append(self.primer)
                self.primer_starts[primer_index].append(idx)
                self.primer_ends[primer_index].append(endidx)
        return possibilities

    def check_conditions(self, primer_index):
        if not self.check_gc_content():
            return False
        if not self.check_gc_clamp():
            return False
        if not self.check_Tm(primer_index):
            return False
        if not self.check_misc():
            return False
        return True

    def check_gc_content(self):
        min_gc = float(self.request.form['gc_content'].split('-')[0])
        max_gc = float(self.request.form['gc_content'].split('-')[1])
        g_count = self.primer.count('G')
        c_count = self.primer.count('C')
        total_percent = (g_count + c_count)/len(self.primer)
        total_percent = total_percent*100
        if min_gc > total_percent or max_gc < total_percent:
            return False
        return True

    def check_gc_clamp(self):
        if self.primer[-5:].count('G') > 3:
            return False
        if self.primer[-5:].count('C') > 3:
            return False
        return True

    def calculate_Tm(self, primer):
        return mt.Tm_NN(primer,
                        nn_table=mt.RNA_NN1,
                        Na=float(self.request.form['na_concentration']),
                        Mg=float(self.request.form['mg_concentration']),
                        dNTPs=float(self.request.form['dNTPs']))

    def check_Tm(self, p_idx):
        min_Tm = int(self.request.form['tm' + p_idx].split('-')[0])
        max_Tm = int(self.request.form['tm' + p_idx].split('-')[1])

        Tm = self.calculate_Tm(self.primer)
        #nn_table=mt.RNA_NN1 (Freier) or mt.DNA_NN1 (Sugimoto '95)
        #mt.DNA_NN1(Breslauer) and mt.DNA_NN2 (Sugomoto '96)
        # TODO: adjust and verify this calculator
        # print(self.primer, Tm)

        if Tm < min_Tm or Tm > max_Tm:
            return False
        return True

    def check_misc(self):
        groups = groupby(self.primer)
        for label, group in groups:
            if sum(1 for _ in group) > 4: #more than 4 of one base
                return False
        # TODO: look for repeats
        return True

    def get_combinations(self):
        for primer_combo in self.primer_combos:
            if len(primer_combo) != 5:
                print('help! this combination doesnt have 5 primers!')
                continue
            primer_sequence = []
            endidx = 0
            for idx, primer in enumerate(primer_combo):
                primer_string = self.sequence[primer[0]:primer[1]]
                if PRIMER_NAME[str(idx)] in ['IR', 'B']:
                    primer_string = self.complement[primer[0]:primer[1]]

                primer_sequence.append(dict(index=[endidx, primer[0]],
                                            string=primer_string,
                                            info=dict(Tm=round(self.calculate_Tm(self.sequence[primer[0]:primer[1]]), 3),
                                                      name=PRIMER_NAME[str(idx)])))
                endidx = primer[1]
            primer_sequence.append(dict(index=[endidx, len(self.sequence)],
                                        string='',
                                        info=None))
            self.primer_sequences.append(primer_sequence)
