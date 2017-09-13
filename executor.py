#! /usr/bin/env python

from config import WithConfig
import destalinator
import slackbot
import slacker

from utils.slack_logging import set_up_slack_logger
from utils.with_logger import WithLogger


class Executor(WithLogger, WithConfig):

    def __init__(self, slackbot_injected=None, slacker_injected=None):
        self.slackbot = slackbot_injected or slackbot.Slackbot(self.config.slack_name, token=self.config.sb_token)
        set_up_slack_logger(self.slackbot)

        self.logger.debug("activated is %s", self.config.activated)

        self.slacker = slacker_injected or slacker.Slacker(self.config.slack_name, token=self.config.api_token)

        self.ds = destalinator.Destalinator(slacker=self.slacker,
                                            slackbot=self.slackbot,
                                            activated=self.config.activated)
