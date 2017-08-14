#! /usr/bin/env python

import os

import config
import destalinator
import slackbot
import slacker

from utils.with_logger import WithLogger, set_up_log_level


class Executor(WithLogger):

    def __init__(self, slackbot_injected=None, slacker_injected=None):
        set_up_log_level()
        self.config = config.Config()
        slackbot_token = os.getenv(self.config.slackbot_api_token_env_varname)
        api_token = os.getenv(self.config.api_token_env_varname)
        self.slackbot = slackbot_injected or slackbot.Slackbot(config.SLACK_NAME, token=slackbot_token)
        self.destalinator_activated = False
        if os.getenv(self.config.destalinator_activated_env_varname):
            self.destalinator_activated = True
        self.logger.debug("destalinator_activated is %s", self.destalinator_activated)
        self.slacker = slacker_injected or slacker.Slacker(config.SLACK_NAME, token=api_token)
        self.ds = destalinator.Destalinator(slacker=self.slacker,
                                            slackbot=self.slackbot,
                                            activated=self.destalinator_activated)
