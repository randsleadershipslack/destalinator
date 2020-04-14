import argparse
import time

import executor

from utils.util import ignore_channel

class Stats(executor.Executor):
    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        super(self.__class__, self).__init__(*args, **kwargs)
        self.now = int(time.time())

    def emit_stats(self):
        channel_message_counts, user_message_counts = self.get_stats()

        channel_keys = sorted(channel_message_counts, key=channel_message_counts.get, reverse=True)
        for ck in channel_keys[:10]:
            print("{} ==> {}".format(ck, channel_message_counts[ck]))

        user_keys = sorted(user_message_counts, key=user_message_counts.get, reverse=True)
        for uk in user_keys[:15]:
            print("{} ==> {}".format(uk, user_keys[uk]))

    def get_stats(self):
        dayago = self.now - 86400

        channel_message_counts = {}
        user_message_counts = {}
        for channel in self.slacker.channels_by_name:
            if ignore_channel(self.config, channel):
                self.logger.debug("Not checking stats for channel: #%s because it's in ignore_channels", channel)
                continue

            cid = self.slacker.get_channelid(channel)
            cur_messages = self.slacker.get_messages_in_time_range(dayago, cid, self.now)

            channel_message_counts[channel] = len(cur_messages)

            for message in cur_messages:
                if message.get('user'):
                    user_name = self.slacker.users_by_id[message['user']]
                    if user_message_counts.get(user_name):
                        user_message_counts[user_name] = user_message_counts[user_name] + 1
                    else:
                        user_message_counts[user_name] = 1

        return channel_message_counts, user_message_counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Flag interesting Slack messages.')
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()

    Stats(debug=args.debug).emit_stats()