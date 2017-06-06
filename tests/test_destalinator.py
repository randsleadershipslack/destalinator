import mock
import os
import unittest

import destalinator
import slacker
import slackbot


sample_slack_messages = [
    {
        "type": "message",
        "channel": "C2147483705",
        "user": "U2147483697",
        "text": "Human human human.",
        "ts": "1355517523.000005",
        "edited": {
            "user": "U2147483697",
            "ts": "1355517536.000001"
        }
    },
    {
        "type": "message",
        "subtype": "bot_message",
        "text": "Robot robot robot.",
        "ts": "1403051575.000407",
        "user": "U023BEAD1"
    },
    {
        "type": "message",
        "subtype": "channel_name",
        "text": "#stalin has been renamed <C2147483705|khrushchev>",
        "ts": "1403051575.000407",
        "user": "U023BECGF"
    },
    {
        "type": "message",
        "channel": "C2147483705",
        "user": "U2147483697",
        "text": "Contemplating existence.",
        "ts": "1355517523.000005"
    },
    {
        "type": "message",
        "subtype": "bot_message",
        "attachments": [
            {
                "fallback": "Required plain-text summary of the attachment.",
                "color": "#36a64f",
                "pretext": "Optional text that appears above the attachment block",
                "author_name": "Bobby Tables",
                "author_link": "http://flickr.com/bobby/",
                "author_icon": "http://flickr.com/icons/bobby.jpg",
                "title": "Slack API Documentation",
                "title_link": "https://api.slack.com/",
                "text": "Optional text that appears within the attachment",
                "fields": [
                    {
                        "title": "Priority",
                        "value": "High",
                        "short": False
                    }
                ],
                "image_url": "http://my-website.com/path/to/image.jpg",
                "thumb_url": "http://example.com/path/to/thumb.png",
                "footer": "Slack API",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": 123456789
            }
        ],
        "ts": "1403051575.000407",
        "user": "U023BEAD1"
    }
]


class MockValidator(object):

    def __init__(self, validator):
        # validator is a function that takes a single argument and returns a bool.
        self.validator = validator

    def __eq__(self, other):
        return bool(self.validator(other))


class SlackerMock(slacker.Slacker):
    def get_users(self):
        pass

    def get_channels(self):
        pass


class DestalinatorChannelMarkupTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_add_slack_channel_markup(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        input_text = "Please find my #general channel reference."
        mock_slacker.add_channel_markup.return_value = "<#ABC123|general>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#ABC123|general> channel reference."
        )

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_add_slack_channel_markup_multiple(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        input_text = "Please find my #general multiple #general channel #general references."
        mock_slacker.add_channel_markup.return_value = "<#ABC123|general>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#ABC123|general> multiple <#ABC123|general> channel <#ABC123|general> references."
        )

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_add_slack_channel_markup_hyphens(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        input_text = "Please find my #channel-with-hyphens references."
        mock_slacker.add_channel_markup.return_value = "<#EXA456|channel-with-hyphens>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#EXA456|channel-with-hyphens> references."
        )

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_add_slack_channel_markup_ignore_screaming(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        input_text = "Please find my #general channel reference and ignore my #HASHTAGSCREAMING thanks."
        mock_slacker.add_channel_markup.return_value = "<#ABC123|general>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#ABC123|general> channel reference and ignore my #HASHTAGSCREAMING thanks."
        )


class DestalinatorChannelMinimumAgeTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_channel_is_old(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 86400 *  60}
        self.assertTrue(self.destalinator.channel_minimum_age("testing", 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_channel_is_exactly_expected_age(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 86400 *  30}
        self.assertFalse(self.destalinator.channel_minimum_age("testing", 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_channel_is_young(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 86400 *  1}
        self.assertFalse(self.destalinator.channel_minimum_age("testing", 30))


class DestalinatorGetMessagesTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_default_included_subtypes(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channelid.return_value = "123456"
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEquals(len(self.destalinator.get_messages("general", 30)), 5)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_empty_included_subtypes(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.destalinator.config.included_subtypes = []
        mock_slacker.get_channelid.return_value = "123456"
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEquals(len(self.destalinator.get_messages("general", 30)), 2)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_limited_included_subtypes(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.destalinator.config.included_subtypes = ['bot_message']
        mock_slacker.get_channelid.return_value = "123456"
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEquals(len(self.destalinator.get_messages("general", 30)), 4)


class DestalinatorGetStaleChannelsTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_no_stale_channels_but_all_minimum_age_with_default_ignore_users(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': {'id': 'ABC4321'}, 'stalinists': {'id': 'ABC4321'}}
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertEqual(len(self.destalinator.get_stale_channels(30)), 0)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_no_stale_channels_but_all_minimum_age_with_specific_ignore_users(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_users = ['U023BEAD1', 'U023BECGF', 'U2147483697']
        mock_slacker.channels_by_name = {'leninists': {'id': 'ABC4321'}, 'stalinists': {'id': 'ABC4321'}}
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertEqual(len(self.destalinator.get_stale_channels(30)), 2)


class DestalinatorIgnoreChannelTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    def test_with_explicit_ignore_channel(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_channels = ['stalinists']
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    def test_with_matching_ignore_channel_pattern(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_channel_patterns = ['^stal']
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_non_mathing_ignore_channel_pattern(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_channel_patterns = ['^len']
        self.assertFalse(self.destalinator.ignore_channel('stalinists'))

    def test_with_many_matching_ignore_channel_patterns(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_channel_patterns = ['^len', 'lin', '^st']
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    def test_with_empty_ignore_channel_config(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_channels = []
        self.destalinator.config.ignore_channel_patterns = []
        self.assertFalse(self.destalinator.ignore_channel('stalinists'))


class DestalinatorStaleTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_all_sample_messages(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertFalse(self.destalinator.stale('stalinists', 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_all_users_ignored(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.destalinator.config.ignore_users = ['U023BEAD1', 'U023BECGF', 'U2147483697']
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertTrue(self.destalinator.stale('stalinists', 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_only_a_dolphin_message(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        messages = [
            {
                "type": "message",
                "channel": "C2147483705",
                "user": "U2147483697",
                "text": ":dolphin:",
                "ts": "1355517523.000005"
            }
        ]
        self.destalinator.get_messages = mock.MagicMock(return_value=messages)
        self.assertTrue(self.destalinator.stale('stalinists', 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_only_an_attachment_message(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=[m for m in sample_slack_messages if m.has_key('attachments')])
        self.assertFalse(self.destalinator.stale('stalinists', 30))


class DestalinatorArchiveTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_skips_ignored_channel(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.slackbot.say = mock.MagicMock(return_value=200)
        mock_slacker.archive.return_value = {'ok': True}
        self.destalinator.config.ignore_channels = ['stalinists']
        self.destalinator.archive("stalinists")
        self.assertFalse(self.slackbot.say.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_skips_when_destalinator_not_activated(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=False)
        self.slackbot.say = mock.MagicMock(return_value=200)
        self.destalinator.archive("stalinists")
        self.assertFalse(self.slackbot.say.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_announces_closure_with_closure_text(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.slackbot.say = mock.MagicMock(return_value=200)
        mock_slacker.archive.return_value = {'ok': True}
        self.destalinator.archive("stalinists")
        self.assertIn(mock.call('stalinists', self.destalinator.closure_text), self.slackbot.say.mock_calls)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_announces_members_at_channel_closing(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.slackbot.say = mock.MagicMock(return_value=200)
        mock_slacker.archive.return_value = {'ok': True}
        names = ['sridhar', 'jane']
        mock_slacker.get_channel_member_names.return_value = names
        self.destalinator.archive("stalinists")
        self.assertIn(
            mock.call('stalinists', MockValidator(lambda s: all(name in s for name in names))),
            self.slackbot.say.mock_calls
        )

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_calls_archive_method(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.slackbot.say = mock.MagicMock(return_value=200)
        mock_slacker.archive.return_value = {'ok': True}
        self.destalinator.archive("stalinists")
        mock_slacker.archive.assert_called_once_with('stalinists')


if __name__ == '__main__':
    unittest.main()
