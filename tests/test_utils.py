# encoding: utf-8

import mock
import unittest

import utils

class UtilsGetLocalFileContentTestCase(unittest.TestCase):
    def test_unicode_file_content(self):
        content = utils.get_local_file_content("tests/content_unicode.txt")
        self.assertIn(u'’', content)

    def test_ascii_file_content(self):
        content = utils.get_local_file_content("tests/content_ascii.txt")
        self.assertIn(u"'", content)
