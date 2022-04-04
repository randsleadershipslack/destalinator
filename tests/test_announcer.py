import os
import unittest
import mock

import announcer
import tests.fixtures as fixtures
import tests.mocks as mocks


class AnnouncerAnnounceTest(unittest.TestCase):
    def setUp(self):
        slacker_obj = mocks.mocked_slacker_object(channels_list=fixtures.channels)
        self.slackbot = mocks.mocked_slackbot_object()
        with mock.patch.dict(os.environ, {'DESTALINATOR_ACTIVATED': 'true'}):
            self.announcer = announcer.Announcer(slacker_injected=slacker_obj, slackbot_injected=self.slackbot)
