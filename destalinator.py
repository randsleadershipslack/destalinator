#! /usr/bin/env python

import datetime
import os
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

    def get_content(self, fname):
        """
        read fname into text blob, return text blob
        """
        f = open(fname)
        ret = f.read().strip()
        f.close()
        return ret

    def api_url(self):
        return "https://{}.slack.com/api/".format(self.slack_name)

    def get_channels(self, exclude_archived=True):
        """
        return a {channel_name: channel_id} dictionary
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
        channels = {x['name']: x['id'] for x in payload['channels']}
        return channels

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
        self.action("{} safe-archiving all appropriate channels stale for more than {} days".format(self.user, days))
        for channel in sorted(self.channels.keys()):
            if self.stale(channel, days):
                # self.debug("Attempting to safe-archive {}".format(channel))
                self.safe_archive(channel)

    def warn_all(self, days, force_warn=False):
        """
        warns all channels which are DAYS idle
        if force_warn, will warn even if we already have
        """
        self.action("{} warning all appropriate channels stale for more than {} days".format(self.user, days))
        for channel in sorted(self.channels.keys()):
            if self.stale(channel, days):
                self.warn(channel, days, force_warn)

    def get_stale_channels(self, days):
        ret = []
        for channel in sorted(self.channels.keys()):
            if self.stale(channel, days):
                ret.append(channel)
        self.debug("{} channels quiet for {} days: {}".format(len(ret), days, ret))
        return ret
