import os
import unittest

from config import get_config


class ConfigTest(unittest.TestCase):
    def setUp(self):
        os.environ['DESTALINATOR_STRING_VARIABLE'] = 'test'
        os.environ['DESTALINATOR_LIST_VARIABLE'] = 'test,'

    def test_environment_variable_configs(self):
        self.assertEqual(get_config().string_variable, 'test')
        self.assertListEqual(get_config().list_variable, ['test'])
