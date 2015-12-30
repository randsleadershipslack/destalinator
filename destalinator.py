#! /usr/bin/env python

import datetime
import sys
import time

import requests

import slackbot
import util


class Destalinator(object):

    closure_text_fname = "closure.txt"
    warning_text_fname = "warning.txt"
    earliest_archive_date = "2016-01-28"  # Do not archive channels prior to this date
    log_channel = "destalinator-log"

    ignore_users = ["USLACKBOT"]

    def __init__(self, slack_name, slackbot, api_token=None, api_token_file=None, api_token_env_variable=None):
        """
        slack name is the short name of the slack (preceding '.slack.com')
        slackbot should be an initialized slackbot.Slackbot() object
        api_token should be a Slack API Token.  However, it can also
        be None, and api_token_file be the file name containing a
        Slack API Token instead.  Lastly, if both are None you can specify
        api_token_env_variable as the environment variable to read for the value
        """
        self.slack_name = slack_name
        self.api_token = util.get_token(api_token, api_token_file, api_token_env_variable)
        self.url = self.api_url()
        self.channels = self.get_channels()
        self.closure_text = self.get_content(self.closure_text_fname)
        self.warning_text = self.get_content(self.warning_text_fname)
        self.slackbot = slackbot

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
        url = url_template.format(exclude_archived, self.api_token)
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
        if today > earliest:
            self.archive(channel_name)
        else:
            message = "Just FYI, I would have archived this channel but it's not yet "
            message += self.earliest_archive_date
            self.slackbot.say(channel_name, message)

    def archive(self, channel_name):
        """
        Archives the given channel name.  Returns the response content
        """
        url_template = self.url + "channels.archive?token={}&channel={}"
        cid = self.get_channelid(channel_name)
        url = url_template.format(self.api_token, cid)
        self.slackbot.say(channel_name, self.closure_text)
        request = requests.get(url)
        payload = request.json()
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
        url = url_template.format(ago, self.api_token, cid)
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
        url = url_template.format(self.api_token, cid)
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
            self.debug("Not checking if {} is stale -- it's too new".format(channel_name))
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
        self.debug("Warned {}".format(channel_name))

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S: ", time.localtime())
        message = timestamp + message
        self.slackbot.say(self.log_channel, message)

    def debug(self, message):
        message = "DEBUG: " + message
        self.log(message)

    def warning(self, message):
        message = "WARNING: " + message
        self.log(message)

    def safe_archive_all(self, days):
        """
        Safe-archives all channels stale longer than DAYS days
        """
        for channel in sorted(self.channels.keys()):
            if self.stale(channel, days):
                self.log("Attempting to safe-archive {}".format(channel))
                self.safe_archive(channel)

    def warn_all(self, days, force_warn=False):
        """
        warns all channels which are DAYS idle
        if force_warn, will warn even if we already have
        """
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
