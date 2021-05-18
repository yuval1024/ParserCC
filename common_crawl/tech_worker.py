#!/usr/bin/env python3

import time
import random
import traceback
import requests
import gzip
import io

from extractors.tech_extractor import WebsiteChecker
from utils import helpers, helpers_regex

import boto3
from botocore.handlers import disable_signing

from utils.sentry_wrapper import SentryInit
SentryInit().init_with_env()

from utils.log_conf import Logger
logger = Logger().logr

from warc import WARCReader

random.seed(time.time())

URL_PREFIX = 'http://commoncrawl.s3.amazonaws.com/'

class WorkerTechnologies():
    def __init__(self, websites_checker: WebsiteChecker, queue_technologies_out, t_index, cc_downloader_ref):
        pass
        self.t_index = t_index
        self.count_encoding_errors = 0

        self.websites_checker = websites_checker

        # read only!! different thread / process (process)
        self.cc_downloader_ref = cc_downloader_ref

        # self.urls_queue = self.cc_downloader_ref.urls_manager.get_urls_queue().get()
        self.urls_queue = self.cc_downloader_ref.urls_manager.get_urls_queue()

        self.count_download_errors = 0
        self.queue_technologies_out = queue_technologies_out

        self.tls_curr_technologies_list = list()

    def is_greenlight_to_run(self):
        return True

    @staticmethod
    # def download_function_wrapper(self_ref, queue_technologies, t_index):
    def download_function_wrapper(worker_ref):
        logger.info("entered")
        assert isinstance(worker_ref, WorkerTechnologies)

        try:
            worker_ref.download_function()
        except Exception as ex:
            bt = traceback.format_exc()
            logger.error(f"Error: {str(ex)}; bt: {bt}")
            SentryInit().capture_exception(ex)

        logger.info("quit")

    def download_function(self):
        session = requests.Session()

        curr_dics_list = []
        while True:
            while not self.is_greenlight_to_run():
                logger.warning("no greenlight; sleep()-ing 1 second")
                time.sleep(0.5)

            if len(curr_dics_list) == 0:
                # get new list of 100 URLs
                # logger.info(f"t_index {t_index}; before get_urls_queue().get()")
                curr_dics_list = self.urls_queue.get()
                if curr_dics_list is None:
                    logger.info(f"curr_dics_list is None; break-ing")
                    break

            if len(curr_dics_list) == 0:
                logger.error(f"curr_dics_list len is still 0; break-ing")
                break

            curr_dic = curr_dics_list.pop()
            url_to_download_http = URL_PREFIX + curr_dic['warc_filename']

            raw_bytes = WorkerTechnologies.get_resource(url_to_download_http, curr_dic, session)
            if raw_bytes is None:
                logger.warning(f"error with t_index: {self.t_index}; sleep()-ing 5 seconds")
                self.count_download_errors += 1
                time.sleep(5)
                continue

            # process context
            self.parse_callback_technologies(raw_bytes, curr_dic)

        self.parse_callback_technologies_post_download()
        logger.info(f"t_index {self.t_index}; last line")

    @staticmethod
    def get_resource(url_to_download_http, curr_dic, session):
        try:
            r = session.get(url_to_download_http, headers={
                'Range': 'bytes=%d-%d' % (
                curr_dic['warc_record_offset'], curr_dic['warc_record_offset'] + curr_dic['warc_record_length'])})
            warc_content_bytes = r.content

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

    def parse_callback_technologies(self, raw_bytes, curr_dic):
        page_url = curr_dic['url']
        fqdn_no_www = helpers.get_fqdn_no_www(curr_dic['url'])

        payload_str = helpers_regex.get_payload_from_byes(raw_bytes)
        if payload_str is None:
            self.count_encoding_errors += 1
            return

        apps_headers = []
        apps_html = self.websites_checker.return_matching_apps_html(payload_str)
        apps_scripts = self.websites_checker.return_matching_apps_scripts(payload_str)

        apps_with_type = {"html": apps_html, "headers": apps_headers, "scripts": apps_scripts}
        for apps_type, apps_list in apps_with_type.items():
            for app_name in apps_list:
                # override seen_time_epoch from before
                tech_name_item = {}
                tech_name_item['seen_time_epoch'] = self.cc_downloader_ref.cc_id_epoch
                tech_name_item['process_time_epoch'] = int(time.time())
                tech_name_item['source'] = f'cc:{self.cc_downloader_ref.cc_id}'

                tech_name_item['fqdn_no_www'] = fqdn_no_www
                tech_name_item['page_url'] = page_url

                tech_name_item['app_type'] = apps_type
                tech_name_item['app_name'] = app_name

                self.tls_curr_technologies_list.append(tech_name_item)

        if len(self.tls_curr_technologies_list) > 10:
            self.queue_technologies_out.put(self.tls_curr_technologies_list)
            self.tls_curr_technologies_list = list()

    def parse_callback_technologies_post_download(self):
        if len(self.tls_curr_technologies_list) > 0:
            self.queue_technologies_out.put(self.tls_curr_technologies_list)
            self.tls_curr_technologies_list = list()

