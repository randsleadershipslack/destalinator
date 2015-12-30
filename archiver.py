#! /usr/bin/env python

import slackbot
import destalinator


class Archiver(object):

    def __init__(self):
        self.sb = slackbot.Slackbot("rands-leadership",
                                    sb_token_env_variable="SB_TOKEN")
        self.ds = destalinator.Destalinator("rands-leadership",
                                            slackbot=self.sb,
                                            api_token_env_variable="API_TOKEN")

    def archive(self):
        self.ds.safe_archive_all(60)

if __name__ == "__main__":
    archiver = Archiver()
    archiver.archive()
