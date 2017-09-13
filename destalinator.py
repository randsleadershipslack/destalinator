#! /usr/bin/env python

from datetime import datetime, date
import re
import time
import json

from config import WithConfig
import utils

from utils.with_logger import WithLogger

# An arbitrary past date, as a default value for the earliest archive date
PAST_DATE_STRING = '2000-01-01'


class Destalinator(WithLogger, WithConfig):

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

        self.config.activated = activated
        self.logger.debug("activated is %s", self.config.activated)

        self.earliest_archive_date = self.get_earliest_archive_date()

        self.cache = {}
        self.now = int(time.time())

    # utility & data fetch methods

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

    def flush_channel_cache(self, channel_name):
        """Flush all internal caches for this channel name."""
        cid = self.slacker.get_channelid(channel_name)
        if cid in self.cache:
            self.logger.debug("Purging cache for %s", channel_name)
            del self.cache[cid]

    def get_earliest_archive_date(self):
        """Return a datetime.date object representing the earliest archive date."""
        date_string = self.config.earliest_archive_date \
            or PAST_DATE_STRING
        return datetime.strptime(date_string, "%Y-%m-%d").date()

    def get_messages(self, channel_name, days):
        """Return `days` worth of messages for channel `channel_name`. Caches messages per channel & days."""
        oldest = self.now - days * 86400
        cid = self.slacker.get_channelid(channel_name)

        if oldest in self.cache.get(cid, {}):
            self.logger.debug("Returning %s cached messages for #%s over %s days", len(self.cache[cid][oldest]), channel_name, days)
            return self.cache[cid][oldest]

        messages = self.slacker.get_messages_in_time_range(oldest, cid)
        self.logger.debug("Fetched %s messages for #%s over %s days", len(messages), channel_name, days)

        messages = [x for x in messages if x.get("subtype") is None or x.get("subtype") in self.config.included_subtypes]
        self.logger.debug("Filtered down to %s messages based on included_subtypes: %s", len(messages), ", ".join(self.config.included_subtypes))

        if cid not in self.cache:
            self.cache[cid] = {}
        self.cache[cid][oldest] = messages

        return messages

    def ignore_channel(self, channel_name):
        """Return True if `channel_name` is a channel we should ignore based on config settings."""
        if channel_name in self.config.ignore_channels:
            return True
        for pat in self.config.ignore_channel_patterns:
            if re.match(pat, channel_name):
                return True
        return False

    def post_marked_up_message(self, channel_name, message, **kwargs):
        self.slacker.post_message(channel_name, self.add_slack_channel_markup(message), **kwargs)

    def stale(self, channel_name, days):
        """
        Return True if channel represented by `channel_name` is stale.
        Definition of stale is: no messages in the last `days` which are not from config.ignore_users.
        """
        if not self.channel_minimum_age(channel_name, days):
            return False

        if self.ignore_channel(channel_name):
            return False

        if self.slacker.channel_has_only_restricted_members(channel_name):
            return False

        messages = self.get_messages(channel_name, days)

        # return True (stale) if none of the messages match the criteria below
        return not any(
            # the message is not from an ignored user
            x.get("user") not in self.config.ignore_users \
            and x.get("username") not in self.config.ignore_users \
            and (
                # the message must have text that doesn't include ignored words
                (x.get("text") and b":dolphin:" not in x.get("text").encode('utf-8', 'ignore')) \
                or x.get("attachments")  # or the message must have attachments
            )
            for x in messages
        )

    # channel actions

    def archive(self, channel_name):
        """Archive the given channel name, returning the Slack API response as a JSON string."""
        # Might not need to do this since we now do this in `stale`
        if self.ignore_channel(channel_name):
            self.logger.debug("Not archiving #%s because it's in ignore_channels", channel_name)
            return

        if self.config.activated:
            self.logger.debug("Announcing channel closure in #%s", channel_name)
            self.post_marked_up_message(channel_name, self.closure_text, message_type='channel_archive')

            members = self.slacker.get_channel_member_names(channel_name)
            say = "Members at archiving are {}".format(", ".join(sorted(members)))
            self.logger.debug("Telling channel #%s: %s", channel_name, say)
            self.post_marked_up_message(channel_name, say, message_type='channel_archive_members')

            self.action("Archiving channel #{}".format(channel_name))
            payload = self.slacker.archive(channel_name)
            if payload['ok']:
                self.logger.debug("Slack API response to archive: %s", json.dumps(payload, indent=4))
                self.logger.info("Archived %s", channel_name)
            else:
                error = payload.get('error', '!! No error found in payload %s !!' % payload)
                self.logger.error("Failed to archive %s: %s. See https://api.slack.com/methods/channels.archive for more context.", channel_name, error)

            return payload

    def safe_archive(self, channel_name):
        """
        Archive channel if today's date is after `self.earliest_archive_date`
        and if channel does not only contain single-channel guests.
        """
        self.logger.debug("Evaluating #%s for archival", channel_name)

        # Might not need to do this since we now do this in `stale`
        if self.slacker.channel_has_only_restricted_members(channel_name):
            self.logger.debug("Would have archived #%s but it contains only restricted users", channel_name)
            return

        today = date.today()
        if today >= self.earliest_archive_date:
            self.archive(channel_name)
        else:
            self.logger.debug("Would have archived #%s but it's not yet %s", channel_name, self.earliest_archive_date)

    def safe_archive_all(self, days):  # TODO: No need to pass in days here
        """Safe archive all channels stale longer than `days`."""
        self.action("Safe-archiving all channels stale for more than {} days".format(days))
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.stale(channel, days):
                self.logger.debug("Attempting to safe-archive #%s", channel)
                self.safe_archive(channel)
            self.flush_channel_cache(channel)

    def warn(self, channel_name, days, force_warn=False):
        """
        Send warning text to channel_name, if it has not been sent already in the last `days`.
        Using `force_warn=True` will warn even if a previous warning exists.
        Return True if we actually warned, otherwise False.
        """
        # Might not need to do this since we now do this in `stale`
        if self.slacker.channel_has_only_restricted_members(channel_name):
            self.logger.debug("Would have warned #%s but it contains only restricted users", channel_name)
            return False

        # Might not need to do this since we now do this in `stale`
        if self.ignore_channel(channel_name):
            self.logger.debug("Not warning #%s because it's in ignore_channels", channel_name)
            return False

        messages = self.get_messages(channel_name, days)
        texts = [x.get("text").strip() for x in messages if x.get("text")]
        if (not force_warn and
                (self.add_slack_channel_markup(self.warning_text) in texts or
                 any(any(a.get('fallback') == 'channel_warning' for a in m.get('attachments', [])) for m in messages))):
            self.logger.debug("Not warning #%s because we found a prior warning", channel_name)
            return False

        if self.config.activated:
            self.post_marked_up_message(channel_name, self.warning_text, message_type='channel_warning')
            self.action("Warned #{}".format(channel_name))

        return True

    def warn_all(self, days, force_warn=False):
        """Warn all channels which are `days` idle; if `force_warn`, will warn even if we already have."""
        if not self.config.activated:
            self.logger.info("Note, destalinator is not activated and is in a dry-run mode. For help, see the "
                             "documentation on the DESTALINATOR_ACTIVATED environment variable.")
        self.action("Warning all channels stale for more than {} days".format(days))

        stale = []
        for channel in sorted(self.slacker.channels_by_name.keys()):
            if self.ignore_channel(channel):
                self.logger.debug("Not warning #%s because it's in ignore_channels", channel)
                continue
            if self.stale(channel, days):
                if self.warn(channel, days, force_warn):
                    stale.append(channel)
            self.flush_channel_cache(channel)

        if stale and self.config.general_message_channel:
            self.logger.debug("Notifying #%s of warned channels", self.config.general_message_channel)
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
        if self.config.activated:
            self.post_marked_up_message(self.config.general_message_channel, message, message_type='warn_in_general')
        self.logger.debug("Notified #%s with: %s", self.config.general_message_channel, message)
