from flask import redirect, url_for, flash, current_app
from io import BytesIO, StringIO
import datetime
import pdfkit
import jinja2
import os
from os.path import basename
import zipfile
import pandas as pd
import numpy as np
from PyPDF2 import PdfFileMerger

from flaskr.clinical_data.sample_models.collection import Collection as SampleCollection
from flaskr.clinical_data.sample_models.sample import SPECIMAN, INTERPRETATION, REPORT
from flaskr.framework.model.request.response import Response
from flaskr.clinical_data.view_model.importprocessor import ImportProcessor


def create_html(data, template):
    image_file = 'https://analysis.fyrdiagnostics.com/logo/FYR-logo.png'
    template_loader = jinja2.FileSystemLoader(searchpath="flaskr/clinical_data/templates")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(template)
    output_text = template.render(sample=data, image=image_file)
    return output_text


def merge_required_files(filename, filepath):
    # merge with required CDC fact sheets
    merger = PdfFileMerger()
    for pdf in [filename + '_temp.pdf', os.path.join(current_app.static_folder, 'files', 'EUA-CDC-panel-hcp.pdf'),
                os.path.join(current_app.static_folder, 'files', 'EUA-CDC-panel-patient.pdf')]:
        merger.append(pdf, import_bookmarks=False)
    merger.write(filepath + '.pdf')
    merger.close()


def write_maestro_templates(positions, fyr_ids):
    files = None
    plate_templates = dict()
    for plate in range(np.ceil(len(positions) / 30)):
        # open the saved templates here, with the 'S-' labels where the fyr_id will go
        new_plate = None
        plate_templates[plate].append(new_plate)
    for (position, id) in zip(positions, fyr_ids):
        if position < 31:
            current_plate = plate_templates[0]
        elif 31 <= position < 61:
            current_plate = plate_templates[1]
        elif 61 <= position <= 90:
            current_plate = plate_templates[2]
        else:
            current_app.logger.error('extra position (%s) id (%s) allocated to a rack' % (position, id), 'error')
            break
        current_plate[position, 'Sample'] = id

    for plate in plate_templates.values():
        plate.to_excel(plate)  # or to csv??

    return files


