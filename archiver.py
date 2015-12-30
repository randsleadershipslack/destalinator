#! /usr/bin/env python

import os

import slackbot
import destalinator


class Archiver(object):

    def __init__(self):
        self.sb = slackbot.Slackbot("rands-leadership",
                                    token=os.getenv("SB_TOKEN"))
        self.ds = destalinator.Destalinator("rands-leadership",
                                            slackbot=self.sb,
                                            token=os.getenv("API_TOKEN"))

    def archive(self):
        self.ds.safe_archive_all(60)

if __name__ == "__main__":
    archiver = Archiver()
    archiver.archive()
