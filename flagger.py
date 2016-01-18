#! /usr/bin/env python

import json
import os
import sys
import time

import config
import executor

config = config.Config()


class Flagger(executor.Executor):

        def is_interesting(self, message):
            """
            True/False whether message is interesting
            """
            if message.get("reactions") is None:
                return False
            reactions = message.get("reactions")
            for reaction in reactions:
                if reaction['name'] != config.interesting_emoji:
                    continue
                if reaction['count'] >= config.interesting_threshold:
                    return True
            return False

        def asciify(self, text):
            return ''.join([x for x in list(text) if ord(x) in range(128)])

        def get_interesting_messages(self):
            """
            returns list of interesting messages
            """
            now = time.time()
            dayago = now - 86400

            messages = []
            for channel in self.slacker.channels_by_name:
                cid = self.slacker.get_channelid(channel)
                cur_messages = self.slacker.get_messages_in_time_range(dayago, cid, now)
                for message in cur_messages:
                    if self.is_interesting(message):
                        messages.append(message)
            return messages

        def announce_interesting_messages(self):
            messages = self.get_interesting_messages()
            slack_name = config.slack_name
            for message in messages:
                ts = message['ts'].replace(".", "")
                channel = message['channel']
                author = message['user']
                author_name = self.slacker.users_by_id[author]
                text = self.asciify(message['text'])
                text = self.slacker.detokenize(text)
                url = "http://{}.slack.com/archives/{}/p{}".format(slack_name, channel, ts)
                m = "*@{}* said in *#{}* _'{}'_ ({})".format(author_name, channel, text, url)
                # print m
                self.sb.say(config.interesting_channel, m)

        def flag(self):
            self.announce_interesting_messages()

if __name__ == "__main__":
    flagger = Flagger()
    flagger.flag()
