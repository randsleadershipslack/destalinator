#! /usr/bin/env python

import datetime
import os
import re
import time
import logging
import json
import requests
import sys

import config
import slackbot
import utils


# An arbitrary past date, as a default value for the earliest archive date
PAST_DATE_STRING = '2000-01-01'


class Destalinator(object):

    closure_text_fname = "closure.txt"
    warning_text_fname = "warning.txt"

    def __init__(self, slacker, slackbot, activated):
        """
        slacker is a Slacker() object
        slackbot should be an initialized slackbot.Slackbot() object
        activated is a boolean indicating whether destalinator should do dry runs or real runs
        """
        self.closure_text = utils.get_local_file_content(self.closure_text_fname)
        self.warning_text = utils.get_local_file_content(self.warning_text_fname)
        self.slacker = slacker
        self.slackbot = slackbot
        self.user = os.getenv("USER")
        self.config = config.Config()
        self.output_debug_to_slack_flag = False
        if os.getenv(self.config.output_debug_env_varname):
            self.output_debug_to_slack_flag = True

        self.logger = logging.getLogger(__name__)
        self.set_up_logger(self.logger,
                           log_level_env_var='DESTALINATOR_LOG_LEVEL',
                           log_to_slack_env_var=self.config.output_debug_env_varname,
                           log_channel=self.config.log_channel)

        self.destalinator_activated = activated
        self.logger.debug("destalinator_activated is %s", self.destalinator_activated)

        archive_date_string = (os.getenv(self.config.earliest_archive_date_env_varname)
                               or PAST_DATE_STRING)
        year, month, day = [int(x) for x in archive_date_string.split("-")]
        self.earliest_archive_date = datetime.date(year, month, day)

        self.cache = {}
        self.now = int(time.time())

    ## utility & data fetch methods

    def action(self, message):
        message = "*ACTION: " + message + "*"
        self.logger.info(message)

    def add_slack_channel_markup_item(self, item):
        return self.slacker.add_channel_markup(item.group(1))

    def add_slack_channel_markup(self, text):
        marked_up = re.sub(r"\#([a-z0-9_-]+)", self.add_slack_channel_markup_item, text)
        return marked_up

    def channel_minimum_age(self, channel_name, days):
        """Return True if channel represented by `channel_name` is at least `days` old, otherwise False."""
        info = self.slacker.get_channel_info(channel_name)
        age = info['age']
        age = age / 86400
        return age > days

    def debug(self, message):
        self.logger.debug(message)
        message = "DEBUG: " + message
        if self.output_debug_to_slack_flag:
            self.log(message)

    def get_messages(self, channel_name, days):
        """Return `days` worth of messages for channel `channel_name`. Caches messages per channel & days."""
        oldest = self.now - days * 86400
        cid = self.slacker.get_channelid(channel_name)

        if oldest in self.cache.get(cid, {}):
            self.debug("Returning {} cached messages for #{} over {} days".format(len(self.cache[cid][oldest]), channel_name, days))
            return self.cache[cid][oldest]

        messages = self.slacker.get_messages_in_time_range(oldest, cid)
        self.debug("Fetched {} messages for #{} over {} days".format(len(messages), channel_name, days))

        messages = [x for x in messages if (x.get("subtype") is None or x.get("subtype") in self.config.included_subtypes)]
        self.debug("Filtered down to {} messages based on included_subtypes: {}".format(len(messages), ", ".join(self.config.included_subtypes)))

        if cid not in self.cache:
            self.cache[cid] = {}
        self.cache[cid][oldest] = messages

        return messages

    def get_stale_channels(self, days):
        """Return a list of channel names that have been stale for `days`."""
        ret = []
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.stale(channel, days):
                ret.append(channel)
        self.debug("{} channels quiet for {} days: {}".format(len(ret), days, ret))
        return ret

    def ignore_channel(self, channel_name):
        """Return True if `channel_name` is a channel we should ignore based on config settings."""
        if channel_name in self.config.ignore_channels:
            return True
        for pat in self.config.ignore_channel_patterns:
            if re.match(pat, channel_name):
                return True
        return False

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S: ", time.localtime())
        message = timestamp + " ({}) ".format(self.user) + message
        self.slacker.post_message(self.config.log_channel, message, message_type='log')

    def set_up_logger(self, logger, log_level_env_var=None, log_to_slack_env_var=None, log_channel=None, default_level='INFO'):
        logger.setLevel(getattr(logging, os.getenv(log_level_env_var, default_level).upper(), getattr(logging, default_level)))
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    def stale(self, channel_name, days):
        """
        Return True if channel represented by `channel_name` is stale.
        Definition of stale is: no messages in the last `days` which are not from config.ignore_users.
        """
        if not self.channel_minimum_age(channel_name, days):
            self.debug("Channel #{} is not yet of minimum_age; skipping stale messages check".format(channel_name))
            return False

        messages = self.get_messages(channel_name, days)

        # return True (stale) if none of the messages match the criteria below
        return not any(
            # the message is not from an ignored user
            x.get("user") not in self.config.ignore_users
            and (
                # the message must have text that doesn't include ignored words
                (x.get("text") and b":dolphin:" not in x.get("text").encode('utf-8', 'ignore'))
                # or the message must have attachments
                or x.get("attachments")
            )
            for x in messages
        )

    ## channel actions

    def archive(self, channel_name):
        """Archive the given channel name, returning the Slack API response as a JSON string."""
        if self.ignore_channel(channel_name):
            self.debug("Not archiving #{} because it's in ignore_channels".format(channel_name))
            return

        if self.destalinator_activated:
            self.debug("Announcing channel closure in #{}".format(channel_name))
            self.slacker.post_message(channel_name, self.closure_text, message_type='channel_archive')

            members = self.slacker.get_channel_member_names(channel_name)
            say = "Members at archiving are {}".format(", ".join(sorted(members)))
            self.debug("Telling channel #{}: {}".format(channel_name, say))
            self.slacker.post_message(channel_name, say, message_type='channel_archive_members')

            self.action("Archiving channel #{}".format(channel_name))
            payload = self.slacker.archive(channel_name)
            if payload['ok']:
                self.debug("Slack API response to archive: {}".format(json.dumps(payload, indent=4)))
                self.logger.info("Archived #{}".format(channel_name))
            else:
                error = payload.get('error', '!! No error found in payload %s !!' % payload)
                self.logger.error("Failed to archive {channel_name}: {error}. See https://api.slack.com/methods/channels.archive for more context.".format(channel_name=channel_name, error=error))

            return payload

    def safe_archive(self, channel_name):
        """
        Archive channel if today's date is after `self.earliest_archive_date`
        and if channel does not only contain single-channel guests.
        """

        if self.slacker.channel_has_only_restricted_members(channel_name):
            self.debug("Would have archived #{} but it contains only restricted users".format(channel_name))
            return

        today = datetime.date.today()
        if today >= self.earliest_archive_date:
            self.action("Archiving channel #{}".format(channel_name))
            self.archive(channel_name)
        else:
            self.debug("Would have archived #{} but it's not yet {}".format(channel_name, self.earliest_archive_date))

    def safe_archive_all(self, days):
        """Safe archive all channels stale longer than `days`."""
        self.action("Safe-archiving all channels stale for more than {} days".format(days))
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.stale(channel, days):
                self.debug("Attempting to safe-archive #{}".format(channel))
                self.safe_archive(channel)

    def warn(self, channel_name, days, force_warn=False):
        """
        Send warning text to channel_name, if it has not been sent already in the last `days`.
        Using `force_warn=True` will warn even if a previous warning exists.
        Return True if we actually warned, otherwise False.
        """
        if self.slacker.channel_has_only_restricted_members(channel_name):
            self.debug("Would have warned #{} but it contains only restricted users".format(channel_name))
            return False

        if self.ignore_channel(channel_name):
            self.debug("Not warning #{} because it's in ignore_channels".format(channel_name))
            return False

        messages = self.get_messages(channel_name, days)
        texts = [x.get("text").strip() for x in messages if x.get("text")]
        if (not force_warn and
            (self.add_slack_channel_markup(self.warning_text) in texts or
                any(any(a.get('fallback') == 'channel_warning' for a in m.get('attachments', [])) for m in messages))):
            self.debug("Not warning #{} because we found a prior warning".format(channel_name))
            return False

        if self.destalinator_activated:
            self.slacker.post_message(channel_name, self.warning_text, message_type='channel_warning')
            self.action("Warned #{}".format(channel_name))

        return True

    def warn_all(self, days, force_warn=False):
        """Warn all channels which are `days` idle; if `force_warn`, will warn even if we already have."""
        if not self.destalinator_activated:
            self.logger.info("Note, destalinator is not activated and is in a dry-run mode. For help, see the " \
                             "documentation on the DESTALINATOR_ACTIVATED environment variable.")
        self.action("Warning all channels stale for more than {} days".format(days))

        stale = []
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.ignore_channel(channel):
                self.debug("Not warning #{} because it's in ignore_channels".format(channel))
                continue
            if self.stale(channel, days):
                if self.warn(channel, days, force_warn):
                    stale.append(channel)
        if stale and self.config.general_message_channel:
            self.debug("Notifying #{} of warned channels".format(self.config.general_message_channel))
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
            self.slacker.post_message(self.config.general_message_channel, message, message_type='warn_in_general')
        self.debug("Notified #{} with: {}".format(self.config.general_message_channel, message))
