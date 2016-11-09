#! /usr/bin/env python

import os

import config
import destalinator
import slackbot
import slacker


class Executor(object):

    def __init__(self, debug=False, verbose=False):
        self.debug = debug
        self.verbose = verbose
        self.config = config.Config()
        slackbot_token = os.getenv(self.config.slackbot_api_token_env_varname)
        api_token = os.getenv(self.config.api_token_env_varname)

        self.destalinator_activated = False
        if os.getenv(self.config.destalinator_activated_env_varname):
            self.destalinator_activated = True
        print("destalinator_activated is {}".format(self.destalinator_activated))

        self.sb = slackbot.Slackbot(config.SLACK_NAME, token=slackbot_token)

        self.slacker = slacker.Slacker(config.SLACK_NAME, token=api_token)

        self.ds = destalinator.Destalinator(
                slacker=self.slacker,
                slackbot=self.sb,
                activated=self.destalinator_activated
                )
