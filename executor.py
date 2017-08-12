#! /usr/bin/env python

import os

import config
import destalinator
import slackbot
import slacker

from utils.slack_logging import set_up_slack_logger
from utils.with_logger import WithLogger


class Executor(WithLogger):

    def __init__(self, slackbot_injected=None, slacker_injected=None):
        self.config = config.Config()
        slackbot_token = self.config.sb_token
        api_token = self.config.api_token
        self.slackbot = slackbot_injected or slackbot.Slackbot(config.SLACK_NAME, token=slackbot_token)
        set_up_slack_logger(self.slackbot)

        self.destalinator_activated = self.config.destalinator_activated == 'true'
        self.logger.debug("destalinator_activated is %s", self.destalinator_activated)

        self.slacker = slacker_injected or slacker.Slacker(config.SLACK_NAME, token=api_token)

        self.ds = destalinator.Destalinator(slacker=self.slacker,
                                            slackbot=self.slackbot,
                                            activated=self.destalinator_activated)
