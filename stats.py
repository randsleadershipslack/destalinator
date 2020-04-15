import argparse
import time

import executor

from utils.util import ignore_channel

# Add the following configuration.yaml items, for example:

# stats_channel: "zmeta-statistics"
# stats_ignore_users:
# - spinnaker
# stats_enabled: true
# stats_channel_top_n: 20
# stats_user_top_n: 5
class Stats(executor.Executor):

    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        super(self.__class__, self).__init__(*args, **kwargs)
        self.now = int(time.time())

    def stats(self):
        if not self.config.get("stats_enabled", True):
            self.logger.info("Not Collecting Stats: Stats disabled")
            return

        self.logger.info("Collecting Stats")

        channel_message_counts, user_message_counts = self.get_stats()

        channel_keys = sorted(channel_message_counts, key=channel_message_counts.get, reverse=True)
        channel_message_format = "*{}* was a top channel in the last 24 hours with {} messages\n"
        channel_top = self.config.get("stats_channel_top_n", 10)
        channel_stats_message = "*==========TOP {} CHANNELS==========*\n".format(channel_top)
        for ck in channel_keys[:channel_top]:
            channel_stats_message += channel_message_format.format(ck, channel_message_counts[ck])

        user_keys = sorted(user_message_counts, key=user_message_counts.get, reverse=True)
        user_message_format = "*{}* was a top user in the last 24 hours with {} messages\n"
        user_top = self.config.get("stats_user_top_n", 25)
        user_stats_message = "\n*==========TOP {} USERS==========*\n".format(user_top)
        for uk in user_keys[:user_top]:
            user_stats_message += user_message_format.format(uk, user_message_counts[uk])

        self.slackbot.say(self.config.get("stats_channel", "zmeta-statistics"), channel_stats_message + user_stats_message)

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
                    if not self.config.stats_ignore_users or not user_name in self.config.stats_ignore_users:
                        if user_message_counts.get(user_name):
                            user_message_counts[user_name] = user_message_counts[user_name] + 1
                        else:
                            user_message_counts[user_name] = 1

        return channel_message_counts, user_message_counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Flag interesting Slack messages.')
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()

    Stats(debug=args.debug).stats()