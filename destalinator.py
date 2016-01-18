#! /usr/bin/env python

import datetime
import os
import re
import sys
import time

import requests

import config
import slackbot


class Destalinator(object):

    closure_text_fname = "closure.txt"
    warning_text_fname = "warning.txt"
    log_channel = "destalinator-log"
    output_debug_to_slack = "DESTALINATOR_SLACK_VERBOSE"
    ignore_users = ["USLACKBOT"]
    ignore_channels = ["destalinator-log"]
    announce_channel = "zmeta-new-channels"

    def __init__(self, slack_name, slackbot, token):
        """
        slack name is the short name of the slack (preceding '.slack.com')
        slackbot should be an initialized slackbot.Slackbot() object
        token should be a Slack API Token.
        """
        self.slack_name = slack_name
        self.token = token
        assert self.token, "Token should not be blank"
        self.url = self.api_url()
        self.channels = self.get_channels()
        self.closure_text = self.get_content(self.closure_text_fname)
        self.warning_text = self.get_content(self.warning_text_fname)
        self.slackbot = slackbot
        self.output_debug_to_slack_flag = False
        if os.getenv(self.output_debug_to_slack):
            self.output_debug_to_slack_flag = True
        print "output_debug_to_slack_flag is {}".format(self.output_debug_to_slack_flag)
        self.user = os.getenv("USER")
        self.config = config.Config()
        self.earliest_archive_date = self.config.earliest_archive_date
        self.get_users()

    def asciify(self, text):
        return ''.join([x for x in list(text) if ord(x) in range(128)])

    def get_users(self):
        url = self.url + "users.list?token=" + self.token
        payload = requests.get(url).json()['members']
        self.users = {x['id']: x['name'] for x in payload}

    def get_content(self, fname):
        """
        read fname into text blob, return text blob
        """
        f = open(fname)
        ret = f.read().strip()
        f.close()
        return ret

    def get_messages_in_time_range(self, oldest, cid, latest=None):
        messages = []
        done = False
        while not done:
            murl = self.url + "channels.history?oldest={}&token={}&channel={}".format(oldest, self.token, cid)
            if latest:
                murl += "&latest={}".format(latest)
            else:
                murl += "&latest={}".format(time.time())
            payload = requests.get(murl).json()
            messages += payload['messages']
            if payload['has_more'] == False:
                done = True
                continue
            ts = [float(x['ts']) for x in messages]
            earliest = min(ts)
            latest = earliest
        messages.sort(key=lambda x: float(x['ts']))
        return messages

    def get_interesting_messages(self):
        """
        returns list of interesting messages
        """
        now = time.time()
        dayago = now - 86400

        messages = []
        for channel in self.channels:
            cid = self.channels[channel]
            cur_messages = self.get_messages_in_time_range(dayago, cid, now)
            for message in cur_messages:
                if message.get("reactions") is None:
                    continue
                reactions = message.get("reactions")
                for reaction in reactions:
                    if reaction['name'] == self.config.interesting_emoji and reaction['count'] >= self.config.interesting_threshold:
                        messages.append(message)
                        message['channel'] = channel

        return messages

    def announce_interesting_messages(self):
        messages = self.get_interesting_messages()
        slack_name = self.config.slack_name
        for message in messages:
            ts = message['ts'].replace(".", "")
            channel = message['channel']
            author = message['user']
            author_name = self.users[author]
            text = self.asciify(message['text'])
            text = self.detokenize(text)
            url = "http://{}.slack.com/archives/{}/p{}".format(slack_name, channel, ts)
            m = "*{}* said in *{}* _'{}'_ ({})".format(author_name, channel, text, url)
            # print m
            self.slackbot.say(self.config.interesting_channel, m)

    def replace_id(self, cid):
        """
        Assuming either a #channelid or @personid, replace them with #channelname or @username
        """
        stripped = cid[1:]
        first = cid[0]
        if first == "#":
            m = [x for x in self.channels if self.channels[x] == stripped]
            if m:
                return "#" + m[0]
            else:
                return cid
        elif first == "@":
            uname = self.users.get(stripped)
            if uname:
                return "@" + uname
        return cid

    def detokenize(self, message):
        new = []
        tokens = re.split("(<.*?>)", message)
        for token in tokens:
            if len(token) > 3 and token[0] == "<" and token[-1] == ">":
                token = self.replace_id(token[1:-1])
            new.append(token)
        message = " ".join(new)
        return message

    def api_url(self):
        return "https://{}.slack.com/api/".format(self.slack_name)

    def get_channels(self, exclude_archived=True):
        """
        return a {channel_name: channel_id} dictionary
        if exclude_arhived (default: True), only shows non-archived channels
        """
        channels = self.get_all_channel_objects(exclude_archived=exclude_archived)
        return {x['name']: x['id'] for x in channels}

    def announce_new_channels(self):
        new = self.get_new_channels()
        for cname, creator, purpose in new:
            m = "Channel #{} was created by {} with purpose: {}".format(cname, creator, purpose)
            self.slackbot.say(self.announce_channel, m)

    def get_new_channels(self):
        """
        returns [(channel_name, creator, purpose)] created in the last 24 hours
        """

        now = time.time()
        dayago = now - 86400
        channels = self.get_all_channel_objects()
        new_channels = [channel for channel in channels if channel['created'] > dayago]
        new = []
        for new_channel in new_channels:
            purpose = self.asciify(new_channel['purpose']['value'])
            creator = new_channel['creator']
            friendly = self.asciify(self.users[creator])
            name = self.asciify(new_channel['name'])
            new.append((name, friendly, purpose))
        return new

    def get_all_channel_objects(self, exclude_archived=True):
        """
        return all channels
        if exclude_arhived (default: True), only shows non-archived channels
        """

        url_template = self.url + "channels.list?exclude_archived={}&token={}"
        if exclude_archived:
            exclude_archived = 1
        else:
            exclude_archived = 0
        url = url_template.format(exclude_archived, self.token)
        request = requests.get(url)
        payload = request.json()
        assert 'channels' in payload
        return payload['channels']

    def get_channelid(self, channel_name):
        """
        Given a channel name, returns the ID of the channel
        """
        return self.channels[channel_name]

    def safe_archive(self, channel_name):
        """
        Arhives channel if today's date is after self.earliest_archive_date
        """
        today = datetime.date.today()
        year, month, day = [int(x) for x in self.earliest_archive_date.split("-")]
        earliest = datetime.date(year, month, day)
        if today >= earliest:
            self.action("Archiving channel {}".format(channel_name))
            # self.archive(channel_name)
        else:
            message = "Would have archived {} but it's not yet {}"
            message = message.format(channel_name, self.earliest_archive_date)
            self.debug(message)

    def archive(self, channel_name):
        """
        Archives the given channel name.  Returns the response content
        """
        if channel_name in self.ignore_channels:
            self.debug("Not warning {} because it's in ignore_channels".format(channel_name))
        url_template = self.url + "channels.archive?token={}&channel={}"
        cid = self.get_channelid(channel_name)
        url = url_template.format(self.token, cid)
        self.slackbot.say(channel_name, self.closure_text)
        request = requests.get(url)
        payload = request.json()
        self.debug("Archived {}".format(channel_name))
        return payload

    def get_messages(self, channel_name, days):
        """
        get 'all' messages for the given channel name in the slack
        name from the last DAYS days
        By default, Slack only returns 100 messages, so if more than 100
        messages were sent, we'll only get a subset of messages.  Since
        this code is used for stale channel handling, that's considered
        acceptable.
        """

        url_template = self.url + "channels.history?oldest={}&token={}&channel={}"
        cid = self.get_channelid(channel_name)
        ago = time.time() - (days * 86400)
        url = url_template.format(ago, self.token, cid)
        payload = requests.get(url).json()
        assert 'messages' in payload
        # Why filter out subtype? Because Slack marks *everything* as
        # messages, even when it's automated 'X has joined the channel'
        # notifications (which really should be marked as events, not messages)
        # The way to know whether or not such message is an event is to see
        # if it has a subtype -- someone just talking has no subtype, but
        # 'X has joined the channel' have a subtype, so we'll filter that out.
        return [x for x in payload['messages'] if x.get("subtype") is None]

    def get_channel_info(self, channel_name):
        """
        returns JSON with channel information.  Adds 'age' in seconds to JSON
        """
        url_template = self.url + "channels.info?token={}&channel={}"
        cid = self.get_channelid(channel_name)
        now = time.time()
        url = url_template.format(self.token, cid)
        ret = requests.get(url).json()
        if ret['ok'] != True:
            m = "Attempted to get channel info for {}, but return was {}"
            m = m.format(channel_name, ret)
            self.warning(m)
            raise RuntimeError(m)
        created = ret['channel']['created']
        age = now - created
        ret['channel']['age'] = age
        return ret['channel']

    def channel_minimum_age(self, channel_name, days):
        """
        returns True/False depending on whether channel_name is at least DAYS old
        """
        info = self.get_channel_info(channel_name)
        age = info['age']
        age = age / 86400
        return age > days

    def stale(self, channel_name, days):
        """
        returns True/False whether the channel is stale.  Definition of stale is
        no messages in the last DAYS days which are not from self.ignore_users
        """
        minimum_age = self.channel_minimum_age(channel_name, days)
        if not minimum_age:
            # self.debug("Not checking if {} is stale -- it's too new".format(channel_name))
            return False
        messages = self.get_messages(channel_name, days)
        messages = [x for x in messages if x.get("user") not in self.ignore_users]
        if messages:
            return False
        else:
            return True

    def warn(self, channel_name, days, force_warn=False):
        """
        send warning text to channel_name, if it has not been sent already
        in the last DAYS days
        if force_warn, will warn even if we have before
        """
        if channel_name in self.ignore_channels:
            self.debug("Not warning {} because it's in ignore_channels".format(channel_name))
        messages = self.get_messages(channel_name, days)
        texts = [x['text'].strip() for x in messages]
        if self.warning_text in texts and not force_warn:
            # nothing to do
            self.debug("Not warning {} because we found a prior warning".format(channel_name))
            return
        self.slackbot.say(channel_name, self.warning_text)
        self.action("Warned {}".format(channel_name))

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S: ", time.localtime())
        message = timestamp + message
        self.slackbot.say(self.log_channel, message)

    def action(self, message):
        message = "*ACTION: " + message + "*"
        self.log(message)

    def debug(self, message):
        message = "DEBUG: " + message
        if self.output_debug_to_slack_flag:
            self.log(message)
        else:
            print message

    def warning(self, message):
        message = "WARNING: " + message
        self.log(message)

    def safe_archive_all(self, days):
        """
        Safe-archives all channels stale longer than DAYS days
        """
        self.action("({}) safe-archiving all appropriate channels stale for more than {} days".format(self.user, days))
        for channel in sorted(self.channels.keys()):
            if channel in self.ignore_channels:
                self.debug("Not archiving {} because it's in ignore_channels".format(channel))
                continue
            if self.stale(channel, days):
                # self.debug("Attempting to safe-archive {}".format(channel))
                self.safe_archive(channel)

    def warn_all(self, days, force_warn=False):
        """
        warns all channels which are DAYS idle
        if force_warn, will warn even if we already have
        """
        self.action("({}) warning all appropriate channels stale for more than {} days".format(self.user, days))
        for channel in sorted(self.channels.keys()):
            if channel in self.ignore_channels:
                self.debug("Not warning {} because it's in ignore_channels".format(channel))
                continue
            if self.stale(channel, days):
                self.warn(channel, days, force_warn)

    def get_stale_channels(self, days):
        ret = []
        for channel in sorted(self.channels.keys()):
            if self.stale(channel, days):
                ret.append(channel)
        self.debug("{} channels quiet for {} days: {}".format(len(ret), days, ret))
        return ret
