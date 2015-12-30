#! /usr/bin/env python

import sys

import slackbot
import destalinator


class Warner(object):

    def __init__(self):
        self.sb = slackbot.Slackbot("rands-leadership", sb_token_env_variable="SB_TOKEN")
        self.ds = destalinator.Destalinator("rands-leadership",
                                            slackbot=self.sb,
                                            api_token_env_variable="API_TOKEN")

    def warn(self, force_warn=False):
        self.ds.warn_all(30, force_warn)

if __name__ == "__main__":
    warner = Warner()
    force_warn = False
    if len(sys.argv) == 2 and sys.argv[1] == "force":
        force_warn = True
    warner.warn(force_warn=force_warn)
