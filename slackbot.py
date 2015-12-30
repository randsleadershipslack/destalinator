#! /usr/bin/env python2.7

import requests

import util


class Slackbot(object):

    def __init__(self, slack_name, sb_token=None, sb_token_file=None, sb_token_env_variable=None):
        self.slack_name = slack_name
        self.sb_token = util.get_token(sb_token, sb_token_file, sb_token_env_variable)
        self.url = self.sb_url()

    def sb_url(self):
        url = "https://{}.slack.com/".format(self.slack_name)
        url += "services/hooks/slackbot"
        return url

    def say(self, channel, statement):
        """
        channel should not be preceded with '#'
        """
        assert channel  # not blank
        if channel[0] == '#':
            channel = channel[1:]
        nurl = self.url + "?token={}&channel=%23{}".format(self.sb_token, channel)
        p = requests.post(nurl, statement)
        return p.status_code
