#! /usr/bin/env python

import os

import config
import destalinator
import slackbot


class Executor(object):

    def __init__(self):
        self.config = config.Config()
        self.sb = slackbot.Slackbot(self.config.slack_name,
                                    token=os.getenv(self.config.slackbot_api_token_env_varname))
        self.ds = destalinator.Destalinator(self.config.slack_name,
                                            slackbot=self.sb,
                                            token=os.getenv(self.config.api_token_env_varname))
