#! /usr/bin/env python

import slackbot
import destalinator

def archive():

    sb = slackbot.Slackbot("rands-leadership", slackbot_token_file="sb_token.txt")
    ds = destalinator.Destalinator("rands-leadership", slackbot=sb, api_token_file="api_token.txt")
    ds.safe_archive_all(60)

if __name__ == "__main__":
    archive()
