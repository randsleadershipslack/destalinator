#! /usr/bin/env python

import os

import config
import destalinator
import slackbot
import slacker


class Executor(object):

    def __init__(self):
        self.config = config.Config()
        slackbot_token = os.getenv(self.config.slackbot_api_token_env_varname)
        api_token = os.getenv(self.config.api_token_env_varname)

        self.sb = slackbot.Slackbot(self.config.slack_name, token=slackbot_token)

        self.slacker = slacker.Slacker(self.config.slack_name, token=api_token)

        self.ds = destalinator.Destalinator(slacker=self.slacker, slackbot=self.sb)
