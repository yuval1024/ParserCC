#!/usr/bin/env python3

import os
import re
import json

from typing import List, Dict, Optional, Any

import re as re_orig
import hyperscan

from extractors.appname_xlator import AppnameXlator
from utils import helpers
from utils import helpers_regex

project_root_folder = helpers.get_project_root_path()

class WebsiteChecker():
    def __init__(self):
        self.file_path_apps_json = os.path.join(project_root_folder, "resources", "apps.json")
        self.appname_xlator = AppnameXlator()

        self.headers_list = {}

        # hyperscan
        self.db_block_html = None  # type:Optional[hyperscan.Database]
        self.html_ids = list()
        self.html_expressions = list()  # type:List[bytes]
        self.html_flags = list()

        self.db_block_scripts = None  # type:Optional[hyperscan.Database]
        self.script_ids = list()
        self.script_expressions = list()  # type:List[bytes]
        self.script_flags = list()

        self.load_apps_file()

    def load_apps_file(self):
        file_body = open(self.file_path_apps_json, encoding='utf8').read()
        j = json.loads(file_body)
        apps = j['apps']
        for appname, values in apps.items():
            try:
                if "headers" in values.keys():
                    headers = values["headers"]
                    for header_name, header_regex in headers.items():
                        self._add_header_regex(appname=appname, header_name=header_name, header_regex=header_regex)
            except Exception as ex:
                print(f"unable to add headers for appname: {appname}: %s" % (str(ex)))

            try:
                if "html" in values.keys():
                    if type(values["html"]) == str:
                        htmls = [values["html"]]    # should be a list
                    else:
                        htmls = values["html"]
                    for html_regex_str in htmls:
                        html_regex_str = helpers_regex.remove_version_from_regex(html_regex_str)
                        html_regex_str = helpers_regex.convert_regex_no_capture(html_regex_str)
                        html_regex_str = "(" + html_regex_str + ")"

                        self._add_html_regex(appname=appname, html_regex_str=html_regex_str)
            except Exception as ex:
                print(f"unable to add html for appname: {appname}: %s" % (str(ex)))

            try:
                if "script" in values.keys():
                    if type(values["script"]) == str:
                        scripts = [values["script"]]    # should be a list
                    else:
                        scripts = values["script"]
                    for script_regex_str in scripts:
                        script_regex_str = helpers_regex.remove_version_from_regex(script_regex_str)
                        script_regex_str = helpers_regex.convert_regex_no_capture(script_regex_str)
                        script_regex_str_no_wrap = "(" + script_regex_str + ")"

                        self._add_script_regex(appname=appname, script_regex_str_no_wrap=script_regex_str_no_wrap)
            except Exception as ex:
                print(f"unable to add script_regex_str for appname: {appname}: %s" % (str(ex)))

        self._compile_hs()

    def _add_header_regex(self, appname, header_name, header_regex):
        header_regex = helpers_regex.remove_version_from_regex(header_regex)

        if header_name not in self.headers_list.keys():
            self.headers_list[header_name] = list()

        compiled_regex = re_orig.compile(header_regex, re.DOTALL | re.IGNORECASE)
        self.headers_list[header_name].append((compiled_regex, appname))

    def _add_script_regex(self, appname: str, script_regex_str_no_wrap: str):
        app_id = self.appname_xlator.get_appname_id(appname)
        self.html_ids.append(app_id)
        self.html_expressions.append(script_regex_str_no_wrap.encode('utf8'))
        self.html_flags.append(hyperscan.HS_FLAG_DOTALL | hyperscan.HS_FLAG_MULTILINE)

    def _add_html_regex(self, appname: str, html_regex_str: str):
        app_id = self.appname_xlator.get_appname_id(appname)
        self.script_ids.append(app_id)
        self.script_expressions.append(html_regex_str.encode('utf8'))
        self.script_flags.append(hyperscan.HS_FLAG_DOTALL | hyperscan.HS_FLAG_MULTILINE)

    def _compile_hs(self):
        mode_block = hyperscan.HS_MODE_BLOCK
        self.db_block_html = hyperscan.Database(mode=mode_block)
        self.db_block_html.compile(expressions=self.html_expressions, ids=self.html_ids, flags=self.html_flags)

        self.db_block_scripts = hyperscan.Database(mode=mode_block)
        self.db_block_scripts.compile(expressions=self.script_expressions, ids=self.script_ids, flags=self.script_flags)

    def return_matching_apps_headers(self, headers: dict):
        apps = []

        for header_key, header_value in headers.items():
            if header_key in self.headers_list.keys():
                list_tuples = self.headers_list[header_key]
                for header_regex, appname in list_tuples:
                    if header_regex.match(header_value):
                        apps.append(appname)

        return apps

    @staticmethod
    def on_match_hs(id_: int, from_pos: int, to_pos: int, flags: int, context: Optional[Any] = None) -> Optional[bool]:
        context['ids'].add(id_)
        return None  # don't halt scan

    def return_matching_apps_scripts(self, html_body: str):
        ctx = {'ids': set()}
        self.db_block_scripts.scan(html_body, match_event_handler=WebsiteChecker.on_match_hs, context=ctx)

        app_names = [self.appname_xlator.get_appname_id(appname, add_app=False) for appname in ctx['ids']]
        return app_names

    def return_matching_apps_html(self, html_body: str):
        ctx = {'ids': set()}
        self.db_block_html.scan(html_body, match_event_handler=WebsiteChecker.on_match_hs, context=ctx)

        app_names = [self.appname_xlator.get_appname_id(appname, add_app=False) for appname in ctx['ids']]
        return app_names

