import re
from flask import flash, current_app
from bson import ObjectId
from urllib.parse import unquote, parse_qs, parse_qsl
import json

from flaskr.model.helpers.calcfunctions import get_regex_response
from flaskr.framework.model.request.response import Response


def build_input_dicts(self):
    raw_dict = json.loads(unquote(self.form.get("json")))

    for swap in raw_dict['swaps']:
        self.swaps[swap[0]] = swap[1]
        self.swaps[swap[1]] = swap[0]

    for error in raw_dict['errors']:
        self.errorwells.append(error)

    for groupindex, group in enumerate(raw_dict['groups']):
        self.groupings[groupindex] = []
        for repindex, replicate in enumerate(group['replicates']):
            self.groupings[groupindex].append(dict(label=replicate['label'],
                                                   designation=replicate['designation'],
                                                   wells=replicate['wells']))


def get_concentrations(string):
    if string.endswith('fM'):
        return float(re.match(r'^\d+', string).group(0)) / 1000
    elif string.endswith('pM'):
        return float(re.match(r'^\d+', string).group(0))
    elif string.endswith('nM'):
        return float(re.match(r'^\d+', string).group(0)) * 1000
    else:
        return -1


def clean_labels(original_list):
    label_list = []
    for label in original_list.split(' '):
        label = re.sub('-', ' ', label)
        label = re.sub('_', ' ', label)
        label_list.extend([word for word in label.split(' ') if word != ''])
    return label_list


def determine_labelling(self, well, wellindex):
    if not any(self.groupings):
        combined_label = clean_labels(well.get_label_history())
        replicate_label = ' '.join(combined_label[1:])
        group_label = well.get_label().split('__')[0]
        if wellindex == 0:
            self.replicates[replicate_label] = dict(sample=self.id['sample'],
                                                    group=self.id['group'],
                                                    replicate=self.id['replicate'],
                                                    replicate_id=self.id['replicate_id'])

        elif replicate_label not in self.replicates.keys():
            self.id['sample'] += 1
            self.id['replicate'] += 1
            self.id['replicate_id'] = ObjectId()
            self.replicates[replicate_label] = dict(sample=self.id['sample'],
                                                    group_label=well.get_label().split('__')[0],
                                                    replicate=self.id['replicate'],
                                                    replicate_id=self.id['replicate_id'])

        if group_label not in self.groups.keys():
            self.groups[group_label] = self.id['group']
            self.id['group'] += 1

        well['group'] = self.groups[group_label]
        well['sample'] = self.replicates[replicate_label]['sample']
        well['replicate'] = self.replicates[replicate_label]['replicate']
        well['replicate_id'] = self.replicates[replicate_label]['replicate_id']
        return [well, True]

    for group in self.groupings.keys():
        for replicate in self.groupings[group]:
            if well.get_excelheader() in replicate['wells']:

                if replicate['label'] not in self.replicates.keys():
                    self.id['sample'] += 1
                    self.id['replicate'] += 1
                    self.id['replicate_id'] = ObjectId()
                    self.replicates[replicate['label']] = dict(sample=self.id['sample'],
                                                               replicate=self.id['replicate'],
                                                               replicate_id=self.id['replicate_id'])

                well['label'] = replicate['label'] + '_' + replicate['designation']
                well['group'] = group
                well['sample'] = self.replicates[replicate['label']]['sample']
                well['replicate'] = self.replicates[replicate['label']]['replicate']
                well['replicate_id'] = self.replicates[replicate['label']]['replicate_id']

                return [well, True]
    return [well, False]


def save_temporary_swap(self, originwell, type='dest'):
    if type == 'origin':
        self.swap_from[originwell.get_excelheader()] = originwell
    else:
        self.swap_to[originwell.get_excelheader()] = originwell


def swap_wells(self, origin_well):  # replaces origin well info with destination well info
    # TODO: swaps isn't working properly'
    # Save well info to a temporary list of origin and destination wells
    if origin_well.get_excelheader() in self.swaps.keys():
        save_temporary_swap(self, origin_well, type='origin')
    if origin_well.get_excelheader() in self.swaps.values():
        save_temporary_swap(self, origin_well, type='dest')

    # well was provided only as a destination well
    if self.swaps.get(origin_well.get_excelheader()) is None:
        flash('%s was overwritten from a one-way swap' % origin_well.get_excelheader(), 'error')
        return None

    # determine if destination well has already been recorded
    dest_well_header = self.swaps[origin_well.get_excelheader()]
    if dest_well_header in self.swap_to.keys():
        # replace labels and remove from temporary lists
        origin_well.edit_labels(dict(group=self.swap_to[dest_well_header]['group'],
                                     sample=self.swap_to[dest_well_header]['sample'],
                                     replicate=self.swap_to[dest_well_header]['replicate'],
                                     label=self.swap_to[dest_well_header]['label']))

        try:
            self.swap_from.pop(origin_well.get_excelheader())
            self.swap_to.pop(dest_well_header)
            self.swaps.pop(origin_well.get_excelheader())
        except KeyError:
            current_app.logger.error('Error deleting swap from swap dictionary')

        return origin_well
    return None


def add_remaining_swaps(self):
    delete = []
    for origin_well_key, dest_well_key in self.swaps.items():
        if origin_well_key in self.swap_from and dest_well_key in self.swap_to:
            origin_well = self.swap_from[origin_well_key]
            dest_well = self.swap_to[dest_well_key]
            origin_well.edit_labels(dict(group=dest_well.get_group(),
                                         sample=dest_well.get_sample(),
                                         replicate=dest_well.get_replicate(),
                                         label=dest_well.get_label()))
            self.swap_from.pop(origin_well_key)
            self.swap_to.pop(dest_well_key)
            delete.append(origin_well_key)

            self.add_measurement(origin_well)
        else:
            current_app.logger.error('A swap could not be completed, dataset: %s' % self.dataset.get_id())
    for key in delete:
        self.swaps.pop(key)


def validate_target(self, target):
    if re.match(r'^\d+\s*[a-z]+\/*[a-zA-Z]+?\s+\w?', target) is not None:
        name = target
        unit = get_regex_response(target, 'unit')
        component = self.component_repository.search_by_name_and_unit(name, unit)
        if component is not None:
            return Response(True, component['_id'])
        return Response(False, 'Target does not exist in the component library')

    return Response(False, 'Target units and name could not be identified')
