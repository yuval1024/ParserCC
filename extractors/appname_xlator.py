#!/usr/bin/env python3

class AppnameXlator():
    def __init__(self, file_path_apps_json=None):
        self.appname_to_id = {}
        self.id_to_appname = {}

    def get_appname_id(self, appname, add_app=True):
        try:
            return self.appname_to_id[appname]
        except KeyError:
            app_id = len(self.appname_to_id) + 1
            self.appname_to_id[appname] = app_id
            self.id_to_appname[app_id] = appname
            return app_id
