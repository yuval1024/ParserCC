#!/usr/bin/env python3

import os
import pathlib
import time
import random
import requests
import json
import gzip
from multiprocessing import Process, Queue
import io
from warc import WARCReader
import re

import boto3
from botocore.handlers import disable_signing

from utils import helpers
from utils.lru_cache import LruCache
from utils.sentry_wrapper import SentryInit
SentryInit().init_with_env()

from utils.log_conf import Logger
logger = Logger().logr

random.seed(time.time())

URL_PREFIX = 'http://commoncrawl.s3.amazonaws.com/'

class TechResultsOutputFile():
    def __init__(self):
        self.queue_technologies_out = Queue()

        self.technologies_results_filename = None
        self.technologies_results_fout = None
        self.store_name_results_curr_file_count = 0
        self.technologies_results_total_count = 0

        self.LIMIT_PER_FILE = 1_500_000  # around 300 MB
        self._new_files_if_needed()

        self.results_lru_cache = LruCache(50000)

        self.count_download_errors = 0
        self.count_encoding_errors = 0
        # self.count_items = 0
        self.count_urls = 0
        self.count_technologies = 0
        self.lru_hit = 0
        self.lru_miss = 0
        self.counter_a_added = 0
        self.counter_b_added = 0

        self.last_stat_epoch = time.time()

        self.fqdn_to_techs = {}
        self.fqdn_and_time_added = []
        self.max_time_to_keep = 60  # seconds
        self.max_records_to_keep = 50000

    def get_queue_out(self):
        return self.queue_technologies_out

    def _new_files_if_needed(self):
        if self.store_name_results_curr_file_count >= self.LIMIT_PER_FILE or self.technologies_results_filename is None:
            self._new_technologies_file()

    def _new_technologies_file(self):
        if self.technologies_results_fout is not None:
            self.technologies_results_fout.close()
            self.technologies_results_filename = None
            self.technologies_results_fout = None

        self.technologies_results_filename = os.path.join(helpers.get_output_folder("technologies"), f"technologies_list__epoch_%s__rnd_%d__.jl" % (str(time.time()), random.randint(1,999999)))
        self.technologies_results_fout = open(self.technologies_results_filename, 'a')
        self.store_name_results_curr_file_count = 0

    def read_from_queues_main(self):
        # read maximum if len(queue) in order to prevent starvation

        queue_technologies_len = self.queue_technologies_out.qsize()
        for _ in range(queue_technologies_len):
            technologies_list = self.queue_technologies_out.get()

            for tech_name_item in technologies_list:
                fqdn_no_www = tech_name_item['fqdn_no_www']
                if fqdn_no_www not in self.fqdn_to_techs.keys():
                    self.fqdn_to_techs[fqdn_no_www] = tech_name_item
                    self.fqdn_to_techs[fqdn_no_www]['name_type_list'] = []
                    self.fqdn_and_time_added.append((fqdn_no_www, time.time()))
                    self.counter_a_added += 1

                tech_name_sig = "%s__%s__%s" % (tech_name_item['fqdn_no_www'], tech_name_item['app_name'], tech_name_item['app_type'])
                if not self.results_lru_cache.add_and_check_exist(tech_name_sig):
                    self.lru_miss += 1
                    self.fqdn_to_techs[fqdn_no_www]['name_type_list'].append((tech_name_item['app_name'], tech_name_item['app_type']))
                else:
                    self.lru_hit += 1

                self.count_technologies += 1

        while True:
            if len(self.fqdn_and_time_added) == 0:
                break

            fqdn_no_www, time_added = self.fqdn_and_time_added[0]
            if (time.time() - time_added < self.max_time_to_keep) and (len(self.fqdn_and_time_added) < self.max_records_to_keep):
                break

            fqdn_no_www, time_added = self.fqdn_and_time_added.pop(0)
            tech_name_item = self.fqdn_to_techs[fqdn_no_www]
            del self.fqdn_to_techs[fqdn_no_www]

            del tech_name_item["app_type"]
            del tech_name_item["app_name"]
            self.technologies_results_fout.write("%s\n" % json.dumps(tech_name_item))
            self.store_name_results_curr_file_count += 1
            self.technologies_results_total_count += 1
            self._new_files_if_needed()

    @staticmethod
    def get_resource(url_to_download_http, curr_dict, session):
        try:
            r = session.get(url_to_download_http, headers={
                'Range': 'bytes=%d-%d' % (
                    curr_dict['warc_record_offset'], curr_dict['warc_record_offset'] + curr_dict['warc_record_length'])})
            warc_content_bytes = r.content

            # self.count_urls += 1
        except requests.exceptions.ConnectionError as ex:
            return None

        try:
            f = gzip.open(io.BytesIO(warc_content_bytes), 'rb')
            first_record = WARCReader(f).read_record()
            first_record.payload.seek(0)
            raw_bytes = first_record.payload.read()
            return raw_bytes
        except Exception as ex:  # probably encoding error
            return None

