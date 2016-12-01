#! /usr/bin/env python

import copy
import argparse
import json
import operator
import re
import time
import traceback

# support Python 2 and 3's versions of this module
try:
    import html.parser as HTMLParser
except ImportError:
    import HTMLParser

import config as _config
import executor

config = _config.Config()


class Flagger(executor.Executor):

    operators = {'>': operator.gt, '<': operator.lt, '==': operator.eq,
                 '>=': operator.ge, '<=': operator.le}

    def __init__(self, *args, **kwargs):
        self.htmlparser = HTMLParser.HTMLParser()
        super(Flagger, self).__init__(*args, **kwargs)

    def dprint(self, message):
        """
        If we're in debug or verbose mode, print message
        """
        if self.debug or self.verbose:
            print(message)

    def extract_threshold(self, token):
        """
        accept tokens of the format:
        int
        >=int
        <=int
        ==int
        >int
        <int
        returns [comparator, int] or throws error if invalid
        """
        comparator = re.sub("\d+$", "", token)
        value = int(re.sub("\D*", "", token))
        if comparator == '':  # no comparator specified
            comparator = '>='

        comparator = self.htmlparser.unescape(comparator)
        self.dprint("token: {} comparator: {} value: {}".format(token, comparator, value))

        assert comparator in self.operators
        return (comparator, value)

    def initialize_control(self):
        """
        sets up known control configuration based on control channel messages
        """
        channel = config.control_channel
        if not self.slacker.channel_exists(channel):
            self.ds.warning("Flagger control channel does not exist, cannot run. Please create #{}.".format(channel))
            return False
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
                comparator, threshold = self.extract_threshold(tokens[4])
                emoji = tokens[5].replace(":", "")
                output_channel_id = re.sub("[<>]", "", tokens[6])
                if output_channel_id.find("|") != -1:
                    cid, cname = output_channel_id.split("|")
                    output_channel_id = cid
                output_channel_name = self.slacker.replace_id(output_channel_id)
                control[uuid] = {'threshold': threshold, "comparator": comparator,
                                 'emoji': emoji, 'output': output_channel_name}
            except Exception as e:
                tb = traceback.format_exc()
                m = "Couldn't create flagger rule with text {}: {} {}".format(text, Exception, e)
                self.dprint(m)
                self.dprint(tb)
                if not self.debug:
                    self.ds.warning(m)
        self.control = control
        self.dprint("control: {}".format(json.dumps(self.control, indent=4)))
        self.emoji = [x['emoji'] for x in self.control.values()]
        self.initialize_emoji_aliases()
        return True

    def initialize_emoji_aliases(self):
        """
        In some cases, emojiA might be an alias of emojiB
        The problem is that if we say that 2xemojiB should be
        enough to flag something, then we should accept
        2 x emojiB
        1 x emojiA, 1 x emojiB
        2 x emojiA
        This method grabs the emoji list from the Slack and creates the equivalence
        structure
        """
        self.dprint("Starting emoji alias list")
        emojis_response = self.slacker.get_emojis()
        self.dprint("emojis_response keys are {}".format(emojis_response.keys()))
        emojis = emojis_response['emoji']
        equivalents = {}
        for emoji in emojis:
            target = emojis[emoji]
            target_type, target_value = target.split(":", 1)
            if target_type != "alias":
                continue
            self.dprint("Found emoji alias: {} <-> {}".format(emoji, target_value))
            if emoji not in equivalents:
                equivalents[emoji] = []
            if target_value not in equivalents:
                equivalents[target_value] = []
            equivalents[emoji].append(target_value)
            equivalents[target_value].append(emoji)
        self.emoji_equivalents = equivalents
        self.dprint("equivalents: {}".format(json.dumps(self.emoji_equivalents, indent=4)))
        if "floppy_disk" in self.emoji_equivalents.keys():
            self.dprint("floppy_disk: {}".format(self.emoji_equivalents['floppy_disk']))

    def message_destination(self, message):
        """
        if interesting, returns channel name[s] in which to announce
        otherwise, returns []
        """
        channels = []
        if message.get("reactions") is None:
            return False
        reactions = message.get("reactions")
        emoji_set = set(self.emoji)
        current_reactions = {}
        t = message.get("text")
        if t.find("SVP") != -1:
            def d(p):
                pass  # print p
        else:
            def d(p):
                pass
        d("reactions: {}".format(reactions))
        d("emoji_equivalents:\n{}".format(json.dumps(self.emoji_equivalents, indent=4)))
        if "floppy_disk" in self.emoji_equivalents.keys():
            d("floppy_disk: {}".format(self.emoji_equivalents['floppy_disk']))
        for reaction in reactions:
            count = reaction['count']
            current_emoji = reaction['name']
            d("current_emoji: {}".format(current_emoji))
            equivalents = copy.copy(self.emoji_equivalents.get(current_emoji, []))
            d("equivalents = {}".format(equivalents))
            equivalents.append(current_emoji)
            d("equivalents = {}".format(equivalents))
            current_set = set(equivalents)
            i = current_set.intersection(emoji_set)
            if not i:
                continue
            for ce in equivalents:
                current_reactions[ce] = current_reactions.get(ce, 0) + count
            # if we're here, at least one emoji matches (but count may still not be right)
        d("Current reactions: {}".format(current_reactions))
        for uuid in self.control:
            rule = self.control[uuid]
            for ce in current_reactions:
                if ce == rule['emoji']:
                    count = current_reactions[ce]
                    threshold = rule['threshold']
                    comparator = rule['comparator']
                    op = self.operators[comparator]
                    if op(count, threshold):
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
                if self.slacker.channel_exists(output_channel):
                    md = "Saying {} to {}".format(m, output_channel)
                    self.dprint(md)
                    if not self.debug and self.destalinator_activated:
                        self.sb.say(output_channel, m)
                else:
                    self.ds.warning("Attempted to announce in {}, but channel does not exist.".format(output_channel))

    def flag(self):
        if self.initialize_control():
            self.announce_interesting_messages()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Flag interesting Slack messages.')
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()

    flagger = Flagger(debug=args.debug, verbose=args.verbose)
    flagger.flag()
