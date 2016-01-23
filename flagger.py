#! /usr/bin/env python

import json
import os
import re
import sys
import time

import config
import executor

config = config.Config()


class Flagger(executor.Executor):

        def initialize_control(self):
            """
            sets up known control configuration based on #zmeta-control messages
            """
            channel = config.control_channel
            cid = self.slacker.get_channelid(channel)
            messages = self.slacker.get_messages_in_time_range(0, cid, time.time())
            control = {}
            for message in messages:
                text = message['text']
                if text.find("flag content rule") != 0:
                    continue
                try:
                    tokens = text.split()
                    uuid = tokens[3]
                    threshold = int(tokens[4])
                    emoji = tokens[5].replace(":", "")
                    output_channel_id = re.sub("[<>]", "", tokens[6])
                    output_channel_name = self.slacker.replace_id(output_channel_id)
                    control[uuid] = {'threshold': threshold, 'emoji': emoji, 'output': output_channel_name}
                except Exception, e:
                    self.ds.warning("Couldn't create flagger rule with text {}: {} {}".format(text, Exception, e))
            self.control = control
            self.emoji = [x['emoji'] for x in self.control.values()]

        def announce_interesting_messages(self):
            messages = self.get_interesting_messages()


        def message_destination(self, message):
            """
            if interesting, returns channel name[s] in which to announce
            otherwise, returns []
            """
            channels = []
            if message.get("reactions") is None:
                return False
            reactions = message.get("reactions")
            for reaction in reactions:
                if reaction['name'] not in self.emoji:
                    continue
                # if we're here, at least one emoji matches (but count may still not be right)
                for uuid in self.control:
                    rule = self.control[uuid]
                    emoji = rule['emoji']
                    count = reaction['count']
                    if reaction['name'] == rule['emoji'] and reaction['count'] >= rule['threshold']:
                        channels.append(rule['output'])
            return channels

        def asciify(self, text):
            return ''.join([x for x in list(text) if ord(x) in range(128)])

        def get_interesting_messages(self):
            """
            returns [[message, [listofchannelstoannounce]]
            """
            now = time.time()
            dayago = now - 86400

            messages = []
            for channel in self.slacker.channels_by_name:
                cid = self.slacker.get_channelid(channel)
                cur_messages = self.slacker.get_messages_in_time_range(dayago, cid, now)
                for message in cur_messages:
                    announce = self.message_destination(message)
                    if announce:
                        messages.append([message, announce])
            return messages

        def announce_interesting_messages(self):
            messages = self.get_interesting_messages()
            slack_name = config.slack_name
            for message, channels in messages:
                ts = message['ts'].replace(".", "")
                channel = message['channel']
                author = message['user']
                author_name = self.slacker.users_by_id[author]
                text = self.asciify(message['text'])
                text = self.slacker.detokenize(text)
                url = "http://{}.slack.com/archives/{}/p{}".format(slack_name, channel, ts)
                m = "*@{}* said in *#{}* _'{}'_ ({})".format(author_name, channel, text, url)
                # print m
                for output_channel in channels:
                    self.sb.say(output_channel, m)

        def flag(self):
            self.initialize_control()
            self.announce_interesting_messages()

if __name__ == "__main__":
    flagger = Flagger()
    flagger.flag()
    # flagger.initialize_control()
