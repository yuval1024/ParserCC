#!/usr/bin/env python3

from utils.singletonmetaclass import SingletonMetaClass


class WarningBreak(metaclass=SingletonMetaClass):
    def __init__(self):
        self.seen_warnings_strs = set()

    def warning_break(self, warning_desc, one_time=False):
        if one_time and warning_desc in self.seen_warnings_strs:
            return

        self.seen_warnings_strs.add(warning_desc)
        warning_line = "Warning:\n**********************************\n%s\nPress any key to continue" % (warning_desc)
        input(warning_line)
        print("Thanks for the cooperation!")

