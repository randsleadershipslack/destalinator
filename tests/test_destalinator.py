# pylint: disable=W0201
from datetime import date, datetime, timedelta
import mock
import os
import unittest

from config import get_config
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

# sample_warning_messages = [
#     {
#         "user": "U023BCDA1",
#         "text": "This is a channel warning! Put on your helmets!",
#         "username": "bot",
#         "bot_id": "B0T8EDVLY",
#         "attachments": [{"fallback": "channel_warning", "id": 1}],
#         "type": "message",
#         "subtype": "bot_message",
#         "ts": "1496855882.185855"
#     }
# ]


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
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
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
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_channel_is_old(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 86400 * 60}
        self.assertTrue(self.destalinator.channel_minimum_age("testing", 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_channel_is_exactly_expected_age(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 86400 * 30}
        self.assertFalse(self.destalinator.channel_minimum_age("testing", 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_channel_is_young(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 86400 * 1}
        self.assertFalse(self.destalinator.channel_minimum_age("testing", 30))


target_archive_date = date.today() + timedelta(days=10)
target_archive_date_string = target_archive_date.isoformat()


class DestalinatorGetEarliestArchiveDateTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    # TODO: This test (and others) would be redundant with solid testing around config directly.
    @mock.patch.dict(os.environ, {'DESTALINATOR_EARLIEST_ARCHIVE_DATE': target_archive_date_string})
    def test_env_var_name_set_in_config(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertEqual(self.destalinator.get_earliest_archive_date(), target_archive_date)

    @mock.patch.object(get_config(), 'earliest_archive_date', target_archive_date_string)
    def test_archive_date_set_in_config(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertEqual(self.destalinator.get_earliest_archive_date(), target_archive_date)

    @mock.patch.object(get_config(), 'earliest_archive_date_env_varname', None)
    @mock.patch.object(get_config(), 'earliest_archive_date', None)
    def test_falls_back_to_past_date(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertEqual(
            self.destalinator.get_earliest_archive_date(),
            datetime.strptime(destalinator.PAST_DATE_STRING, "%Y-%m-%d").date()
        )


class DestalinatorGetMessagesTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_default_included_subtypes(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channelid.return_value = "123456"
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEqual(len(self.destalinator.get_messages("general", 30)), len(sample_slack_messages))

    @mock.patch.object(get_config(), 'included_subtypes', [])
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_empty_included_subtypes(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channelid.return_value = "123456"
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEqual(
            len(self.destalinator.get_messages("general", 30)),
            sum('subtype' not in m for m in sample_slack_messages)
        )

    @mock.patch.object(get_config(), 'included_subtypes', ['bot_message'])
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_limited_included_subtypes(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channelid.return_value = "123456"
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEqual(
            len(self.destalinator.get_messages("general", 30)),
            sum(m.get('subtype', None) in (None, 'bot_message') for m in sample_slack_messages)
        )


class DestalinatorIgnoreChannelTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch.object(get_config(), 'ignore_channels', ['stalinists'])
    def test_with_explicit_ignore_channel(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['^stal'])
    def test_with_ignore_channel_pattern_matching_beginning_of_channel_name(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['linists$'])
    def test_with_ignore_channel_pattern_matching_end_of_channel_name(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['lini'])
    def test_with_ignore_channel_pattern_matching_middle_of_channel_name(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['^len'])
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_non_matching_ignore_channel_pattern(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        self.assertFalse(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['^len', 'lin', 'ists$'])
    def test_with_many_matching_ignore_channel_patterns(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channels', [])
    @mock.patch.object(get_config(), 'ignore_channel_patterns', [])
    def test_with_empty_ignore_channel_config(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.assertFalse(self.destalinator.ignore_channel('stalinists'))


class DestalinatorPostMarkedUpMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    def test_with_a_string_having_a_channel(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.post_marked_up_message('stalinists', "Really great message about #leninists.")
        self.slacker.post_message.assert_called_once_with('stalinists',
                                                          "Really great message about <#C012839|leninists>.")

    def test_with_a_string_having_many_channels(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.post_marked_up_message('stalinists', "Really great message about #leninists and #stalinists.")
        self.slacker.post_message.assert_called_once_with(
            'stalinists',
            "Really great message about <#C012839|leninists> and <#C102843|stalinists>."
        )

    def test_with_a_string_having_no_channels(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.post_marked_up_message('stalinists', "Really great message.")
        self.slacker.post_message.assert_called_once_with('stalinists', "Really great message.")


class DestalinatorStaleTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_all_sample_messages(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertFalse(self.destalinator.stale('stalinists', 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_minimum_channel_age_not_met(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.channel_minimum_age = mock.MagicMock(return_value=False)
        self.assertFalse(self.destalinator.stale('stalinists', 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_channel_ignored(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.ignore_channel = mock.MagicMock(return_value=True)
        self.assertFalse(self.destalinator.stale('stalinists', 30))

    @mock.patch.object(get_config(), 'ignore_users', [m['user'] for m in sample_slack_messages if m.get('user')])
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_all_users_ignored(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        mock_slacker.channel_has_only_restricted_members.return_value = False
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
        mock_slacker.channel_has_only_restricted_members.return_value = False
        self.destalinator.get_messages = mock.MagicMock(return_value=messages)
        self.assertTrue(self.destalinator.stale('stalinists', 30))

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_with_only_an_attachment_message(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=[m for m in sample_slack_messages if 'attachments' in m])
        self.assertFalse(self.destalinator.stale('stalinists', 30))


class DestalinatorArchiveTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch.object(get_config(), 'ignore_channels', ['stalinists'])
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_skips_ignored_channel(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        mock_slacker.archive.return_value = {'ok': True}
        self.destalinator.archive("stalinists")
        self.assertFalse(mock_slacker.post_message.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_skips_when_destalinator_not_activated(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=False)
        mock_slacker.post_message.return_value = {}
        self.destalinator.archive("stalinists")
        self.assertFalse(mock_slacker.post_message.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_announces_closure_with_closure_text(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        mock_slacker.archive.return_value = {'ok': True}
        mock_slacker.get_channel_member_names.return_value = ['sridhar', 'jane']
        self.destalinator.archive("stalinists")
        self.assertIn(
            mock.call('stalinists', mock.ANY, message_type='channel_archive'),
            mock_slacker.post_message.mock_calls
        )

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_announces_members_at_channel_closing(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        mock_slacker.archive.return_value = {'ok': True}
        names = ['sridhar', 'jane']
        mock_slacker.get_channel_member_names.return_value = names
        self.destalinator.archive("stalinists")
        self.assertIn(
            mock.call('stalinists', MockValidator(lambda s: all(name in s for name in names)), message_type=mock.ANY),
            mock_slacker.post_message.mock_calls
        )

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_calls_archive_method(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        mock_slacker.archive.return_value = {'ok': True}
        self.destalinator.archive("stalinists")
        mock_slacker.archive.assert_called_once_with('stalinists')

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_handles_a_bad_archive_api_response(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        mock_slacker.archive.return_value = {'ok': False, 'error': 'yup'}
        self.destalinator.archive("stalinists")
        mock_slacker.archive.assert_called_once_with('stalinists')


class DestalinatorSafeArchiveTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_skips_channel_with_only_restricted_users(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        mock_slacker.archive.return_value = {'ok': True}
        mock_slacker.channel_has_only_restricted_members.return_value = True
        self.destalinator.safe_archive("stalinists")
        self.assertFalse(mock_slacker.archive.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_skips_archiving_if_before_earliest_archive_date(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        self.destalinator.archive = mock.MagicMock(return_value=True)
        mock_slacker.channel_has_only_restricted_members.return_value = False
        today = date.today()
        self.destalinator.earliest_archive_date = today + timedelta(days=1)
        self.destalinator.safe_archive("stalinists")
        self.assertFalse(self.destalinator.archive.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_calls_archive_method(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.post_message.return_value = {}
        self.destalinator.archive = mock.MagicMock(return_value=True)
        mock_slacker.channel_has_only_restricted_members.return_value = False
        self.destalinator.safe_archive("stalinists")
        self.destalinator.archive.assert_called_once_with('stalinists')


class DestalinatorSafeArchiveAllTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_calls_stale_once_for_each_channel_with_cache(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.get_channelid.return_value = 'C012839'
        days_ago = self.destalinator.now - (86400 * 30)
        self.destalinator.cache = {'C012839': {days_ago: sample_slack_messages}}
        self.destalinator.stale = mock.MagicMock(return_value=False)
        days = self.destalinator.config.archive_threshold
        self.destalinator.safe_archive_all(days)
        self.assertEqual(self.destalinator.stale.mock_calls, [mock.call('leninists', days), mock.call('stalinists', days)])

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_calls_stale_once_for_each_channel_without_cache(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.get_channelid.return_value = 'C012839'
        self.destalinator.stale = mock.MagicMock(return_value=False)
        days = self.destalinator.config.archive_threshold
        self.destalinator.safe_archive_all(days)
        self.assertEqual(self.destalinator.stale.mock_calls, [mock.call('leninists', days), mock.call('stalinists', days)])

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_only_archives_stale_channels(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        days = self.destalinator.config.archive_threshold
        self.destalinator.safe_archive = mock.MagicMock()
        self.destalinator.safe_archive_all(days)
        self.destalinator.safe_archive.assert_called_once_with('leninists')

    @mock.patch.object(get_config(), 'ignore_channels', ['leninists'])
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_does_not_archive_ignored_channels(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        mock_slacker.channel_has_only_restricted_members.return_value = False
        self.destalinator.earliest_archive_date = date.today()
        self.destalinator.safe_archive_all(self.destalinator.config.archive_threshold)
        self.assertFalse(mock_slacker.archive.called)


class DestalinatorWarnTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_warns_by_posting_message(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channel_has_only_restricted_members.return_value = False
        mock_slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.destalinator.warn("stalinists", 30)
        mock_slacker.post_message.assert_called_with("stalinists",
                                                     self.destalinator.warning_text,
                                                     message_type='channel_warning')

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_warns_with_cached_messages(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        days_ago = self.destalinator.now - (86400 * 30)
        self.destalinator.cache = {'C012839': {days_ago: sample_slack_messages}}
        mock_slacker.get_channelid.return_value = 'C012839'
        mock_slacker.channel_has_only_restricted_members.return_value = False
        self.destalinator.warn("stalinists", 30)
        mock_slacker.post_message.assert_called_with("stalinists",
                                                     self.destalinator.warning_text,
                                                     message_type='channel_warning')

    def test_warns_by_posting_message_with_channel_names(self):
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot, activated=True)
        warning_text = self.destalinator.warning_text + " #leninists"
        self.destalinator.warning_text = warning_text
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.channel_has_only_restricted_members = mock.MagicMock(return_value=False)
        self.slacker.get_messages_in_time_range = mock.MagicMock(return_value=sample_slack_messages)
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.warn("stalinists", 30)
        self.slacker.post_message.assert_called_with("stalinists",
                                                     self.destalinator.add_slack_channel_markup(warning_text),
                                                     message_type='channel_warning')

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_does_not_warn_when_previous_warning_found(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channel_has_only_restricted_members.return_value = False
        mock_slacker.get_messages_in_time_range.return_value = [
            {
                "text": self.destalinator.warning_text,
                "user": "ABC123",
                "attachments": [{"fallback": "channel_warning"}]
            }
        ]
        self.destalinator.warn("stalinists", 30)
        self.assertFalse(mock_slacker.post_message.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_does_not_warn_when_previous_warning_with_changed_text_found(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channel_has_only_restricted_members.return_value = False
        mock_slacker.get_messages_in_time_range.return_value = [
            {
                "text": self.destalinator.warning_text + "Some new stuff",
                "user": "ABC123",
                "attachments": [{"fallback": "channel_warning"}]
            }
        ]
        self.destalinator.warn("stalinists", 30)
        self.assertFalse(mock_slacker.post_message.called)


class DestalinatorWarnAllTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock("testing", "bot_token", "user_token")
        self.slackbot = slackbot.Slackbot("testing", "token")

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_posts_a_warning_for_a_stale_channel(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.channel_has_only_restricted_members.return_value = False

        def fake_add_channel_markup(channel: str):
            return "<#{}|C012839>".format(channel)

        mock_slacker.add_channel_markup = mock.MagicMock(side_effect=fake_add_channel_markup)

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.warn_all(self.destalinator.config.archive_threshold)
        self.assertTrue(mock_slacker.post_message.called)

    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_posts_no_warning_during_dry_run(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=False)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.channel_has_only_restricted_members.return_value = False

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.warn_all(self.destalinator.config.archive_threshold)
        self.assertFalse(mock_slacker.post_message.called)

    @mock.patch.object(get_config(), 'general_message_channel', False)
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_does_not_warn_without_general_channel_configured(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.channel_has_only_restricted_members.return_value = False

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.warn_in_general = mock.MagicMock()

        self.destalinator.warn_all(self.destalinator.config.archive_threshold)
        self.assertFalse(self.destalinator.warn_in_general.called)

    @mock.patch.object(get_config(), 'general_message_channel', 'stalinists')
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_does_not_warn_in_general_channel_with_no_stale_channels(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.channel_has_only_restricted_members.return_value = False

        def fake_stale(channel, days):
            return False

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.warn_in_general = mock.MagicMock(return_value=True)

        self.destalinator.warn_all(self.destalinator.config.archive_threshold)
        self.assertFalse(self.destalinator.warn_in_general.called)

    @mock.patch.object(get_config(), 'general_message_channel', 'stalinists')
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_warns_in_general_channel_with_one_stale_channel(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.channel_has_only_restricted_members.return_value = False

        def fake_add_channel_markup(channel: str):
            return "<#{}|C012839>".format(channel)

        mock_slacker.add_channel_markup = mock.MagicMock(side_effect=fake_add_channel_markup)

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.warn_all(self.destalinator.config.archive_threshold)
        self.assertTrue(mock_slacker.post_message.called)

    @mock.patch.object(get_config(), 'general_message_channel', 'stalinists')
    @mock.patch('tests.test_destalinator.SlackerMock')
    def test_warns_in_general_channel_with_two_stale_channels(self, mock_slacker):
        self.destalinator = destalinator.Destalinator(mock_slacker, self.slackbot, activated=True)
        mock_slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        mock_slacker.channel_has_only_restricted_members.return_value = False

        def fake_add_channel_markup(channel: str):
            return "<#{}|C012839>".format(channel)

        mock_slacker.add_channel_markup = mock.MagicMock(side_effect=fake_add_channel_markup)

        def fake_stale(channel, days):
            return True

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.warn_all(self.destalinator.config.archive_threshold)
        self.assertTrue(mock_slacker.post_message.called)
