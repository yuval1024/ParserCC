#!/usr/bin/env python3

import os
import pathlib
import threading
import time
import random
import json
import gzip
from multiprocessing import Queue

from utils import helpers, helpers_regex

# import logging
# import logging.handlers

from utils.log_conf import Logger
logger = Logger().logr

random.seed(time.time())

path_data = helpers.get_output_folder("data")
URL_PREFIX = 'http://commoncrawl.s3.amazonaws.com/'


class URLsReaderCC:
    def __init__(self, path_dir_with_files, desc, max_from_domain=0):
        self.lock = threading.Lock()
        self.path_dir_with_files = path_dir_with_files
        self.desc = desc
        self.files_list_all_files = list()
        self.all_processes_files = set()
        self.files_to_process = set()
        self.curr_file_path = None

        self.urls_seens = 0
        self.urls_returned = 0
        self.urls_skipped_same_domain = 0

        # max X urls from domain
        self.domain_to_count = {}
        self.domains_in_dic = list()
        self.MAX_DOMAINS_IN_LIST = 50000
        self.MAX_RESULTS_FROM_DOMAIN = max_from_domain

        self.path_files_dir = os.path.join(path_data, 'urls_mgr_cc', self.desc)
        pathlib.Path(self.path_files_dir).mkdir(parents=True, exist_ok=True)
        self.seen_files_file_path = os.path.join(self.path_files_dir, 'seen_files.txt')
        self.init_urls()

        self.mp_urls_queue = Queue()

        self._open_next_file_gz()

    def init_urls(self):
        for root, dirs, files in os.walk(self.path_dir_with_files):
            for name in files:
                if name.endswith(".gz"):
                    # if self.filename_filter is None or self.filename_filter in name:
                    self.files_list_all_files.append(os.path.join(root, name))

        if os.path.isfile(self.seen_files_file_path):
            with open(self.seen_files_file_path, 'r') as fin:
                for line in fin:
                    self.all_processes_files.add(line.strip())

        self.files_to_process = set(self.files_list_all_files) - self.all_processes_files

        logger.info(f"files_list_all_files len: {len(self.files_list_all_files)}; "
            f"all_processes_files len: {len(self.all_processes_files)}; "
            f"files_to_process len: {len(self.files_to_process)}")

    def get_urls_queue(self) -> Queue:
        return self.mp_urls_queue

    def set_new_file_to_process(self):
        if self.curr_file_path is not None:
            # mark previous file as processed
            self.files_to_process.remove(self.curr_file_path)
            self.all_processes_files.add(self.curr_file_path)
            with open(self.seen_files_file_path, 'a') as fout:
                fout.write(self.curr_file_path + "\n")
                logger.info(f"desc: {self.desc} ; new file retrieved:: all len: {len(self.files_list_all_files)}; "
                    f"processed len: {len(self.all_processes_files)}; "
                    f"to process len: {len(self.files_to_process)}")

        if len(self.files_to_process) == 0:
            self.curr_file_path = None
            return

        current_files = random.sample(self.files_to_process, k=1)     # no replacement
        self.curr_file_path = current_files[0]
        logger.info(f"new file retrieved")

    def _next_file_exists(self):
        return len(self.files_to_process) > 0

    def _open_next_file_gz(self):
        '''
        assume next file exists, e.g. should do pre-check using "_next_file_exists"
        :return:
        '''

        self.set_new_file_to_process()
        if self.curr_file_path is None:
            self.fin = None
            return None

        self.fin = gzip.open(self.curr_file_path, 'rt')

    def _get_next_line(self):
        with self.lock:
            while True:
                if self.fin is None:
                    return None

                try:
                    line = next(self.fin)
                    self.urls_seens += 1
                    return line
                except StopIteration as ex:
                    if self._next_file_exists():
                        self._open_next_file_gz()
                    else:
                        return None

    def is_domain_count_ok(self, dic_to_process):
        if self.MAX_RESULTS_FROM_DOMAIN == 0:   # feature disabled
            return True

        url = dic_to_process['url']
        fqdn_no_www = helpers.get_fqdn_no_www(url)
        if fqdn_no_www in self.domain_to_count.keys():
            self.domain_to_count[fqdn_no_www] += 1
        else:
            self.domain_to_count[fqdn_no_www] = 1
            self.domains_in_dic.append(fqdn_no_www)

        return_val = self.domain_to_count[fqdn_no_www] <= self.MAX_RESULTS_FROM_DOMAIN

        if len(self.domains_in_dic) >= self.MAX_DOMAINS_IN_LIST:
            domain_to_remove = self.domains_in_dic.pop(0)
            try:
                del self.domain_to_count[domain_to_remove]
            except:
                pass

        return return_val

    def get_next_dict(self):
        # with self.lock:
        while True:
            line = self._get_next_line()
            if line is None:
                return None

            j = json.loads(line.strip())
            url = j['url']

            # less than self.MAX_RESULTS_FROM_DOMAIN pages OR get root page
            if not self.is_domain_count_ok(j) and not helpers_regex.is_root_domain_homepage(url):
                self.urls_skipped_same_domain += 1
                continue
            else:
                break

        return j

    def get_next_dict_root_pages(self):
        # with self.lock:
        while True:
            curr_dic = self.get_next_dict()
            if curr_dic is None:
                return None
            url = curr_dic['url']
            if url.endswith('robots.txt'):
                continue
            if "?" in url:
                continue

            if helpers_regex.is_root_domain_url_or_page(url):
                self.urls_returned += 1
                if self.urls_returned % 200_000 == 0 and self.urls_returned > 0:
                    logger.info(f"get_next_dic_root_pages:: returned {self.urls_returned/1000.0}K seen {self.urls_seens/1000.0}K pct: {100.0*self.urls_returned/self.urls_seens:2.2f}%; same domain skip: {self.urls_skipped_same_domain/1000.0}K")
                return curr_dic

    def get_next_dict_root_domains(self):
        '''
        only TLD, e.g.
        www.acme.com
        :return:
        '''
        while True:
            curr_dic = self.get_next_dict()
            if curr_dic is None:
                return None

            url = curr_dic['url']
            if helpers_regex.is_root_domain_homepage(url):
                self.urls_returned += 1
                if self.urls_returned % 200_000 == 0 and self.urls_returned > 0:
                    logger.info(f"get_next_dic_root_domains:: returned {self.urls_returned/1000.0}K seen {self.urls_seens/1000.0}K pct: {100.0*self.urls_returned/self.urls_seens:2.2f}%%")
                return curr_dic


def print_stats():
    # crawl_ids = ['CC-MAIN-2020-40', 'CC-MAIN-2020-34']
    crawl_ids = ['CC-MAIN-2020-40']

    for cc_id in crawl_ids:
        logger.info(f"print_stats querying cc_id: [{cc_id}] v6")
        path_dir_with_files = helpers.get_athena_index_path(cc_id)

        desc = "test_count_records"
        urls_manager_commcr = URLsReaderCC(path_dir_with_files, desc=desc)

        count_pages = 0
        while True:
            z = urls_manager_commcr.get_next_dict_root_pages()
            if z is None:
                break

            count_pages += 1

            if count_pages % 100_000 == 0:
                logger.info(f"count_pages: {count_pages/1e6} 100K")


if __name__ == '__main__':
    pass
    print_stats()
