# -*- coding: utf-8 -*-

import os
import subprocess

from itertools import chain, imap
from collections import defaultdict
from operator import itemgetter
from copy import deepcopy
from functools import partial
from lxml import etree

import config

from pyxsl.parse import get_xsls_in_dir, get_tree, is_xsl_tag


def extend_one_file_templates(file_name, data_dict):
    xsl_data = data_dict.get(file_name, None)

    if xsl_data is None:
        return data_dict

    extended_templates = xsl_data.get('extended_templates', None)
    if extended_templates is not None:
        return data_dict

    templates = xsl_data.get('templates', None)
    xsl_data['extended_templates'] = []
    extended_templates = templates.copy()
    for template in extended_templates:
        template['import_priority'] = 0


    imports = xsl_data.get('imports', None)
    if imports is None:
        return data_dict

    for xsl_import in imports:
        imported_data = extend_one_file_templates(xsl_import, data_dict)




def get_all_file_imports(name, data_dict):
    single_file_data = data_dict.get(name, {})
    keys = single_file_data.get('imports', [])
    return keys + list(chain.from_iterable(get_all_file_imports(import_name, data_dict) for import_name in single_file_data.get('imports', [])))


def get_duplicated_imports(data_dict):
    result = defaultdict(dict)
    for file_name in data_dict:
        temp = defaultdict(int)
        for imported_file in get_all_file_imports(file_name, data_dict):
            temp[imported_file] += 1
            if temp[imported_file] > 4:
                result[file_name][imported_file] = temp[imported_file]
    return result


def analyze_modes_usage(data_dict):
    result = defaultdict(int)

    for file_name in data_dict:
        for mode in  data_dict[file_name]['modes']:
            result[mode]

        for mode in data_dict[file_name]['applied_modes']:
            result[mode] += 1

    result = sorted(result.iteritems(), key=itemgetter(1))
    return result


def fgrep_xhh(words, additional_exclude_dirs=[], start_dir=config.ROOT_XHH_DIR):
    empty = []

    exclude_dirs = ['\.git', '\.idea']
    exclude_dirs.extend(additional_exclude_dirs)

    if not words:
        return empty

    os.chdir(start_dir)

    for word in words:
        try:
            command = ['fgrep', '-R'] + ['--exclude-dir={0}'.format(dir) for dir in exclude_dirs] + [word, '.']
            subprocess.check_output(command)
        except:
            empty.append(word)

    return empty


def get_not_used_xsls(data, index):
    data = deepcopy(data)

    del data[config.ROOT_XSL_DIR + '/hh-precompile.xsl']

    res = [f for f in data if f not in index]
    res = map(lambda path: os.path.relpath(path, config.ROOT_XSL_DIR).split('/', 1)[-1], res)

    return fgrep_xhh(sorted(list(set(res))))


def get_platform(file_name):
    splited = file_name.split(os.path.sep)
    return splited[splited.index('xsl') + 1]

def get_file_ancestors(index, file_name):
    return index.get(file_name, [])

def get_all_file_ancestors(index, file_name):
    imported_by = get_file_ancestors(index, file_name)
    return imported_by + list(chain.from_iterable(imap(partial(get_all_file_ancestors, index), imported_by)))


def search_class_names(start_dir):
    classes = set()
    files = get_xsls_in_dir(start_dir)
    for xsl in files:
        for el in get_tree(xsl).getiterator():
            class_names = el.get('class')
            if class_names is not None:
                classes = classes.union(class_names.split(' '))
            if is_xsl_tag(el, 'attribute') and el.get('name') == 'class':
                class_names = el.text.split(' ')
                classes = classes.union(class_names)
                if el.getchildren():
                    print 'Some dynamic class defenition in {0}:'.format(xsl)
                    print etree.tostring(el, pretty_print=True)

    return classes


def get_endpoint_xsls(data):
    page_files = []
    not_page_files = []

    for xsl_name in data:

        platform, _, path = xsl_name.replace(config.ROOT_XSL_DIR, '').strip('/').partition('/')
        if path.startswith('pages'):
            page_files.append(xsl_name)
        else:
            not_page_files.append(xsl_name)



def search_cross_platform_imports(index, start_dir):
    files = get_xsls_in_dir(start_dir)

    for file_name in files:
        file_platform = get_platform(file_name)

        ancestors = get_file_ancestors(index, file_name)

        cross_platform_ancestors = [
            ancestor for ancestor in ancestors if get_platform(ancestor) != file_platform
        ]

        if cross_platform_ancestors:
            print file_name, cross_platform_ancestors


def analyze_vars_usage(data):
    for file in data.itervalues():
        empty = fgrep_xhh(map(lambda x: '$'+x, file['variables']))
        if empty:
            print empty

def analyze_funcs_usage(data):
    for file in data.itervalues():
        empty = fgrep_xhh(map(lambda x: x+'(', file['functions']))
        if empty:
            print empty

