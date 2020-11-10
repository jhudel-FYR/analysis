import os
from Bio import SeqIO

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flaskr.framework.exception import InvalidArgument


class TXTFILE():
    FOLDER = 'text'
    ALLOWED_EXTENSION = ['txt', 'fasta', 'fq', 'fastqsanger', 'fastq']
    name = ''
    file = None
    filetype = None

    def __init__(self, file: FileStorage = None, name: str = ''):
        if name == '':
            if file is not None and not self.is_allowed(file.filename):
                raise InvalidArgument('Only text or fasta files are allowed')

            if file.filename != secure_filename(file.filename):
                raise InvalidArgument('Unsecure filename provided')

            self.name = file.filename
            self.file = file
            self.save()
        else:
            self.name = name

    def is_allowed(self, filename: str) -> bool:
        allowed = True
        if '.' not in filename:
            allowed = False

        self.filetype = filename.rsplit('.', 1)[1].lower()
        if self.filetype not in self.ALLOWED_EXTENSION:
            allowed = False
        if self.filetype.startswith('f'):
            self.filetype = 'fasta'

        return allowed

    def get_file_save_path(self) -> str:
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.FOLDER, self.name)

    def read(self):
        self.error_count = 0

        if self.filetype == 'fasta':
            fasta_sequences = SeqIO.parse(open(self.get_file_save_path()), 'fasta')
            for idx, fasta in enumerate(fasta_sequences):
                name, self.sequence = fasta.id, str(fasta.seq)
                if self.is_invalid_line(self.sequence):
                    current_app.logger.warning('invalid line found for sequence %s', self.sequence)
                yield name, self.sequence
        elif self.filetype == 'txt':
            # TODO: research different file types (Tre's document)
            with open(self.get_file_save_path(), 'r') as f:
                sequence = f.readlines()
                if self.is_invalid_line(sequence):
                    current_app.logger.warning('invalid line found for sequence %s', sequence)
                yield '', sequence

    def save(self):
        self.file.save(self.get_file_save_path())

    def delete(self):
        os.remove(self.get_file_save_path())

    def is_invalid_line(self, line) -> bool:
        if type(line) != str:
            self.error_count += 1
            return True
        return False
