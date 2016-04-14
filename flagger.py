#! /usr/bin/env python

import argparse
import json
import re
import time

import config as _config
import executor

config = _config.Config()


class Flagger(executor.Executor):

    def dprint(self, message):
        """
        If we're in debug or verbose mode, print message
        """
        if self.debug or self.verbose:
            print message

    def initialize_control(self):
        """
        sets up known control configuration based on control channel messages
        """
        channel = config.control_channel
        cid = self.slacker.get_channelid(channel)
        messages = self.slacker.get_messages_in_time_range(0, cid, time.time())
        control = {}
        for message in messages:
            text = message['text']
            tokens = text.split()
            if tokens[0:3] != ['flag', 'content', 'rule']:
                continue
            if len(tokens) < 5:
                self.ds.warning("control message {} has too few tokens".format(text))
                continue
            if len(tokens) == 5 and tokens[4] == 'delete':
                uuid = tokens[3]
                if uuid in control:
                    del(control[uuid])
                    self.dprint("Message {} deletes UUID {}".format(text, uuid))
                    continue
            try:
                tokens = text.split()
                uuid = tokens[3]
                threshold = int(tokens[4])
                emoji = tokens[5].replace(":", "")
                output_channel_id = re.sub("[<>]", "", tokens[6])
                if output_channel_id.find("|") != -1:
                    cid, cname = output_channel_id.split("|")
                    output_channel_id = cid
                output_channel_name = self.slacker.replace_id(output_channel_id)
                control[uuid] = {'threshold': threshold, 'emoji': emoji, 'output': output_channel_name}
            except Exception, e:
                m = "Couldn't create flagger rule with text {}: {} {}".format(text, Exception, e)
                self.dprint(m)
                if not self.debug:
                    self.ds.warning(m)
        self.control = control
        self.dprint("control: {}".format(json.dumps(self.control, indent=4)))
        self.emoji = [x['emoji'] for x in self.control.values()]

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
                if reaction['name'] == rule['emoji'] and reaction['count'] >= rule['threshold']:
                    channels.append(rule['output'])
        return channels

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
        slack_name = _config.SLACK_NAME
        for message, channels in messages:
            ts = message['ts'].replace(".", "")
            channel = message['channel']
            author = message['user']
            author_name = self.slacker.users_by_id[author]
            text = self.slacker.asciify(message['text'])
            text = self.slacker.detokenize(text)
            url = "http://{}.slack.com/archives/{}/p{}".format(slack_name, channel, ts)
            m = "*@{}* said in *#{}* _'{}'_ ({})".format(author_name, channel, text, url)
            for output_channel in channels:
                md = "Saying {} to {}".format(m, output_channel)
                self.dprint(md)
                if not self.debug:
                    self.sb.say(output_channel, m)

    def flag(self):
        self.initialize_control()
        self.announce_interesting_messages()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Flag interesting Slack messages.')
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()

    flagger = Flagger(debug=args.debug, verbose=args.verbose)
    flagger.flag()
