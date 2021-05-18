#!/usr/bin/env python3
import unittest

from extractors.tech_extractor import WebsiteChecker


class TestTech(unittest.TestCase):
    def setUp(self):
        self.websites_checker = WebsiteChecker()

    def test_headers(self):
        headers = {"Set-Cookie": "BITRIX_"}
        apps = self.websites_checker.return_matching_apps_headers(headers)
        assert "1C-Bitrix" in apps
        assert len(apps) == 1

        headers = {"X-Powered-CMS": "Bitrix Site Manager"}
        apps = self.websites_checker.return_matching_apps_headers(headers)
        assert "1C-Bitrix" in apps
        assert len(apps) == 1


if __name__ == '__main__':
    unittest.main()
