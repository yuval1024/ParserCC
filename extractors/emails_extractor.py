#!/usr/bin/env python3

try:
    import re2 as re
    re.match("a", "abcd")
except:
    print("re2 not installed / runtime exceptions")
    import re

class EmailsExtractor():
    stopwords = [".jpg", ".jpeg", ".gif", ".png"]

    def __init__(self):
        pass
        # https://stackoverflow.com/a/17681902
        self.regex = r'[\w\.-]+@[\w\.-]+\.\w+'
        # self.regex_v2 = r'[\w\.-]{1,30}@[\w\.-]{1,30}\.\w{1,10}'  # much slower so don't use for now

        self.re_email = re.compile(self.regex, re.MULTILINE | re.IGNORECASE)

    def return_matching_emails(self, html_body: str):
        emails = []
        matches = self.re_email.finditer(html_body)
        for m in matches:
            email_addr = m.group(0)

            if EmailsExtractor.filter_email_initial(email_addr):
                emails.append(email_addr)

        return emails

    @staticmethod
    def filter_email_initial(email_addr):
        # initial filtering; more filtering in later steps
        if any(word in email_addr.lower() for word in EmailsExtractor.stopwords):
            return False

        return True
