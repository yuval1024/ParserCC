#!/usr/bin/env python3

import os
from collections import defaultdict

import traceback
import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from utils.log_conf import Logger
logger = Logger().logr

from utils.singletonmetaclass import SingletonMetaClass


class SentryInit(metaclass=SingletonMetaClass):
    def __init__(self, log_level=logging.INFO, max_events_of_type=100):
        pass
        self.max_events_of_type = max_events_of_type
        self.error_to_count = defaultdict(int)

        self.env = os.environ
        self.mode_flask = False
        self.mode_django = False
        self.mode_celery = False
        self.mode_sqlalchemy = False
        self.mode_redis = False

        self.log_level = log_level
        self.sentry_debug = False

    def set_env(self, env):
        self.env = env
        return self

    def set_mode_flask(self):
        self.mode_flask = True
        return self

    def set_mode_django(self):
        self.mode_django = True
        return self

    def set_mode_celery(self):
        self.mode_celery = True
        return self

    def set_mode_sqlalchemy(self):
        self.mode_sqlalchemy = True
        return self

    def set_mode_redis(self):
        self.mode_redis = True
        return self

    def init_with_env(self):
        sentry_debug = self.env.get("SENTRY_DEBUG", None)
        if sentry_debug is not None and (sentry_debug==True or sentry_debug.lower()=="true" or sentry_debug==1):
            sentry_debug = True
        else:
            sentry_debug = False

        sentry_dsn = self.env.get("SENTRY_DSN", None)
        if sentry_dsn is None:
            print("Warning: SentryInit:: SENTRY_DSN is None")
            return False
        else:
            self.init_with_dsn(sentry_dsn, sentry_debug)

    def init_with_dsn(self, sentry_dsn, sentry_debug=False):
        try:
            # https://flask.palletsprojects.com/en/1.1.x/errorhandling/
            list_integrations = []

            try:
                if self.mode_flask:
                    from sentry_sdk.integrations.flask import FlaskIntegration
                    list_integrations += [FlaskIntegration()]
                if self.mode_django:
                    from sentry_sdk.integrations.django import DjangoIntegration
                    list_integrations += [DjangoIntegration()]
                if self.mode_celery:
                    from sentry_sdk.integrations.celery import CeleryIntegration
                    list_integrations += [CeleryIntegration()]
                if self.mode_sqlalchemy:
                    # https://docs.sentry.io/platforms/python/integrations/sqlalchemy/
                    from sentry_sdk.integrations.celery import SqlalchemyIntegration
                    list_integrations += [SqlalchemyIntegration()]
                if self.mode_redis:
                    # https://docs.sentry.io/platforms/python/integrations/redis/
                    from sentry_sdk.integrations.celery import RedisIntegration
                    list_integrations += [RedisIntegration()]
            except Exception as ex:
                logging.error("error initializing sentry modules: %s" % (str(ex)))

            if self.log_level is not None:
                # SENTRY_LOG_LEVEL = env.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)
                sentry_logging = LoggingIntegration(
                    level=self.log_level,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors as events
                )
                list_integrations += [sentry_logging]

            sentry_sdk.init(sentry_dsn,
                            with_locals=True,
                            integrations=list_integrations,
                            send_default_pii=False,
                            debug=sentry_debug)
            return True
        except Exception as ex:
            print("SentryInit:: error main: %s" % (ex))

        return False

    def increase_and_should_report(self, ex):
        bt = traceback.format_exc()
        self.error_to_count[bt] += 1
        if self.error_to_count[bt] < self.max_events_of_type:
            return True

        print("not exporting ERROR with stack: __%s__" % (bt))
        return False

    def capture_exception(self, ex):
        if self.increase_and_should_report(ex):
            sentry_sdk.capture_exception(ex)

