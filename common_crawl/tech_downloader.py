#!/usr/bin/env python3

import os
import time
import random
from multiprocessing import Process, Queue

# libs
from warc import WARCReader
import boto3
from botocore.handlers import disable_signing


from common_crawl.tech_queue_in import TechResultsOutputFile
from common_crawl.tech_worker import WorkerTechnologies
from common_crawl.urls_reader import URLsReaderCC
from extractors.tech_extractor import WebsiteChecker
from utils import helpers, helpers_regex
from utils.date_utils import DateUtils


from utils.sentry_wrapper import SentryInit
SentryInit().init_with_env()

from utils.log_conf import Logger
logger = Logger().logr


random.seed(time.time())

path_output = helpers.get_output_folder("athena_test")
URL_PREFIX = 'http://commoncrawl.s3.amazonaws.com/'


class CommonCrawlDownloaderSearcher():
    def __init__(self, max_threads, stop_after, urls_manager, desc, cc_id):
        self.MAX_THREADS = max_threads
        self.STOP_AFTER = stop_after
        self.urls_manager = urls_manager
        self.desc = desc
        self.cc_id = cc_id
        self.cc_id_epoch = DateUtils().get_epoch_for_cc_id(self.cc_id)

        self.tech_results_output = TechResultsOutputFile()

        self.technologies_results_filename = None
        self.technologies_results_fout = None
        self.store_name_results_curr_file_count = 0
        self.technologies_results_total_count = 0

        # TODO: create a Counter class
        self.count_download_errors = 0
        self.count_encoding_errors = 0
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

    def ingest_more_urls_main(self):
        count_added = 0
        curr_list = []

        queue = self.urls_manager.get_urls_queue()
        if queue.qsize() < (self.MAX_THREADS * 1):  # e.g. 1000
            to_add = (self.MAX_THREADS * 2) - queue.qsize()  # 2000
            while True:
                dic_to_process = self._get_next_dic_single()
                if dic_to_process is None:
                    for _ in range(self.MAX_THREADS * 2):
                        queue.put(None)  # this will cause thread getting None to quit
                    logger.info(f"no more URLs; break")
                    return False

                curr_list.append(dic_to_process)
                self.count_urls += 1

                if len(curr_list) >= 100:
                    queue.put(curr_list)
                    curr_list = []
                    count_added += 1

                if count_added >= to_add:
                    if len(curr_list) > 0:
                        queue.put(curr_list)

                    break

        return True

    def mainloop_main(self):
        threads = []

        websites_checker = WebsiteChecker()

        add_more_urls = self.ingest_more_urls_main()

        for t_index in range(self.MAX_THREADS):
            logger.info(f"starting t_index [{t_index}]")
            worker_ref = WorkerTechnologies(websites_checker, self.tech_results_output.get_queue_out(), t_index=t_index, cc_downloader_ref=self)
            t1 = Process(target=WorkerTechnologies.download_function_wrapper, args=(worker_ref,))
            t1.start()
            threads.append(t1)

        while add_more_urls:
            add_more_urls = self.ingest_more_urls_main()

            self.tech_results_output.read_from_queues_main()

            if time.time() - self.last_stat_epoch > 60:
                self.last_stat_epoch = time.time()

                logger.info(f"{self.desc} technologies: {self.count_technologies / 1000.0:2.3f} K; "
                            f"urls {self.count_urls / 1000.0:2.3f} K; "
                            f"lru hit {self.lru_hit / 1000.0:2.3f} K; miss {self.lru_miss / 1000.0:2.3f} K; "
                            f"counter_a_added {self.counter_a_added / 1000.0:2.3f} K; "
                            # f"encoding problems {self.count_encoding_errors}"
                            )

            time.sleep(0.2)

        # 2 minutes grace, then terminate
        logger.info(f"exit while add_more_urls")
        epoch_stop = time.time() + 120
        while time.time() < epoch_stop:
            alive_count = 0
            for t in threads:
                if t.is_alive():
                    alive_count += 1
                else:
                    t.join()

            if alive_count == 0:
                break

            logger.warning(f"alive {alive_count}; sleep()-ing 1 second")
            time.sleep(1)

        for t in threads:
            if t.is_alive():
                t.terminate()
                t.join()

        logger.info("cleaning queue")  # otherwise \"broken pipe\" error (if there are items in queue")
        while not self.urls_manager.get_urls_queue().empty():
            self.urls_manager.get_urls_queue().get()

        logger.info(f"exiting mainloop_main for desc [{self.desc}], cc_id [{self.cc_id}]")

    def _get_next_dic_single(self):
        # dic = self.urls_manager.get_next_dic_root_domains()
        dic = self.urls_manager.get_next_dict_root_pages()
        return dic



def download_urls_main_query_main_pages():
    crawl_id = os.environ.get('CRAWL_ID', "CC-MAIN-2020-50")

    try:
        CC_PROCS_COUNT = int(os.environ.get('CC_PROCS_COUNT', None))
    except:
        CC_PROCS_COUNT = 500

    try:
        MAX_FROM_DOMAIN = int(os.environ.get('MAX_FROM_DOMAIN', None))
    except:
        MAX_FROM_DOMAIN = 3

    logger.info(f"querying crawl_id: [{crawl_id}], CC_PROCS_COUNT {CC_PROCS_COUNT} MAX_FROM_DOMAIN {MAX_FROM_DOMAIN}")

    path_dir_with_files = helpers.get_athena_index_path(crawl_id)

    urls_manager_commcr = URLsReaderCC(path_dir_with_files, desc="test_%d_ppmax_%s" % (MAX_FROM_DOMAIN, crawl_id), max_from_domain=MAX_FROM_DOMAIN)

    common_crawl_downloader = CommonCrawlDownloaderSearcher(CC_PROCS_COUNT, 0, urls_manager_commcr, desc=crawl_id, cc_id=crawl_id)

    common_crawl_downloader.mainloop_main()


def do_main():
    download_urls_main_query_main_pages()


if __name__ == '__main__':
    do_main()
