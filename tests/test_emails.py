#!/usr/bin/env python3

import unittest

from extractors.emails_extractor import EmailsExtractor

class TestEmails(unittest.TestCase):
    def setUp(self):
        self.emails_checker = EmailsExtractor()

    def test_simple_email(self):
        html_body = r"""test@gmail.com"""
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 1)
        self.assertIn("test@gmail.com", emails)

    def test_multiple_emails(self):
        html_body = r"""test@gmail.com test2@yahoo.com"""
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 2)
        self.assertIn("test@gmail.com", emails)
        self.assertIn("test2@yahoo.com", emails)

    def test_email_inside_tag(self):
        html_body = r"""<test_gt_lt@gmail.com>""" # test2@yahoo.com"""
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 1)
        self.assertIn("test_gt_lt@gmail.com", emails)

    def test_email_with_dot(self):
        html_body = r"""test.dot.after@gmail.com. test2@yahoo.com;""" # """
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 2)
        self.assertIn("test.dot.after@gmail.com", emails)
        self.assertIn("test2@yahoo.com", emails)

    def test_hyphen_in_domain(self):
        html_body = r"""test@gmail-hyphen-in-domain.com""" # """
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 1)
        self.assertIn("test@gmail-hyphen-in-domain.com", emails)

    def test_empty_string(self):
        html_body = ""
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 0)

    def test_inside_span(self):
        html_body = r'<span class="elementor-icon-list-text">ventas@example.com</span>'
        emails = self.emails_checker.return_matching_emails(html_body)
        self.assertIsNotNone(emails)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 1)
        self.assertIn("ventas@example.com", emails)


if __name__ == '__main__':
    unittest.main()