class Writer:
    def __init__(self,
                 writer = None,
                 dataset_id: str = ''):
        self.writer = writer
        self.dataset_id = dataset_id
        self.time = []
        self.workbook = None
        self.rowshift = 0
        self.columnshift = 0

    def write_covid_to_excel(self, id, provider=None):
        collection = SampleCollection()
        collection.add_filter('dataset_id', id)
        if provider is not None:
            collection.add_filter('provider_id', provider)
        df = pd.DataFrame(list(collection.find()))

        if df.empty:
            return Response(False, 'None found')

        # translate report and interpretation
        interpretation_dict = dict(INTERPRETATION)
        df['interpretation'] = df['report'].apply(lambda x: interpretation_dict[str(x)])
        report_dict = dict(REPORT)
        df['report'] = df['report'].apply(lambda x: report_dict[str(x)])

        prioritized_columns = ['sample_id1', 'sample_id2', 'interpretation', 'report', 'test_type']
        df = df.reindex(columns=(prioritized_columns + list([a for a in df.columns if a not in prioritized_columns])))

        # clean up targets
        split_targets = df['targets'].apply(pd.Series)
        for target_name in df['targets'].iloc[0].keys():
            df.insert(4, target_name, split_targets[target_name])

            if provider is not None:
                df[target_name] = df[target_name].apply(lambda x: 'Positive' if 0 < float(x) < 40 else 'Negative')

        df = df.drop(columns=['_id', 'date_collected', 'date_received', 'targets', 'rack_id', 'rack_position', 'status'])

        if provider is not None:
            speciman_dict = dict(SPECIMAN)
            df['speciman_type'] = df['speciman_type'].apply(lambda x: speciman_dict[x])
            df = df.drop(columns=['dataset_id', 'provider_id', 'invalid_plate'])

        df.to_excel(self.writer, sheet_name='summary', index=False)
        self.stats_excel_formatting('summary', df)

        return Response(True, '')

    def write_covid_official(self, include_invalid=False):
        sample_collection = SampleCollection()
        sample_collection.add_filter('dataset_id', self.dataset_id)

        results = []
        for sample in sample_collection:
            if not include_invalid:
                if sample['report'] < 0:
                    continue

            sample['test_date'] = sample['date_tested'].date()
            sample['experiment_id'] = self.dataset_id[:9]
            sample['converted_report'] = sample.get_report()
            sample['converted_interpretation'] = sample.get_interpretation()
            sample['converted_targets'] = dict()
            for name, value in sample['targets'].items():
                sample['converted_targets'][name] = self.deidentify_target(value)

            sample['previous_results'] = []
            previous_sample_collection = SampleCollection()
            previous_sample_collection.add_filter('sample_id1', sample.get_sample_id1())
            previous_sample_collection.add_filter('sample_id2', sample.get_sample_id2())
            previous_sample_collection.add_filter('date_tested', sample['date_tested'], '$ne')
            previous_sample_collection.add_order('date_tested', -1)
            for previous_sample in previous_sample_collection:
                if previous_sample['report'] < 0:
                    continue
                sample['previous_results'].append(dict(date=previous_sample.get_test_date(),
                                                       result=previous_sample.get_report()))
                if len(sample['previous_results']) > 15:
                    break
            results.append(sample)

        return results

    def deidentify_target(self, value):
        if 0 < value < 40:
            return 'Positive'
        return 'Negative'

    def output_results(self, id):
        results = self.write_covid_official()
        try:
            path_wkhtmltopdf = current_app.config['WKHTMLTOPDF_PATH']
            if current_app.config['DEBUG']:
                path_wkhtmltopdf = r'/mnt/c/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        except OSError:
            flash('Error #1, please notify a developer', 'error')
            return None

        unique_providers = []
        memory_file = BytesIO()

        with zipfile.ZipFile(memory_file, 'w') as zf:
            for sample in results:
                if sample.get_provider() not in unique_providers:
                    unique_providers.append(sample.get_provider())

                filename = sample.get_sample_id1() + '_' + str(sample.get_test_date().strftime("%Y%m%d")) + \
                           '_' + sample.get_provider()
                if sample.get_fyr_id().startswith('Z000'):
                    continue

                pdf_filepath = os.path.join('instance', 'download', filename)

                # create html
                html = create_html(data=sample, template="sampleresults.html")

                # create pdf
                try:
                    pdfkit.from_string(html, filename + '_temp.pdf', configuration=config)
                except IOError:
                    current_app.logger(pdfkit.from_string(html, filename + '_temp.pdf', configuration=config))
                    flash('Error #2, please notify a developer', 'error')
                    continue

                merge_required_files(filename, pdf_filepath)

                # save pdf to zip
                zf.write(pdf_filepath + '.pdf', basename(filename) + '.pdf')

                # remove temp pdfs
                # TODO: improve this process
                os.remove(filename + '_temp.pdf')
                os.remove(pdf_filepath + '.pdf')

            # Lab summary
            excel_stream = BytesIO()
            excelwriter = pd.ExcelWriter(excel_stream, engine='xlsxwriter')
            writer = Writer(writer=excelwriter, dataset_id=id)
            response = writer.write_covid_to_excel(id)
            excelwriter.save()
            excel_stream.seek(0)
            if response.is_success():
                zf.writestr('lab_summary.xlsx', excel_stream.getvalue())

            # provider summary
            for provider in unique_providers:
                excel_stream = BytesIO()
                excelwriter = pd.ExcelWriter(excel_stream, engine='xlsxwriter')
                writer = Writer(writer=excelwriter, dataset_id=id)
                response = writer.write_covid_to_excel(id, provider=provider)
                excelwriter.save()
                excel_stream.seek(0)
                if response.is_success():
                    zf.writestr(provider + '_summary.xlsx', excel_stream.getvalue())

        memory_file.seek(0)
        return memory_file

    def stats_excel_formatting(self, sheetname, df):
        worksheet = self.writer.sheets[sheetname]
        for idx, column in enumerate(df.columns):
            lengths = [len(x) for x in df.loc[:, column].astype('str')]
            lengths.append(len(column))
            maxlength = max(lengths)
            worksheet.set_column(idx, idx + 1, maxlength + 3)

    def get_sample_list_for_pdf(self, provider):
        sample_collection = SampleCollection()
        sample_collection.add_filter('provider_id', provider)
        # TODO: verify that only newly submitted samples show up?
        # sample_collection.add_filter('status', 1)
        sample_collection.add_filter('date_tested', None)
        sample_collection.add_filter('dataset_id', None)

        samples = []
        for sample in sample_collection:
            samples.append(dict(fyr_id=sample.get_fyr_id(),
                                sample_id1=sample.get_sample_id1(),
                                sample_id2=sample.get_sample_id2()))
        return dict(samples=[dict(item) for item in samples],
                    provider=provider)
