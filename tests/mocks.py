import mock

from config import get_config
import slackbot
import slacker


def mocked_slackbot_object():
    obj = mock.MagicMock(wraps=slackbot.Slackbot(get_config().slack_name, token='token'))
    obj.say = mock.MagicMock(return_value=True)
    return obj


def mocked_slacker_object(channels_list=None, users_list=None, messages_list=None, emoji_list=None):
    slacker_obj = slacker.Slacker(get_config().slack_name, token='token', init=False)

    slacker_obj.get_all_channel_objects = mock.MagicMock(return_value=channels_list or [])
    slacker_obj.get_channels()

    slacker_obj.get_all_user_objects = mock.MagicMock(return_value=users_list or [])
    slacker_obj.get_users()

    slacker_obj.get_messages_in_time_range = mock.MagicMock(return_value=messages_list or [])
    slacker_obj.get_emojis = mock.MagicMock(return_value=emoji_list or [])

    return slacker_obj
