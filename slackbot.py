#! /usr/bin/env python2.7

import requests


class Slackbot(object):

    def __init__(self, slack_name, token):
        self.slack_name = slack_name
        self.token = token
        assert self.token, "Token should not be blank"
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
        nurl = self.url + "?token={}&channel=%23{}".format(self.token, channel)
        p = requests.post(nurl, statement)
        return p.status_code
