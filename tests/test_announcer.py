import os
import time
import unittest
import mock

import announcer
from tests.test_destalinator import MockValidator
import tests.fixtures as fixtures
import tests.mocks as mocks


class AnnouncerAnnounceTest(unittest.TestCase):
    def setUp(self):
        slacker_obj = mocks.mocked_slacker_object(channels_list=fixtures.channels, users_list=fixtures.users)
        self.slackbot = mocks.mocked_slackbot_object()
        with mock.patch.dict(os.environ, {'DESTALINATOR_ACTIVATED': 'true'}):
            self.announcer = announcer.Announcer(slacker_injected=slacker_obj, slackbot_injected=self.slackbot)

    def test_announce_posts_to_announce_channel(self):
        def channel_message_test(channel):
            """Ensure that an announce message contains the name of the channel being announced."""
            return lambda message: channel['name'] in message

        self.announcer.announce()

        for channel in fixtures.channels:
            if channel['created'] > int(time.time()) - 86400:
                self.assertIn(
                    mock.call(self.announcer.config.announce_channel, MockValidator(channel_message_test(channel))),
                    self.slackbot.say.mock_calls
                )
