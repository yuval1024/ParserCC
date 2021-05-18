#!/usr/bin/env python3

import os
import pathlib
import tldextract
import pathlib

PATH_HOMEFOLDER = "/home/user/ubuntu/"

def get_output_folder(suffix_dir):
    '''
    TODO: Fix error with WSL paths!
    '''
    if os.path.isdir(r'C:\\'):
        path_output_folder = r'C:\output\\'
    elif os.path.isdir('/home/ubuntu/'):
        path_output_folder = r'/home/ubuntu/output/'
    elif os.path.isdir('/home/ec2-user/'):
        path_output_folder = r'/home/ubuntu/output/'
    else:
        raise Exception("no output folder found")

    path_output_folder = os.path.join(path_output_folder, suffix_dir)
    pathlib.Path(path_output_folder).mkdir(parents=True, exist_ok=True)
    return path_output_folder

def get_project_root_path():
    current_path = os.path.dirname(os.path.realpath(__file__))
    while current_path is not None and len(current_path) > 0:
        if os.path.isdir(os.path.join(current_path, 'utils')) and os.path.isdir(os.path.join(current_path, 'resources')):
            return current_path

        current_path = str(pathlib.Path(current_path).parent)

    return current_path


def get_fqdn_no_www(url):
    fqdn = tldextract.extract(url).fqdn
    fqdn_no_www = fqdn.replace("www.", "")
    return fqdn_no_www

def get_athena_index_path(cc_id):
    output_folder_athena = get_output_folder("athena_output")

    path_dir_with_files = os.path.join(output_folder_athena, "crawl_ids_v6", cc_id)
    pathlib.Path(path_dir_with_files).mkdir(parents=True, exist_ok=True)

    return path_dir_with_files

