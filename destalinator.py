#! /usr/bin/env python

import datetime
import os
import re
import time
import json
import requests

import config
import slackbot


class Destalinator(object):

    closure_text_fname = "closure.txt"
    warning_text_fname = "warning.txt"

    def __init__(self, slacker, slackbot, activated):
        """
        slacker is a Slacker() object
        slackbot should be an initialized slackbot.Slackbot() object
        """
        self.closure_text = self.get_content(self.closure_text_fname)
        self.warning_text = self.get_content(self.warning_text_fname)
        self.slacker = slacker
        self.slackbot = slackbot
        self.user = os.getenv("USER")
        self.config = config.Config()
        self.output_debug_to_slack_flag = False
        if os.getenv(self.config.output_debug_env_varname):
            self.output_debug_to_slack_flag = True
        print("output_debug_to_slack_flag is {}".format(self.output_debug_to_slack_flag))
        self.destalinator_activated = activated
        print("destalinator_activated is {}".format(self.destalinator_activated))
        self.earliest_archive_date = self.config.earliest_archive_date
        self.cache = {}
        self.now = time.time()

    def get_content(self, fname):
        """
        read fname into text blob, return text blob
        """
        f = open(fname)
        ret = f.read().strip()
        f.close()
        return ret

    def safe_archive(self, channel_name):
        """
        Arhives channel if today's date is after self.earliest_archive_date
        and if channel does not only contain SCGs (Single-Channel Guests)
        """

        if self.slacker.channel_has_only_restricted_members(channel_name):
            message = "Would have archived {} but it contains restricted users"
            self.debug(message)
            return

        today = datetime.date.today()
        year, month, day = [int(x) for x in self.earliest_archive_date.split("-")]
        earliest = datetime.date(year, month, day)
        if today >= earliest:
            self.action("Archiving channel {}".format(channel_name))
            self.archive(channel_name)
        else:
            message = "Would have archived {} but it's not yet {}"
            message = message.format(channel_name, self.earliest_archive_date)
            self.debug(message)

    def archive(self, channel_name):
        """
        Archives the given channel name.  Returns the response content
        """
        if self.ignore_channel(channel_name):
            self.debug("Not warning {} because it's in ignore_channels".format(channel_name))
            return
        
        if self.destalinator_activated:
            self.slackbot.say(channel_name, self.closure_text)
            self.debug("Telling channel {}: {}".format(channel_name, self.closure_text))
            members = self.slacker.get_channel_member_names(channel_name)
            say = "Members at archiving are {}".format(", ".join(members))
            self.slackbot.say(channel_name, say)
            self.debug("Telling channel {}: {}".format(channel_name, say))
            payload = self.slacker.archive(channel_name)

            if payload['ok']:
                self.debug("Payload: {}".format(json.dumps(payload, indent=4)))
                self.debug("Archived {}".format(channel_name))
            else:
                error = payload.get('error', '!! No error found in payload %s !!' % payload)
                self.debug("Failed to archive {channel_name}: {error}. See https://api.slack.com/methods/channels.archive for more context.".format(channel_name=channel_name, error=error))

            return payload

    def channel_minimum_age(self, channel_name, days):
        """
        returns True/False depending on whether channel_name is at least DAYS old
        """
        info = self.slacker.get_channel_info(channel_name)
        age = info['age']
        age = age / 86400
        return age > days

    def stale(self, channel_name, days):
        """
        returns True/False whether the channel is stale.  Definition of stale is
        no messages in the last DAYS days which are not from config.ignore_users
        """
        minimum_age = self.channel_minimum_age(channel_name, days)
        if not minimum_age:
            # self.debug("Not checking if {} is stale -- it's too new".format(channel_name))
            return False
        messages = self.get_messages(channel_name, days)
        messages = [
            x
            for x
            in messages
            if x.get("user") not in self.config.ignore_users
            and x.get("text")
            and ":dolphin:" not in x.get("text").encode('utf-8', 'ignore')
        ]
        if messages:
            return False
        else:
            return True

    def get_messages(self, cname, days):
        """
        returns messages for channel cname, in the last days days
        """
        oldest = self.now - days * 86400
        cid = self.slacker.get_channelid(cname)
        if oldest in self.cache.get(cid, {}):
            return self.cache[cid][oldest]
        messages = self.slacker.get_messages_in_time_range(oldest, cid)
        # print "now is {}, oldest is {}, diff is {}".format(now, oldest, now - oldest)
        # print "messages for {} are {}".format(cid, messages)
        messages = [x for x in messages if (x.get("subtype") is None or x.get("subtype") in self.config.included_subtypes)]
        if cid not in self.cache:
            self.cache[cid] = {}
        self.cache[cid][oldest] = messages
        # kprint "After filtering, messages are {}".format(messages)
        return messages

    def warn(self, channel_name, days, force_warn=False):
        """
        send warning text to channel_name, if it has not been sent already
        in the last DAYS days
        if force_warn, will warn even if we have before
        returns True/False whether or not we actually warned
        """
        if self.ignore_channel(channel_name):
            self.debug("Not warning {} because it's in ignore_channels".format(channel_name))
            return False
        messages = self.get_messages(channel_name, days)
        # print "messages for {}: {}".format(channel_name, messages)
        texts = [x.get("text").strip() for x in messages if x.get("text")]
        if self.warning_text in texts and not force_warn:
            # nothing to do
            self.debug("Not warning {} because we found a prior warning".format(channel_name))
            return False
        if self.destalinator_activated:
            self.slackbot.say(channel_name, self.warning_text)
        self.action("Warned {}".format(channel_name))
        # print "warned {}".format(channel_name)
        return True

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S: ", time.localtime())
        message = timestamp + " ({}) ".format(self.user) + message
        self.slackbot.say(self.config.log_channel, message)

    def action(self, message):
        message = "*ACTION: " + message + "*"
        self.log(message)

    def debug(self, message):
        message = "DEBUG: " + message
        if self.output_debug_to_slack_flag:
            self.log(message)
        else:
            print(message)

    def warning(self, message):
        message = "WARNING: " + message
        self.log(message)

    def safe_archive_all(self, days):
        """
        Safe-archives all channels stale longer than DAYS days
        """
        self.action("Safe-archiving all channels stale for more than {} days".format(days))
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.ignore_channel(channel):
                self.debug("Not archiving {} because it's in ignore_channels".format(channel))
                continue
            if self.stale(channel, days):
                # self.debug("Attempting to safe-archive {}".format(channel))
                self.safe_archive(channel)

    def ignore_channel(self, channel_name):
        if channel_name in self.config.ignore_channels:
            return True
        for pat in self.config.ignore_channel_patterns:
            if re.match(pat, channel_name):
                return True
        return False

    def warn_all(self, days, force_warn=False):
        """
        warns all channels which are DAYS idle
        if force_warn, will warn even if we already have
        """
        if not self.destalinator_activated:
            m  = "Note, destalinator is not activated and is in a dry-run"
            m += "mode. For help, see the documentation on the "
            m += "DESTALINATOR_ACTIVATED environment variable."
            self.log(m)
        self.action("Warning all channels stale for more than {} days".format(days))
        # for channel in ["austin"]:
        stale = []
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.ignore_channel(channel):
                self.debug("Not warning {} because it's in ignore_channels".format(channel))
                continue
            if self.stale(channel, days):
                if self.warn(channel, days, force_warn):
                    stale.append(channel)
        if stale:
            self.debug("Notifying #general of warned channels")
            self.warn_in_general(stale)

    def warn_in_general(self, stale_channels):
        if not stale_channels:
            return
        if len(stale_channels) > 1:
            channel = "channels"
            being = "are"
            there = "them"
        else:
            channel = "channel"
            being = "is"
            there = "it"
        message = "Hey, heads up -- the following {} {} stale and will be "
        message += "archived if no one participates in {} over the next 30 days: "
        message += ", ".join(["#" + x for x in stale_channels])
        message = message.format(channel, being, there)
        if self.destalinator_activated:
            self.slackbot.say("general", message)
        self.debug("Notified #general with: {}".format(message))


    def get_stale_channels(self, days):
        ret = []
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.stale(channel, days):
                ret.append(channel)
        self.debug("{} channels quiet for {} days: {}".format(len(ret), days, ret))
        return ret
