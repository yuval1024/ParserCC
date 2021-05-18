#!/usr/bin/env python3
import re

re_newlines = re.compile(pattern="\r\n")

def convert_regex_no_capture(regex_str: str):
    # replace all "(" with "(?:" - e.g. to match but not to capture
    assert "(?!" not in regex_str

    str_keeper = "zzzz"
    while str_keeper in regex_str:
        str_keeper = str_keeper + str_keeper

    # if we already have "(?:", replace it with some random string to prevent result like "(?:?:"
    regex_str = regex_str.replace("(?:", str_keeper)
    regex_str = regex_str.replace("(", "(?:")
    regex_str = regex_str.replace(str_keeper, "(?:")

    return regex_str


def remove_version_from_regex(regex_str):
    if r"\;version:" in regex_str:
        regex_str = regex_str[0:regex_str.index(r"\;version:")]

    return regex_str


def get_headers_from_payload(payload_str):
    headers_str = payload_str[0:payload_str.index("\r\n\r\n")]
    headers_strs = re_newlines.sub("\n", headers_str).split("\n")
    headers = {}
    for header_and_key in headers_strs:
        if header_and_key.lower().startswith("http/"):
            continue

        header_name, header_value = header_and_key.split(": ", 1)
        headers[header_name] = header_value

    return headers


def get_payload_from_byes(raw_bytes):
    '''
    Get payload from WARC bytes
    '''
    try:
        payload_str = raw_bytes.decode('utf-8')
    except Exception as ex:  # probably encoding error, try another encoding
        try:
            payload_str = raw_bytes.decode('iso-8859-1')
        except Exception as ex:
            return None

    return payload_str


def is_root_domain_url_or_page(url):
    # e.g.: https://acme.com/blog/

    count_slashes = url.count("/")

    if count_slashes == 2 or count_slashes == 3 or (count_slashes == 4 and url.endswith("/")):
        return True

def is_root_domain_homepage(url):
    # e.g.: https://acme.com/

    count_slashes = url.count("/")

    if count_slashes == 2 or (count_slashes == 3 and url.endswith("/")):
        return True
