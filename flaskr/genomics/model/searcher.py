import pandas as pd
import re
import os
from flask import current_app, flash

from flaskr.framework.model.Io.txt_file import TXTFILE
from flaskr.framework.exception import InvalidArgument
from flaskr.genomics.model.helper import get_reverse


class Searcher():
    def __init__(
            self,
    ):
        self.sequence = ''
        self.location = -1
        self.ignore_location = -1
        self.primer = ''
        self.reverse = False
        self.request = None
        self.max_line_checks = 5

    def execute(self, request):
        self.request = request

        primers = self.get_primers()

        fasta_files = []
        try:
            for file in self.request.files.getlist("fastafile[]"):
                fasta_files.append(TXTFILE(file))
        except InvalidArgument:
            flash('An invalid file was provided, please make sure you are uploading a .txt file', 'error')
            return None

        result_string = ['']
        for p, primer in enumerate(primers):
            primer = primer.lower()
            self.primer = primer
            result_string.append('Primer: ' + self.primer)
            flash('Primer: ' + self.primer)

            for file in fasta_files:
                result_string.append('File: ' + file.name)
                flash('File: ' + file.name)

                search_count = 0
                self.reverse = False
                self.location = -1
                primer_not_found = False

                for idx, (name, self.sequence) in enumerate(file.read()):
                    try:
                        re.match("[AaTtGgCc]*", self.sequence)
                    except TypeError:
                        flash('invalid sequence format, please check your primer sequence and try again', 'error')
                        result_string.append('invalid sequence format, please check your primer sequence and try again')
                        current_app.logger.error("invalid sequence, please check primer sequence %s and try again"
                                                 % name)
                        break

                    if self.reverse:
                        get_reverse(self)

                    # find location of primer
                    if search_count < 3:  # only search first 3 sequences for the primer location
                        search_count += 1
                        if not self.get_location():
                            primer_not_found = True
                            continue
                        else:
                            search_count = 0
                    elif primer_not_found:
                        break
                    self.sequence = self.sequence[self.location:self.location + len(self.primer)]

                    # search aligned location for differences
                    differences = []
                    if primer not in self.sequence and self.location > -1:
                        for seq_idx, letter in enumerate(self.sequence):
                            if letter != self.primer[seq_idx] and letter != 'n':
                                differences.append(
                                    'position %s, change from %s -> %s' % (
                                        str(seq_idx), str(primer[seq_idx]), str(letter)))

                    if len(differences) > len(primer)/2:
                        # probably identified the wrong location if the next sequences aren't even close
                        self.reset_location()
                        current_app.logger.error('There may be an error in the primer %s found in file %s, more'
                                                 'than half the located alignment differs from the expected primer'
                                                 % (self.primer, file.name))
                        continue

                    if len(differences) > 0:
                        result_string.append('   ' + name + '')
                        result_string.append('   ' + ''.join(differences))
                        result_string.append('')
                        flash(name)
                        flash(''.join(differences))

                if primer_not_found:
                    result_string.append('     not found')
                    flash('     not found')
            result_string.append('---------------------------------------')
            flash('---------------------------------------')

        for file in fasta_files:
            file.delete()
        return result_string

    def get_primers(self):
        if not self.request.files.get('primer_list'):
            primer_file = os.path.join(current_app.static_folder, 'files', 'primers.xlsx')
        else:
            primer_file = self.request.files['primer_list']
        df = pd.read_excel(primer_file, sheet_name='Sheet1')
        return df['Sequence']

    def reset_location(self):
        self.ignore_location = self.location
        self.location = -1
        self.get_location()

    def get_location(self):
        if self.location >= 0:
            return True

        if self.primer in self.sequence:
            self.location = self.sequence.find(self.primer)
            return True

        get_reverse(self)
        if self.primer in self.sequence:
            self.location = self.sequence.find(self.primer)
            self.reverse = True
            return True

        # TODO: only identifying strings with less than 4 character differences from the primer
        # TODO: also this makes the program SLOW!
        wild_cards = 1
        while not self.get_wild_card_primer(wild_cards):
            get_reverse(self)
            wild_cards += .5

            if wild_cards >= 4:
                return False

        return False

    def get_wild_card_primer(self, wild_cards):
        wild_cards = int(wild_cards)
        num_letters = len(self.primer)

        for idx in range(num_letters):
            wild_primer = self.primer[:idx] + '.' + self.primer[idx + 1:]
            if wild_cards == 1:
                single_wild = re.compile(wild_primer)
                search = re.search(single_wild, self.sequence)
                if search is not None and self.location != self.ignore_location:
                    self.location = search.span(0)[0]
                    return True

            elif wild_cards == 2:
                for idx2 in range(idx + 1, num_letters):
                    double_wilds = re.compile(wild_primer[:idx2] + '.' + wild_primer[idx2 + 1:])
                    search = re.search(double_wilds, self.sequence)
                    if search is not None and self.location != self.ignore_location:
                        self.location = search.span(0)[0]
                        return True

            elif wild_cards == 3:
                for idx2 in range(idx + 1, num_letters):
                    double_wilds = wild_primer[:idx2] + '.' + wild_primer[idx2 + 1:]
                    for idx3 in range(idx2 + 1, num_letters):
                        triple_wilds = re.compile(double_wilds[:idx3] + '.' + double_wilds[idx3 + 1:])
                        search = re.search(triple_wilds, self.sequence)
                        if search is not None and self.location != self.ignore_location:
                            self.location = search.span(0)[0]
                            return True

        return False
