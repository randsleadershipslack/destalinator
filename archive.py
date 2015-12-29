#! /usr/bin/env python

import slackbot
import destalinator

sb = slackbot.Slackbot("rands-leadership", slackbot_token_file="sb_token.txt")
ds = destalinator.Destalinator("rands-leadership", slackbot=sb, api_token_file="api_token.txt")
ds.warn_all(30)
ds.safe_archive_all(60)
