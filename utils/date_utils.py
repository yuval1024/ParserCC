#!/usr/bin/env python3

import time
import datetime
# from timeit import default_timer

from utils.singletonmetaclass import SingletonMetaClass


class DateUtils(metaclass=SingletonMetaClass):
    def __init__(self):
        self.cc_id_to_epoch = {'CC-MAIN-2014-10': 1394928000, 'CC-MAIN-2014-15': 1397952000,
                               'CC-MAIN-2014-23': 1402790400, 'CC-MAIN-2014-35': 1410048000,
                               'CC-MAIN-2014-41': 1413676800, 'CC-MAIN-2014-42': 1414281600,
                               'CC-MAIN-2014-49': 1418515200, 'CC-MAIN-2014-52': 1420329600,
                               'CC-MAIN-2015-06': 1423958400, 'CC-MAIN-2015-11': 1426982400,
                               'CC-MAIN-2015-14': 1428796800, 'CC-MAIN-2015-18': 1431216000,
                               'CC-MAIN-2015-22': 1433635200, 'CC-MAIN-2015-27': 1436659200,
                               'CC-MAIN-2015-32': 1439683200, 'CC-MAIN-2015-35': 1441497600,
                               'CC-MAIN-2015-40': 1444521600, 'CC-MAIN-2015-48': 1449360000,
                               'CC-MAIN-2016-07': 1456012800, 'CC-MAIN-2016-18': 1462665600,
                               'CC-MAIN-2016-22': 1465084800, 'CC-MAIN-2016-26': 1467504000,
                               'CC-MAIN-2016-30': 1469923200, 'CC-MAIN-2016-36': 1473552000,
                               'CC-MAIN-2016-40': 1475971200, 'CC-MAIN-2016-44': 1478390400,
                               'CC-MAIN-2016-50': 1482019200, 'CC-MAIN-2017-04': 1485648000,
                               'CC-MAIN-2017-09': 1488672000, 'CC-MAIN-2017-13': 1491091200,
                               'CC-MAIN-2017-17': 1493510400, 'CC-MAIN-2017-22': 1496534400,
                               'CC-MAIN-2017-26': 1498953600, 'CC-MAIN-2017-30': 1501372800,
                               'CC-MAIN-2017-34': 1503792000, 'CC-MAIN-2017-39': 1506816000,
                               'CC-MAIN-2017-43': 1509235200, 'CC-MAIN-2017-47': 1511654400,
                               'CC-MAIN-2017-51': 1514073600, 'CC-MAIN-2018-05': 1517702400,
                               'CC-MAIN-2018-09': 1520121600, 'CC-MAIN-2018-13': 1522540800,
                               'CC-MAIN-2018-17': 1524960000, 'CC-MAIN-2018-22': 1527984000,
                               'CC-MAIN-2018-26': 1530403200, 'CC-MAIN-2018-30': 1532822400,
                               'CC-MAIN-2018-34': 1535241600, 'CC-MAIN-2018-39': 1538265600,
                               'CC-MAIN-2018-43': 1540684800, 'CC-MAIN-2018-47': 1543104000,
                               'CC-MAIN-2018-51': 1545523200, 'CC-MAIN-2019-04': 1549152000,
                               'CC-MAIN-2019-09': 1552176000, 'CC-MAIN-2019-13': 1554595200,
                               'CC-MAIN-2019-18': 1557619200, 'CC-MAIN-2019-22': 1560038400,
                               'CC-MAIN-2019-26': 1562457600, 'CC-MAIN-2019-30': 1564876800,
                               'CC-MAIN-2019-35': 1567900800, 'CC-MAIN-2019-39': 1570320000,
                               'CC-MAIN-2019-43': 1572739200, 'CC-MAIN-2019-47': 1575158400,
                               'CC-MAIN-2019-51': 1577577600, 'CC-MAIN-2020-05': 1581206400,
                               'CC-MAIN-2020-10': 1584230400, 'CC-MAIN-2020-16': 1587859200,
                               'CC-MAIN-2020-24': 1592697600, 'CC-MAIN-2020-29': 1595721600,
                               'CC-MAIN-2020-34': 1598745600, 'CC-MAIN-2020-40': 1602374400}

    @staticmethod
    def _generate_epoch_for_year_and_weeknum(year, week):
        # see: https://stackoverflow.com/a/38528688, https://stackoverflow.com/q/50356572
        d = datetime.datetime.strptime(f"{year:04d} {week:02d} 0 00:00:00", "%Y %W %w %H:%M:%S")
        epoch = int(time.mktime(d.timetuple()))
        return epoch

    def get_epoch_for_cc_id(self, cc_id):
        try:
            return self.cc_id_to_epoch[cc_id]
        except:
            parts = cc_id.split("-")
            year, week = int(parts[2]), int(parts[3])
            epoch = self._generate_epoch_for_year_and_weeknum(year, week)
            self.cc_id_to_epoch[cc_id] = epoch
            return epoch

