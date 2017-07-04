#! /usr/bin/env python

import os

import config
import destalinator
import slackbot
import slacker
import utils

from utils.with_logger import WithLogger


class Executor(WithLogger):

    def __init__(self, debug=False, verbose=False, slackbot_injected=None, slacker_injected=None):
        self.debug = debug
        self.verbose = verbose
        self.config = config.Config()
        slackbot_token = os.getenv(self.config.slackbot_api_token_env_varname)
        api_token = os.getenv(self.config.api_token_env_varname)

        self.slackbot = slackbot_injected or slackbot.Slackbot(config.SLACK_NAME, token=slackbot_token)

        utils.set_up_logger(self.logger,
                            slackbot=self.slackbot)

        self.destalinator_activated = False
        if os.getenv(self.config.destalinator_activated_env_varname):
            self.destalinator_activated = True
        self.logger.debug("destalinator_activated is %s", self.destalinator_activated)

        self.slacker = slacker_injected or slacker.Slacker(config.SLACK_NAME, token=api_token)

        self.ds = destalinator.Destalinator(slacker=self.slacker,
                                            slackbot=self.slackbot,
                                            activated=self.destalinator_activated)
