#!/usr/bin/env python3

import logging
import logging.handlers
import logging.config

from utils.singletonmetaclass import SingletonMetaClass


class Logger(metaclass=SingletonMetaClass):
    def __init__(self):
        # logging.config.fileConfig('logging.conf')
        logr = logging.getLogger('root')
        handler = logging.handlers.RotatingFileHandler('%s.log' % (__name__), maxBytes=1000000, backupCount=5)
        formatter = logging.Formatter("%(created)f %(asctime)s %(funcName)15s():%(lineno)d %(levelname)s:: %(message)s",
                                      datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        logr.addHandler(handler)
        logr.setLevel(logging.INFO)

        self.logr = logr

