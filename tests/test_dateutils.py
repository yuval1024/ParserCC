#!/usr/bin/env python3
import unittest

from utils.date_utils import DateUtils


class TestDateUtils(unittest.TestCase):
    def test_convert_common_crawl_ids_to_dates(self):
        # http://index.commoncrawl.org/
        crawl_ids_all = ['CC-MAIN-2020-40', 'CC-MAIN-2020-34', 'CC-MAIN-2020-29', 'CC-MAIN-2020-24', 'CC-MAIN-2020-16',
                         'CC-MAIN-2020-10', 'CC-MAIN-2020-05', 'CC-MAIN-2019-51', 'CC-MAIN-2019-47', 'CC-MAIN-2019-43',
                         'CC-MAIN-2019-39', 'CC-MAIN-2019-35', 'CC-MAIN-2019-30', 'CC-MAIN-2019-26', 'CC-MAIN-2019-22',
                         'CC-MAIN-2019-18', 'CC-MAIN-2019-13', 'CC-MAIN-2019-09', 'CC-MAIN-2019-04', 'CC-MAIN-2018-51',
                         'CC-MAIN-2018-47', 'CC-MAIN-2018-43', 'CC-MAIN-2018-39', 'CC-MAIN-2018-34', 'CC-MAIN-2018-30',
                         'CC-MAIN-2018-26', 'CC-MAIN-2018-22', 'CC-MAIN-2018-17', 'CC-MAIN-2018-13', 'CC-MAIN-2018-09',
                         'CC-MAIN-2018-05', 'CC-MAIN-2017-51', 'CC-MAIN-2017-47', 'CC-MAIN-2017-43', 'CC-MAIN-2017-39',
                         'CC-MAIN-2017-34', 'CC-MAIN-2017-30', 'CC-MAIN-2017-26', 'CC-MAIN-2017-22', 'CC-MAIN-2017-17',
                         'CC-MAIN-2017-13', 'CC-MAIN-2017-09', 'CC-MAIN-2017-04', 'CC-MAIN-2016-50', 'CC-MAIN-2016-44',
                         'CC-MAIN-2016-40', 'CC-MAIN-2016-36', 'CC-MAIN-2016-30', 'CC-MAIN-2016-26', 'CC-MAIN-2016-22',
                         'CC-MAIN-2016-18', 'CC-MAIN-2016-07', 'CC-MAIN-2015-48', 'CC-MAIN-2015-40', 'CC-MAIN-2015-35',
                         'CC-MAIN-2015-32', 'CC-MAIN-2015-27', 'CC-MAIN-2015-22', 'CC-MAIN-2015-18', 'CC-MAIN-2015-14',
                         'CC-MAIN-2015-11', 'CC-MAIN-2015-06', 'CC-MAIN-2014-52', 'CC-MAIN-2014-49', 'CC-MAIN-2014-42',
                         'CC-MAIN-2014-41', 'CC-MAIN-2014-35', 'CC-MAIN-2014-23', 'CC-MAIN-2014-15', 'CC-MAIN-2014-10',
                         'CC-MAIN-2013-48', 'CC-MAIN-2013-20']
        s = ""
        for year in range(2014, 2020 + 1):
            for week in range(1, 55):
                try:
                    cc_id = f"CC-MAIN-{year:04d}-{week:02d}"
                    if cc_id not in crawl_ids_all:
                        continue

                    epoch = DateUtils._generate_epoch_for_year_and_weeknum(year, week)
                    s += f"'{cc_id}': {epoch},"
                except Exception as ex:
                    print(f"error with year {year} week {week}; no such week?!")
                    raise ex

        s = s.strip(",")
        s = "self.cc_id_to_epoch = {" + s + "}"
        print(s)


if __name__ == '__main__':
    unittest.main()
