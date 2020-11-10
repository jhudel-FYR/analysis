from Bio.Blast import NCBIWWW
import pandas as pd
import os
import ssl
from flask import current_app, flash

from flaskr.framework.model.Io.txt_file import TXTFILE
from flaskr.framework.exception import InvalidArgument


class Blaster():
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

        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context


        self.request = request

        primers = self.get_primers()

        fasta_file = []
        try:
            fasta_file = TXTFILE(self.request.files['fastafile'])
        except InvalidArgument:
            flash('An invalid file was provided, please make sure you are uploading a .txt file', 'error')
            return None

        output_file = 'results.txt'
        output_file = os.path.join(current_app.config['DOWNLOAD_FOLDER'], output_file)

        with open(output_file, 'w') as out_file:
            out_file.write('Cross Reactivity results with BLASTN')

            for idx, sequence_data in enumerate(fasta_file.read()):
                try:
                    result_handle = NCBIWWW.qblast('blastn', 'nt', sequence_data)
                except ValueError as e:
                    flash(str(e), 'error')
                    return None
                out_file.write(result_handle.read())
                break

            out_file.write('---------------------------------------\n')
            flash('---------------------------------------')

        fasta_file.delete()
        os.remove(os.path.join(current_app.config['DOWNLOAD_FOLDER'], 'results.txt'))
        return output_file

    def get_primers(self):
        if not self.request.files.get('primer_list'):
            primer_file = os.path.join(current_app.static_folder, 'files', 'primers.xlsx')
        else:
            primer_file = self.request.files['primer_list']
        df = pd.read_excel(primer_file, sheet_name='Sheet1')
        return df['Sequence']



