#!/usr/bin/env python3

import pathlib
import string
import time
import random
from urllib.parse import urlparse
import traceback

import boto3
from boto3.session import Session
import pyathena

from utils.sentry_wrapper import SentryInit
SentryInit().init_with_env()


from utils import helpers

from utils.log_conf import Logger
logger = Logger().logr

random.seed(time.time())


path_data = helpers.get_output_folder("cc_index_data")
URL_PREFIX = 'http://commoncrawl.s3.amazonaws.com/'

class CommonCrawlIndexQuery():
    def __init__(self, database, output_format='JSON'):
        pass
        self.cursor = pyathena.connect().cursor()
        self.database = database
        self.output_format = output_format

    def create_query_homepages_and_level1(self, crawl_id):
        '''
        Get URLs of homepages and up to 1 level, e.g.
        www.domain/
        www.domain/about-us/
        www.domain/about-us.html
        www.domain/about-us.php

        :param crawl_id: CommonCrawl index
        :return:
        '''
        query_template = """
SELECT cc.url,
       cc.warc_filename,
       cc.warc_record_offset,
       cc.warc_record_length,
       cc.crawl
FROM "ccindex"."ccindex" AS cc
WHERE cc.crawl = '~~CRAWL_ID~~'
  AND cc.subset = 'warc'
  AND cc.url_query is null
  AND (
    -- create_query_by_crawl_id_v6
    -- fix, v6: including pages in form acme.com/some-page/, which were absent before 
    -- before:  '^/[^/+]/?$'
    -- after:  '^/[^/]+/?$'
    (length(cc.url_path)=0 OR cc.url_path='/' OR regexp_like(cc.url_path, '^/[^/]+/?$') OR regexp_like(cc.url_path, '^/[^/+]$'))
  OR
    -- create_query_by_crawl_id
    (regexp_like(cc.url_path, '^/?(?:index\.(?:html?|php))?$')
    AND cc.url_query is NULL
    AND (length(cc.url_host_name) = length(cc.url_host_registered_domain)
       AND (substr(cc.url, 1, 8) = 'https://')
       OR (length(cc.url_host_name) = (length(cc.url_host_registered_domain)+4)
       AND substr(cc.url_host_name, 1, 4) = 'www.'))
    )
  )
  """.strip()

        query = query_template.replace("~~CRAWL_ID~~", crawl_id)
        return query

    def _temp_table_name(self, name_length=10, name_prefix="sandbox.temp_"):
        """Generate a random string of fixed length """
        return self.database + "." + "sandboxtemp_" + "".join(random.choices(string.ascii_lowercase, k=name_length))

    def do_main_from_crawl_ids(self):
        crawl_ids = ['CC-MAIN-2020-45', 'CC-MAIN-2020-50', 'CC-MAIN-2021-04']

        for crawl_id in crawl_ids:
            logger.info(f"crawl_id: [{crawl_id}]")

            query = self.create_query_homepages_and_level1(crawl_id)
            path_dir_with_files = helpers.get_athena_index_path(crawl_id)

            table_name = "query_indexes__%s__%d" % (crawl_id, int(time.time()))
            table_name = table_name.replace("-", "_")
            self.download_table(path_dir_with_files, query, table_name=table_name, format=self.output_format)
            logger.info(f"downloading to path_dir_with_files [{path_dir_with_files}]")

    def download_table(self, path_outfolder, query, table_name, format="JSON"):
        """Use PyAthena cursor to download query to path_outfolder in format

        Note that all columns in query must be named for this to work
        Multiple files may be created in path_outfolder.
        """

        try:
            self._create_table_as(self.cursor, table_name, query, format)
            s3_locations = self.table_file_location(self.cursor, table_name)
            self._download_s3(s3_locations, path_outfolder)
        except Exception as ex:
            bt = traceback.format_exc()
            logger.error(f"bt: __%s__" % (str(bt)))

        finally:
            pass

        logger.info("finished downloading table")

    def _create_table_as(self, cursor, table, query, format='AVRO'):
        cursor.execute(f"CREATE TABLE {table} WITH (format = '{format}') as {query}")

    def table_file_location(self, cursor, table):
        cursor.execute(f'SELECT DISTINCT "$path" FROM {table}')
        return [row[0] for row in cursor.fetchall()]

    def _get_bucket_key(self, s3_path):
        """Returns bucket name, key from s3_path of form s3://bucket/key"""
        url = urlparse(s3_path)
        if url.scheme != 's3':
            raise ValueError(f'Unexpected scheme {url.scheme} in {s3_path}; expected s3')
        return url.netloc, url.path.lstrip('/')

    def _download_s3(self, s3_paths, outpath):
        outpath = pathlib.Path(outpath)
        outpath.mkdir(parents=True, exist_ok=True)
        client = Session().client('s3')
        for s3_path in s3_paths:
            bucket_name, bucket_key = self._get_bucket_key(s3_path)
            filename = bucket_key.split('/')[-1]
            client.download_file(bucket_name, bucket_key, str(outpath / filename))

    def _drop_table(self, cursor, table):
        # Optionally remove underlying S3 files here
        cursor.execute(f'DROP TABLE {table} IF EXISTS')

if __name__ == '__main__':
    cc_index_query = CommonCrawlIndexQuery(database='db_cc', output_format='JSON')
    cc_index_query.do_main_from_crawl_ids()
